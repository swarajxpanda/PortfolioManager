from fastapi import APIRouter

from .service import get_fragility_overview

router = APIRouter()


@router.get("/overview")
def fragility_overview():
    return get_fragility_overview()
