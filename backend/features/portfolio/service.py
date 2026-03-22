from .data import get_holdings
from .compute import compute_overview
from .settings import get_settings

def get_overview():
    df = get_holdings()
    config = get_settings()

    return compute_overview(df, config)