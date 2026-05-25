from typing import Optional

from fastapi import APIRouter, Query

from app.database import get_cursor
from app.utils import oracle_error, rows_to_list

router = APIRouter(prefix="/pagos", tags=["Pagos"])


@router.get("")
def listar_pagos(
    id_usuario: Optional[int] = None,
    estado: Optional[str] = None,
    limite: int = Query(50, ge=1, le=200),
):
    sql = "SELECT * FROM pago_suscripcion WHERE 1=1"
    params: dict = {"limite": limite}
    if id_usuario:
        sql += " AND id_usuario = :id_usuario"
        params["id_usuario"] = id_usuario
    if estado:
        sql += " AND estado_pago = :estado"
        params["estado"] = estado.upper()
    sql += " ORDER BY fecha_pago DESC FETCH FIRST :limite ROWS ONLY"
    try:
        with get_cursor() as cur:
            cur.execute(sql, params)
            return rows_to_list(cur)
    except Exception as exc:
        raise oracle_error(exc) from exc
