from datetime import date, timedelta

import numpy as np
import pandas as pd


def fetch_price_matrix(kite, df, days=252):
    """Fetch daily close prices for all holdings and return a price matrix.

    Parameters
    ----------
    kite : KiteConnect
        Authenticated Kite API client.
    df : pd.DataFrame
        Portfolio DataFrame with ``tradingsymbol`` and ``instrument_token`` columns.
    days : int, optional
        Number of calendar days of history to fetch (default 252).

    Returns
    -------
    pd.DataFrame
        Columns are trading symbols, index is date, values are closing prices.
    """
    to_date = date.today()
    from_date = to_date - timedelta(days=days)

    price_series = {}
    for _, row in df.iterrows():
        symbol = row["tradingsymbol"]
        token = row["instrument_token"]
        try:
            records = kite.historical_data(
                token,
                from_date=from_date,
                to_date=to_date,
                interval="day",
            )
        except Exception:
            continue
        if not records:
            continue
        hist = pd.DataFrame(records)
        hist["date"] = pd.to_datetime(hist["date"]).dt.date
        hist.set_index("date", inplace=True)
        if "close" in hist.columns:
            price_series[symbol] = hist["close"]

    if not price_series:
        return pd.DataFrame()

    price_matrix = pd.DataFrame(price_series)
    price_matrix.sort_index(inplace=True)
    price_matrix.ffill(inplace=True)
    price_matrix.dropna(inplace=True)
    return price_matrix


def compute_log_returns(price_matrix):
    """Compute log returns from a price matrix.

    Parameters
    ----------
    price_matrix : pd.DataFrame
        Price matrix with stocks as columns and dates as index.

    Returns
    -------
    pd.DataFrame
        Log returns matrix (first row dropped).
    """
    log_returns = np.log(price_matrix / price_matrix.shift(1))
    log_returns = log_returns.iloc[1:]
    return log_returns


def compute_portfolio_weights(df, stock_list):
    """Compute portfolio weights for the given stocks.

    Parameters
    ----------
    df : pd.DataFrame
        Portfolio DataFrame with ``tradingsymbol`` and ``value`` columns.
    stock_list : list[str]
        List of trading symbols present in the price matrix.

    Returns
    -------
    np.ndarray
        Normalised weight for each stock in *stock_list* order.
    """
    subset = df[df["tradingsymbol"].isin(stock_list)].copy()
    subset = subset.set_index("tradingsymbol").loc[stock_list]
    total_value = subset["value"].sum()
    if total_value == 0:
        return np.zeros(len(stock_list))
    weights = (subset["value"] / total_value).values
    return weights


def get_fragility_data(kite, df):
    """Orchestrate data fetching and validation for fragility analysis.

    Parameters
    ----------
    kite : KiteConnect
        Authenticated Kite API client.
    df : pd.DataFrame
        Portfolio DataFrame with columns ``tradingsymbol``, ``instrument_token``,
        ``value``, ``category``, etc.

    Returns
    -------
    dict
        A result dictionary with ``status``, ``warning_message``, and (on success)
        ``price_matrix``, ``returns_matrix``, ``weights``, and ``stock_names``.
    """
    # --- guard: minimum holdings ---
    if len(df) < 8:
        return {
            "status": "insufficient_holdings",
            "warning_message": "Need at least 8 holdings for fragility analysis",
        }

    # --- guard: mostly cash ---
    total_value = df["value"].sum()
    if total_value > 0:
        equity_mask = df["category"].str.upper() != "CASH"
        equity_value = df.loc[equity_mask, "value"].sum()
        if equity_value / total_value < 0.20:
            return {
                "status": "mostly_cash",
                "warning_message": "Portfolio is mostly cash — fragility analysis not meaningful",
            }

    # --- fetch prices ---
    price_matrix = fetch_price_matrix(kite, df)

    # --- guard: insufficient price history ---
    if price_matrix.empty or len(price_matrix) < 90:
        return {
            "status": "insufficient_data",
            "warning_message": "Need at least 90 days of price history",
        }

    # --- compute returns and weights ---
    stock_names = list(price_matrix.columns)
    returns_matrix = compute_log_returns(price_matrix)
    weights = compute_portfolio_weights(df, stock_names)

    # --- build warning if some stocks were skipped ---
    all_symbols = set(df["tradingsymbol"])
    fetched_symbols = set(stock_names)
    skipped = all_symbols - fetched_symbols
    warning_message = None
    if skipped:
        warning_message = f"Skipped {len(skipped)} stock(s) with no price data: {', '.join(sorted(skipped))}"

    return {
        "status": "ok",
        "warning_message": warning_message,
        "price_matrix": price_matrix,
        "returns_matrix": returns_matrix,
        "weights": weights,
        "stock_names": stock_names,
    }
