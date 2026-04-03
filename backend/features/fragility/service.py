from .data import get_holdings, get_historical_data
from .compute import compute_fragility_overview


def get_fragility_overview():
    df = get_holdings()
    tokens = df["instrument_token"].dropna().unique().tolist() if not df.empty else []
    history = get_historical_data(tokens) if tokens else {}
    return compute_fragility_overview(df, history)
