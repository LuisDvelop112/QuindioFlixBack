from fastapi import APIRouter, HTTPException

from app.database import get_cursor
from app.utils import oracle_error

router = APIRouter(tags=["Salud"])


@router.get("/health")
def health():
    return {"status": "ok", "service": "QuindioFlix API"}


@router.get("/health/db")
def health_db():
    try:
        with get_cursor() as cur:
            cur.execute("SELECT 1 FROM DUAL")
            cur.fetchone()
        return {"status": "ok", "database": "connected"}
    except Exception as exc:
        raise oracle_error(exc) from exc
