from fastapi import APIRouter, Request
from .service import get_overview
from .settings import get_settings, save_settings, reset_settings
from .data import get_holdings
from core.kite import is_authenticated

router = APIRouter()


@router.get("/overview")
def overview():
    return get_overview()


@router.get("/settings")
def read_settings():
    config = get_settings()

    # send all holdings symbols so frontend can compute the unassigned pool
    holdings_symbols = []
    if is_authenticated():
        try:
            df = get_holdings()
            holdings_symbols = sorted(df["tradingsymbol"].tolist())
        except Exception:
            pass

    return {"config": config, "holdings": holdings_symbols}


@router.put("/settings")
async def update_settings(request: Request):
    body = await request.json()
    save_settings(body)
    return {"status": "ok"}


@router.post("/settings/reset")
def do_reset_settings():
    defaults = reset_settings()
    return {"config": defaults, "holdings": []}