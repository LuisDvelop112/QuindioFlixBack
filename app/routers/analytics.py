from fastapi import APIRouter, Query

from app.database import get_cursor
from app.utils import oracle_error, rows_to_list

router = APIRouter(prefix="/analytics", tags=["Reportes y analítica"])


# --- Componente D: consultas parametrizadas ---

@router.get("/top-contenido-por-ciudad")
def top_contenido_por_ciudad(ciudad: str):
    sql = """
        SELECT u.ciudad_residencia AS ciudad, c.titulo AS titulo_contenido,
               c.tipo_contenido, COUNT(r.id_reproduccion) AS total_reproducciones
        FROM usuario u
        JOIN perfil p ON p.id_usuario = u.id_usuario
        JOIN reproduccion r ON r.id_perfil = p.id_perfil
        JOIN contenido c ON c.id_contenido = r.id_contenido
        WHERE UPPER(u.ciudad_residencia) = UPPER(:ciudad)
        GROUP BY u.ciudad_residencia, c.titulo, c.tipo_contenido
        ORDER BY total_reproducciones DESC, titulo_contenido ASC
        FETCH FIRST 10 ROWS ONLY
    """
    try:
        with get_cursor() as cur:
            cur.execute(sql, {"ciudad": ciudad})
            return rows_to_list(cur)
    except Exception as exc:
        raise oracle_error(exc) from exc


@router.get("/ingresos-por-plan")
def ingresos_por_plan(mes: int = Query(..., ge=1, le=12), anio: int = Query(..., ge=2000)):
    sql = """
        SELECT pl.nombre AS plan, SUM(pg.monto_pagado) AS ingresos_totales
        FROM pago_suscripcion pg
        JOIN usuario u ON u.id_usuario = pg.id_usuario
        JOIN plan_suscripcion pl ON pl.id_plan = u.id_plan
        WHERE pg.estado_pago = 'EXITOSO'
          AND EXTRACT(MONTH FROM pg.fecha_pago) = :mes
          AND EXTRACT(YEAR FROM pg.fecha_pago) = :anio
        GROUP BY pl.nombre
        ORDER BY ingresos_totales DESC
    """
    try:
        with get_cursor() as cur:
            cur.execute(sql, {"mes": mes, "anio": anio})
            return rows_to_list(cur)
    except Exception as exc:
        raise oracle_error(exc) from exc


@router.get("/calificacion-por-genero")
def calificacion_por_genero(genero: str):
    sql = """
        SELECT g.nombre AS genero, c.titulo AS titulo_contenido, c.tipo_contenido,
               ROUND(AVG(cc.estrellas), 2) AS calificacion_promedio,
               COUNT(cc.id_calificacion) AS cantidad_calificaciones
        FROM genero g
        JOIN contenido_genero cg ON cg.id_genero = g.id_genero
        JOIN contenido c ON c.id_contenido = cg.id_contenido
        LEFT JOIN calificacion_contenido cc ON cc.id_contenido = c.id_contenido
        WHERE UPPER(g.nombre) = UPPER(:genero)
        GROUP BY g.nombre, c.titulo, c.tipo_contenido
        ORDER BY calificacion_promedio DESC NULLS LAST
    """
    try:
        with get_cursor() as cur:
            cur.execute(sql, {"genero": genero})
            return rows_to_list(cur)
    except Exception as exc:
        raise oracle_error(exc) from exc


# --- Vistas materializadas ---

@router.get("/mv/consumo-contenido")
def mv_consumo_contenido(limite: int = Query(20, ge=1, le=100)):
    sql = """
        SELECT * FROM MV_CONSUMO_CONTENIDO
        ORDER BY TOTAL_REPRODUCCIONES DESC NULLS LAST
        FETCH FIRST :limite ROWS ONLY
    """
    try:
        with get_cursor() as cur:
            cur.execute(sql, {"limite": limite})
            return rows_to_list(cur)
    except Exception as exc:
        raise oracle_error(exc) from exc


