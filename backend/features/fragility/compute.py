from collections import defaultdict

import numpy as np
import pandas as pd

from .settings import get_settings


def _empty_result(summary_note: str):
    return {
        "summary": {
            "total_holdings": 0,
            "usable_holdings": 0,
            "portfolio_enb": 0.0,
            "cluster_count": 0,
            "largest_cluster_weight": 0.0,
            "avg_pairwise_corr": 0.0,
            "window_days": get_settings()["window_days"],
        },
        "warnings": [summary_note],
        "heatmap": {
            "symbols": [],
            "matrix": [],
            "cluster_breaks": [],
        },
        "clusters": [],
        "enb_list": [],
    }


def _find(parent, item):
    while parent[item] != item:
        parent[item] = parent[parent[item]]
        item = parent[item]
    return item


def _union(parent, a, b):
    ra = _find(parent, a)
    rb = _find(parent, b)
    if ra != rb:
        parent[rb] = ra


def _pairwise_mean(matrix: pd.DataFrame) -> float:
    if matrix.shape[0] < 2:
        return 1.0

    values = matrix.to_numpy(dtype=float)
    upper = values[np.triu_indices(values.shape[0], k=1)]
    if upper.size == 0:
        return 1.0

    mean = float(np.nanmean(upper))
    return mean if np.isfinite(mean) else 0.0


def _cluster_enb(weights: pd.Series, corr: pd.DataFrame) -> float:
    if corr.empty:
        return 0.0

    cluster_weights = weights.loc[corr.index].to_numpy(dtype=float)
    weight_sum = float(cluster_weights.sum())
    if weight_sum <= 0:
        return float(corr.shape[0])

    normalized = cluster_weights / weight_sum
    denom = float(normalized @ corr.to_numpy(dtype=float) @ normalized)
    if denom <= 0:
        return float(corr.shape[0])

    return float(1.0 / denom)


