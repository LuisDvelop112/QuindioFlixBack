from fastapi import APIRouter, HTTPException

from app.database import get_cursor
from app.utils import oracle_error

router = APIRouter(prefix="/funciones", tags=["Funciones Oracle"])


@router.get("/monto-usuario/{id_usuario}")
def calcular_monto(id_usuario: int):
    """FN_CALCULAR_MONTO — próximo pago con descuento."""
    try:
        with get_cursor() as cur:
            cur.execute(
                "SELECT FN_CALCULAR_MONTO(:id) AS monto FROM DUAL",
                {"id": id_usuario},
            )
            row = cur.fetchone()
            if row is None or row[0] is None:
                raise HTTPException(404, "Usuario o plan no encontrado")
            return {"id_usuario": id_usuario, "monto_calculado": float(row[0])}
    except HTTPException:
        raise
    except Exception as exc:
        raise oracle_error(exc) from exc


@router.get("/contenido-recomendado/{id_perfil}")
def contenido_recomendado(id_perfil: int):
    """FN_CONTENIDO_RECOMENDADO — sugerencia por historial del perfil."""
    try:
        with get_cursor() as cur:
            cur.execute(
                "SELECT FN_CONTENIDO_RECOMENDADO(:id) AS id_contenido FROM DUAL",
                {"id": id_perfil},
            )
            row = cur.fetchone()
            id_contenido = row[0] if row else None
            if id_contenido is None:
                return {"id_perfil": id_perfil, "id_contenido": None, "mensaje": "Sin recomendación"}
            cur.execute(
                "SELECT titulo, tipo_contenido FROM contenido WHERE id_contenido = :id",
                {"id": id_contenido},
            )
            det = cur.fetchone()
            return {
                "id_perfil": id_perfil,
                "id_contenido": int(id_contenido),
                "titulo": det[0] if det else None,
                "tipo_contenido": det[1] if det else None,
            }
    except Exception as exc:
        raise oracle_error(exc) from exc
