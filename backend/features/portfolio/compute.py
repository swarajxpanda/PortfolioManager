def compute_overview(df, config):
    df["value"] = df["last_price"] * df["quantity"]
    df["invested"] = df["average_price"] * df["quantity"]
    df["pnl"] = df["value"] - df["invested"]

    total_value = df["value"].sum()
    total_invested = df["invested"].sum()
    total_pnl = df["pnl"].sum()

    capital_at_risk = df[df["pnl"] < 0]["value"].sum()

    # ---------- ALLOCATION ----------
    def classify(sym):
        for g, arr in config["groups"].items():
            if sym in arr:
                return g
        return "Unassigned"

    df["group"] = df["tradingsymbol"].apply(classify)

    grouped = df.groupby("group").agg({
        "value": "sum",
        "invested": "sum",
        "pnl": "sum"
    }).reset_index()

    allocation = []

    for _, r in grouped.iterrows():
        g = r["group"]
        val = r["value"]
        inv = r["invested"]
        pnl = r["pnl"]

        pct = (val / total_value) * 100
        pnl_pct = (pnl / inv) * 100 if inv else 0

        t = config["targets"].get(g)
        if t:
            tmin, tmax = t
            if pct > tmax:
                amt = val - (tmax / 100) * total_value
                action = {"type": "TRIM", "amount": int(amt)}
            elif pct < tmin:
                amt = (tmin / 100) * total_value - val
                action = {"type": "ADD", "amount": int(amt)}
            else:
                action = {"type": "HOLD", "amount": 0}
            target_str = f"{tmin}-{tmax}%"
        else:
            action = {"type": "HOLD", "amount": 0}
            target_str = "—"

        allocation.append({
            "group": g,
            "value": float(val),
            "allocation_pct": round(pct, 1),
            "pnl": float(pnl),
            "pnl_pct": round(pnl_pct, 1),
            "target": target_str,
            "action": action
        })

    # ---------- CONCENTRATION ----------
    df_sorted = df.sort_values("value", ascending=False)

    top5 = df_sorted.head(5)
    top5_val = top5["value"].sum()
    top5_pct = (top5_val / total_value) * 100

    top5_limit = config["concentration"]["top5"]
    top5_action = (
        {"type": "TRIM", "amount": int(top5_val - (top5_limit/100)*total_value)}
        if top5_pct > top5_limit else {"type": "HOLD", "amount": 0}
    )

    largest = df_sorted.iloc[0]
    largest_pct = (largest["value"] / total_value) * 100
    single_limit = config["concentration"]["single"]

    largest_action = (
        {"type": "TRIM", "amount": int(largest["value"] - (single_limit/100)*total_value)}
        if largest_pct > single_limit else {"type": "HOLD", "amount": 0}
    )

    concentration = [
        {
            "metric": "Top 5 Holdings",
            "value": float(top5_val),
            "value_pct": round(top5_pct, 1),
            "pnl": float(top5["pnl"].sum()),
            "limit": f"< {top5_limit}%",
            "action": top5_action
        },
        {
            "metric": f"Largest Holding - {largest['tradingsymbol']}",
            "value": float(largest["value"]),
            "value_pct": round(largest_pct, 1),
            "pnl": float(largest["pnl"]),
            "limit": f"≤ {single_limit}%",
            "action": largest_action
        }
    ]

    return {
        "health": {
            "total_value": float(total_value),
            "total_pnl": float(total_pnl),
            "return_pct": float((total_pnl / total_invested) * 100) if total_invested else 0,
            "capital_at_risk": float(capital_at_risk)
        },
        "allocation": allocation,
        "concentration": concentration
    }