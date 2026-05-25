from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.database import get_cursor
from app.utils import oracle_error, rows_to_list

router = APIRouter(prefix="/usuarios", tags=["Usuarios y planes"])


@router.get("/roles")
def listar_roles():
    try:
        with get_cursor() as cur:
            cur.execute("SELECT * FROM rol ORDER BY nombre")
            return rows_to_list(cur)
    except Exception as exc:
        raise oracle_error(exc) from exc


@router.get("/planes")
def listar_planes():
    try:
        with get_cursor() as cur:
            cur.execute(
                "SELECT * FROM plan_suscripcion WHERE activo = 'S' ORDER BY precio_mensual"
            )
            return rows_to_list(cur)
    except Exception as exc:
        raise oracle_error(exc) from exc


@router.get("")
def listar_usuarios(
    estado: Optional[str] = None,
    ciudad: Optional[str] = None,
    limite: int = Query(50, ge=1, le=200),
):
    sql = """
        SELECT u.*, p.nombre AS plan_nombre
        FROM usuario u
        JOIN plan_suscripcion p ON p.id_plan = u.id_plan
        WHERE 1=1
    """
    params: dict = {"limite": limite}
    if estado:
        sql += " AND u.estado_cuenta = :estado"
        params["estado"] = estado.upper()
    if ciudad:
        sql += " AND UPPER(u.ciudad_residencia) = UPPER(:ciudad)"
        params["ciudad"] = ciudad
    sql += " ORDER BY u.fecha_registro DESC FETCH FIRST :limite ROWS ONLY"
    try:
        with get_cursor() as cur:
            cur.execute(sql, params)
            return rows_to_list(cur)
    except Exception as exc:
        raise oracle_error(exc) from exc


@router.get("/{id_usuario}")
def obtener_usuario(id_usuario: int):
    try:
        with get_cursor() as cur:
            cur.execute(
                """
                SELECT u.*, p.nombre AS plan_nombre, p.precio_mensual
                FROM usuario u
                JOIN plan_suscripcion p ON p.id_plan = u.id_plan
                WHERE u.id_usuario = :id
                """,
                {"id": id_usuario},
            )
            rows = rows_to_list(cur)
            if not rows:
                raise HTTPException(404, "Usuario no encontrado")
            return rows[0]
    except HTTPException:
        raise
    except Exception as exc:
        raise oracle_error(exc) from exc


@router.get("/{id_usuario}/perfiles")
def listar_perfiles(id_usuario: int):
    try:
        with get_cursor() as cur:
            cur.execute(
                "SELECT * FROM perfil WHERE id_usuario = :id ORDER BY fecha_creacion",
                {"id": id_usuario},
            )
            return rows_to_list(cur)
    except Exception as exc:
        raise oracle_error(exc) from exc

