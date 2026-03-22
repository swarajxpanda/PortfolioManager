from kiteconnect import KiteConnect
from config import API_KEY

kite = KiteConnect(api_key=API_KEY)

_access_token = None


def set_access_token(token: str):
    global _access_token
    _access_token = token
    kite.set_access_token(token)


def is_authenticated():
    return _access_token is not None


def get_kite():
    if not _access_token:
        raise Exception("Not authenticated")
    return kite