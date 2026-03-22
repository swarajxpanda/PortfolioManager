import pandas as pd
from core.kite import get_kite

def get_holdings():
    kite = get_kite()
    return pd.DataFrame(kite.holdings())