@router.get("/mv/reproducciones-diarias-ciudad")
def mv_reproducciones_ciudad(ciudad: str | None = None):
    sql = "SELECT * FROM MV_REPRODUCCIONES_DIARIAS_CIUDAD WHERE 1=1"
    params: dict = {}
    if ciudad:
        sql += " AND UPPER(CIUDAD) = UPPER(:ciudad)"
        params["ciudad"] = ciudad
    sql += " ORDER BY FECHA DESC"
    try:
        with get_cursor() as cur:
            cur.execute(sql, params)
            return rows_to_list(cur)
    except Exception as exc:
        raise oracle_error(exc) from exc


@router.post("/mv/refresh")
def refresh_materialized_views():
    try:
        with get_cursor() as cur:
            cur.execute(
                "BEGIN DBMS_MVIEW.REFRESH('MV_CONSUMO_CONTENIDO'); "
                "DBMS_MVIEW.REFRESH('MV_REPRODUCCIONES_DIARIAS_CIUDAD'); END;"
            )
        return {"message": "Vistas materializadas actualizadas"}
    except Exception as exc:
        raise oracle_error(exc) from exc


# --- Pivot / Unpivot / Rollup / Cube ---

@router.get("/pivot/usuarios-ciudad-plan")
def pivot_usuarios_ciudad_plan():
    sql = """
        SELECT * FROM (
            SELECT u.ciudad_residencia AS ciudad, pl.nombre AS plan, u.id_usuario
            FROM usuario u
            JOIN plan_suscripcion pl ON pl.id_plan = u.id_plan
            WHERE u.estado_cuenta = 'ACTIVA'
        ) src
        PIVOT (COUNT(id_usuario) FOR plan IN ('BASICO' AS basico, 'ESTANDAR' AS estandar, 'PREMIUM' AS premium))
        ORDER BY ciudad
    """
    try:
        with get_cursor() as cur:
            cur.execute(sql)
            return rows_to_list(cur)
    except Exception as exc:
        raise oracle_error(exc) from exc


@router.get("/pivot/reproducciones-tipo-dispositivo")
def pivot_reproducciones():
    sql = """
        SELECT * FROM (
            SELECT c.tipo_contenido, r.dispositivo, r.id_reproduccion
            FROM reproduccion r JOIN contenido c ON c.id_contenido = r.id_contenido
        ) src
        PIVOT (COUNT(id_reproduccion) FOR dispositivo IN (
            'CELULAR' AS celular, 'TABLET' AS tablet, 'TV' AS tv, 'COMPUTADOR' AS computador
        ))
        ORDER BY tipo_contenido
    """
    try:
        with get_cursor() as cur:
            cur.execute(sql)
            return rows_to_list(cur)
    except Exception as exc:
        raise oracle_error(exc) from exc


@router.get("/rollup/ingresos-ciudad-plan")
def rollup_ingresos():
    sql = """
        SELECT NVL(u.ciudad_residencia, 'TOTAL_GENERAL') AS ciudad,
               NVL(pl.nombre, 'SUBTOTAL_CIUDAD') AS plan,
               SUM(pg.monto_pagado) AS ingresos_totales
        FROM pago_suscripcion pg
        JOIN usuario u ON u.id_usuario = pg.id_usuario
        JOIN plan_suscripcion pl ON pl.id_plan = u.id_plan
        WHERE pg.estado_pago = 'EXITOSO'
        GROUP BY ROLLUP (u.ciudad_residencia, pl.nombre)
        ORDER BY ciudad NULLS LAST, plan NULLS LAST
    """
    try:
        with get_cursor() as cur:
            cur.execute(sql)
            return rows_to_list(cur)
    except Exception as exc:
        raise oracle_error(exc) from exc


@router.get("/cube/reproducciones-tipo-dispositivo")
def cube_reproducciones():
    sql = """
        SELECT NVL(c.tipo_contenido, 'TODOS_TIPOS') AS tipo_contenido,
               NVL(r.dispositivo, 'TODOS_DISPOSITIVOS') AS dispositivo,
               COUNT(r.id_reproduccion) AS total_reproducciones
        FROM reproduccion r
        JOIN contenido c ON c.id_contenido = r.id_contenido
        GROUP BY CUBE (c.tipo_contenido, r.dispositivo)
        ORDER BY tipo_contenido NULLS LAST, dispositivo NULLS LAST
    """
    try:
        with get_cursor() as cur:
            cur.execute(sql)
            return rows_to_list(cur)
    except Exception as exc:
        raise oracle_error(exc) from exc
