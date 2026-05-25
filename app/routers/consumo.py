from datetime import date

import oracledb
from fastapi import APIRouter, HTTPException, Query

from app.database import get_cursor
from app.utils import row_to_dict
from app.schemas.consumo import CalificacionCreate, ReproduccionCreate
from app.utils import oracle_error, rows_to_list

router = APIRouter(prefix="/consumo", tags=["Consumo"])


@router.get("/reproducciones")
def listar_reproducciones(
    id_perfil: int | None = None,
    limite: int = Query(50, ge=1, le=200),
):
    sql = """
        SELECT r.*, c.titulo
        FROM reproduccion r
        JOIN contenido c ON c.id_contenido = r.id_contenido
        WHERE 1=1
    """
    params: dict = {"limite": limite}
    if id_perfil:
        sql += " AND r.id_perfil = :id_perfil"
        params["id_perfil"] = id_perfil
    sql += " ORDER BY r.fecha_hora_inicio DESC FETCH FIRST :limite ROWS ONLY"
    try:
        with get_cursor() as cur:
            cur.execute(sql, params)
            return rows_to_list(cur)
    except Exception as exc:
        raise oracle_error(exc) from exc


@router.post("/reproducciones", status_code=201)
def registrar_reproduccion(body: ReproduccionCreate):
    try:
        with get_cursor() as cur:
            cur.execute(
                """
                INSERT INTO reproduccion (
                    id_perfil, id_contenido, id_episodio,
                    fecha_hora_inicio, fecha_hora_fin, dispositivo, porcentaje_avance
                ) VALUES (
                    :id_perfil, :id_contenido, :id_episodio,
                    :fecha_inicio, :fecha_fin, :dispositivo, :avance
                )
                """,
                {
                    "id_perfil": body.id_perfil,
                    "id_contenido": body.id_contenido,
                    "id_episodio": body.id_episodio,
                    "fecha_inicio": body.fecha_hora_inicio,
                    "fecha_fin": body.fecha_hora_fin,
                    "dispositivo": body.dispositivo,
                    "avance": body.porcentaje_avance,
                },
            )
        return {"message": "Reproducción registrada"}
    except Exception as exc:
        raise oracle_error(exc) from exc


@router.get("/perfiles/{id_perfil}/favoritos")
def listar_favoritos(id_perfil: int):
    try:
        with get_cursor() as cur:
            cur.execute(
                """
                SELECT f.*, c.titulo, c.tipo_contenido
                FROM favorito_perfil f
                JOIN contenido c ON c.id_contenido = f.id_contenido
                WHERE f.id_perfil = :id
                ORDER BY f.fecha_agregado DESC
                """,
                {"id": id_perfil},
            )
            return rows_to_list(cur)
    except Exception as exc:
        raise oracle_error(exc) from exc


@router.get("/contenidos/{id_contenido}/calificaciones")
def listar_calificaciones(id_contenido: int):
    try:
        with get_cursor() as cur:
            cur.execute(
                """
                SELECT cc.*, p.nombre AS perfil_nombre
                FROM calificacion_contenido cc
                JOIN perfil p ON p.id_perfil = cc.id_perfil
                WHERE cc.id_contenido = :id
                ORDER BY cc.fecha_calificacion DESC
                """,
                {"id": id_contenido},
            )
            return rows_to_list(cur)
    except Exception as exc:
        raise oracle_error(exc) from exc


@router.post("/calificaciones", status_code=201)
def crear_calificacion(body: CalificacionCreate):
    try:
        with get_cursor() as cur:
            cur.execute(
                """
                INSERT INTO calificacion_contenido (id_perfil, id_contenido, estrellas, resena)
                VALUES (:id_perfil, :id_contenido, :estrellas, :resena)
                """,
                body.model_dump(),
            )
        return {"message": "Calificación registrada"}
    except Exception as exc:
        raise oracle_error(exc) from exc


@router.get("/reportes/morosos")
def usuarios_morosos():
    """Equivalente al cursor c_listar_usuarios_morosos."""
    sql = """
        SELECT id_usuario, nombre, apellido, email, estado_cuenta, fecha_vencimiento_pago
        FROM usuario
        WHERE estado_cuenta = 'SUSPENDIDA'
           OR (fecha_vencimiento_pago IS NOT NULL AND fecha_vencimiento_pago < SYSDATE)
        ORDER BY fecha_vencimiento_pago NULLS LAST
    """
    try:
        with get_cursor() as cur:
            cur.execute(sql)
            return rows_to_list(cur)
    except Exception as exc:
        raise oracle_error(exc) from exc


@router.get("/reportes/popularidad")
def popularidad_contenido(limite: int = Query(20, ge=1, le=100)):
    """Equivalente al cursor c_calcular_popularidad_contenido."""
    sql = """
        SELECT c.id_contenido, c.titulo, c.tipo_contenido,
               COUNT(r.id_reproduccion) AS total_reproducciones,
               ROUND(AVG(r.porcentaje_avance), 2) AS promedio_avance
        FROM contenido c
        JOIN reproduccion r ON r.id_contenido = c.id_contenido
        GROUP BY c.id_contenido, c.titulo, c.tipo_contenido
        ORDER BY total_reproducciones DESC, promedio_avance DESC
        FETCH FIRST :limite ROWS ONLY
    """
    try:
        with get_cursor() as cur:
            cur.execute(sql, {"limite": limite})
            return rows_to_list(cur)
    except Exception as exc:
        raise oracle_error(exc) from exc


@router.get("/reportes/consumo-perfil")
def reporte_consumo_perfil(
    id_perfil: int,
    fecha_inicio: date,
    fecha_fin: date,
):
    """Llama sp_reporte_consumo o replica su consulta."""
    if fecha_inicio > fecha_fin:
        raise HTTPException(400, "La fecha inicial no puede ser mayor que la final")
    try:
        with get_cursor() as cur:
            ref = cur.var(oracledb.CURSOR)
            cur.callproc(
                "sp_reporte_consumo",
                [id_perfil, fecha_inicio, fecha_fin, ref],
            )
            result_cur = ref.getvalue()
            columns = [d[0] for d in result_cur.description]
            return [row_to_dict(columns, row) for row in result_cur.fetchall()]
    except Exception as exc:
        if "ORA-06550" in str(exc) or "does not exist" in str(exc).lower():
            sql = """
                SELECT c.id_contenido, c.titulo, c.tipo_contenido,
                       COUNT(r.id_reproduccion) AS total_reproducciones,
                       ROUND(AVG(r.porcentaje_avance), 2) AS promedio_avance
                FROM reproduccion r
                JOIN contenido c ON c.id_contenido = r.id_contenido
                WHERE r.id_perfil = :id_perfil
                  AND TRUNC(r.fecha_hora_inicio) BETWEEN :ini AND :fin
                GROUP BY c.id_contenido, c.titulo, c.tipo_contenido
                ORDER BY total_reproducciones DESC
            """
            with get_cursor() as cur:
                cur.execute(
                    sql,
                    {"id_perfil": id_perfil, "ini": fecha_inicio, "fin": fecha_fin},
                )
                return rows_to_list(cur)
        raise oracle_error(exc) from exc