def compute_fragility_overview(holdings_df: pd.DataFrame, history: dict[int, pd.DataFrame]) -> dict:
    settings = get_settings()
    window_days = settings["window_days"]
    min_return_points = settings["min_return_points"]
    threshold = settings["correlation_threshold"]

    if holdings_df is None or holdings_df.empty:
        return _empty_result("No holdings found for fragility analysis.")

    df = holdings_df.copy()
    required_columns = {"tradingsymbol", "quantity", "last_price", "instrument_token"}
    if not required_columns.issubset(df.columns):
        return _empty_result("Holdings payload is missing required fields for fragility analysis.")

    df = df[df["quantity"].fillna(0) > 0].copy()

    if df.empty:
        return _empty_result("No active holdings found for fragility analysis.")

    df["value"] = df["last_price"].fillna(0) * df["quantity"].fillna(0)
    total_value = float(df["value"].sum())
    if total_value <= 0:
        return _empty_result("Holdings have no positive market value.")

    weights = (df.set_index("tradingsymbol")["value"] / total_value).sort_values(ascending=False)

    returns_map = {}
    excluded_symbols = []

    for _, row in df.iterrows():
        symbol = row["tradingsymbol"]
        token = row.get("instrument_token")
        hist = history.get(token)
        if hist is None or hist.empty or "close" not in hist:
            excluded_symbols.append(symbol)
            continue

        closes = (
            hist.sort_values("date")
            .tail(window_days + 1)
            .set_index("date")["close"]
            .astype(float)
        )
        if len(closes) < min_return_points + 1:
            excluded_symbols.append(symbol)
            continue

        returns = closes.pct_change().dropna()
        if len(returns) < min_return_points:
            excluded_symbols.append(symbol)
            continue

        returns_map[symbol] = returns

    if not returns_map:
        note = "Insufficient historical data to build the correlation heatmap."
        if excluded_symbols:
            note = f"{note} Excluded: {', '.join(excluded_symbols[:5])}"
        return _empty_result(note)

    returns_df = pd.concat(returns_map, axis=1).dropna(how="any")
    if returns_df.shape[0] < min_return_points:
        note = "Not enough overlapping return history to compute correlations."
        if excluded_symbols:
            note = f"{note} Excluded: {', '.join(excluded_symbols[:5])}"
        return _empty_result(note)

    corr = returns_df.corr().fillna(0.0)
    for sym in corr.columns:
        corr.loc[sym, sym] = 1.0

    symbols = list(corr.columns)

    parent = {sym: sym for sym in symbols}
    for i, left in enumerate(symbols):
        for right in symbols[i + 1 :]:
            if float(corr.loc[left, right]) >= threshold:
                _union(parent, left, right)

    components = defaultdict(list)
    for sym in symbols:
        components[_find(parent, sym)].append(sym)

    cluster_entries = []
    for idx, members in enumerate(components.values(), start=1):
        members = sorted(members, key=lambda s: (-float(weights.get(s, 0.0)), s))
        sub_corr = corr.loc[members, members]
        cluster_weight = float(weights.reindex(members).fillna(0.0).sum())
        cluster_enb = _cluster_enb(weights, sub_corr)
        avg_corr = _pairwise_mean(sub_corr)

        cluster_entries.append({
            "id": idx,
            "name": f"Cluster {idx}",
            "weight_pct": round(cluster_weight * 100, 1),
            "enb": round(cluster_enb, 2),
            "avg_corr": round(avg_corr, 2),
            "size": len(members),
            "symbols": [
                {
                    "symbol": sym,
                    "weight_pct": round(float(weights.get(sym, 0.0)) * 100, 1),
                    "value": round(float(df.loc[df["tradingsymbol"] == sym, "value"].iloc[0]), 2),
                }
                for sym in members
            ],
        })

    cluster_entries.sort(key=lambda x: (-x["weight_pct"], -x["size"], x["name"]))
    for idx, cluster in enumerate(cluster_entries, start=1):
        cluster["id"] = idx
        cluster["name"] = f"Cluster {idx}"

    ordered_symbols = []
    cluster_breaks = []
    for cluster in cluster_entries:
        if ordered_symbols:
            cluster_breaks.append(len(ordered_symbols))
        ordered_symbols.extend([item["symbol"] for item in cluster["symbols"]])

    heatmap = corr.reindex(index=ordered_symbols, columns=ordered_symbols)
    matrix = [[round(float(heatmap.iloc[i, j]), 4) for j in range(heatmap.shape[1])] for i in range(heatmap.shape[0])]

    portfolio_weights = weights.reindex(ordered_symbols).fillna(0.0)
    normalized = portfolio_weights.to_numpy(dtype=float)
    denom = float(normalized @ heatmap.to_numpy(dtype=float) @ normalized)
    portfolio_enb = float(1.0 / denom) if denom > 0 else float(len(ordered_symbols))

    upper = corr.to_numpy(dtype=float)[np.triu_indices(corr.shape[0], k=1)]
    avg_pairwise_corr = float(np.nanmean(upper)) if upper.size else 0.0

    strongest_pair = {"symbols": [], "corr": 0.0}
    if corr.shape[0] > 1:
        best = -1.0
        best_pair = ()
        for i, left in enumerate(ordered_symbols):
            for right in ordered_symbols[i + 1 :]:
                value = float(corr.loc[left, right])
                if value > best:
                    best = value
                    best_pair = (left, right)
        strongest_pair = {"symbols": list(best_pair), "corr": round(best, 2)}

    largest_cluster_weight = max((c["weight_pct"] for c in cluster_entries), default=0.0)

    warnings = []
    if excluded_symbols:
        warnings.append(
            f"Excluded {len(excluded_symbols)} holding(s) with insufficient history: "
            + ", ".join(excluded_symbols[:5])
        )

    enb_rows = []
    for cluster in cluster_entries:
        cluster_enb = cluster["enb"] if cluster["enb"] > 0 else 1.0
        for symbol in cluster["symbols"]:
            enb_rows.append({
                "symbol": symbol["symbol"],
                "cluster": cluster["name"],
                "weight_pct": symbol["weight_pct"],
                "cluster_enb": cluster["enb"],
                "enb_share": round(symbol["weight_pct"] / cluster_enb, 2),
            })

    enb_rows.sort(key=lambda row: (-row["enb_share"], -row["weight_pct"], row["symbol"]))

    return {
        "summary": {
            "total_holdings": int(len(df)),
            "usable_holdings": int(len(ordered_symbols)),
            "portfolio_enb": round(portfolio_enb, 2),
            "cluster_count": int(len(cluster_entries)),
            "largest_cluster_weight": round(largest_cluster_weight, 1),
            "avg_pairwise_corr": round(avg_pairwise_corr, 2),
            "window_days": window_days,
            "strongest_pair": strongest_pair,
        },
        "warnings": warnings,
        "heatmap": {
            "symbols": ordered_symbols,
            "matrix": matrix,
            "cluster_breaks": cluster_breaks,
        },
        "clusters": cluster_entries,
        "enb_list": enb_rows,
    }

