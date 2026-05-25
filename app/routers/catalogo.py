from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.database import get_cursor
from app.utils import oracle_error, rows_to_list

router = APIRouter(prefix="/catalogo", tags=["Catálogo"])


@router.get("/generos")
def listar_generos(activo: Optional[str] = Query(None, pattern="^[SN]$")):
    sql = "SELECT * FROM genero"
    params: dict = {}
    if activo:
        sql += " WHERE activo = :activo"
        params["activo"] = activo
    sql += " ORDER BY nombre"
    try:
        with get_cursor() as cur:
            cur.execute(sql, params)
            return rows_to_list(cur)
    except Exception as exc:
        raise oracle_error(exc) from exc


@router.get("/contenidos")
def listar_contenidos(
    tipo: Optional[str] = None,
    activo: str = Query("S", pattern="^[SN]$"),
    limite: int = Query(50, ge=1, le=200),
):
    sql = """
        SELECT c.*, e.nombre || ' ' || e.apellido AS publicador
        FROM contenido c
        JOIN empleado e ON e.id_empleado = c.id_empleado_publica
        WHERE c.activo = :activo
    """
    params: dict = {"activo": activo, "limite": limite}
    if tipo:
        sql += " AND c.tipo_contenido = :tipo"
        params["tipo"] = tipo.upper()
    sql += " ORDER BY c.fecha_agregado DESC FETCH FIRST :limite ROWS ONLY"
    try:
        with get_cursor() as cur:
            cur.execute(sql, params)
            return rows_to_list(cur)
    except Exception as exc:
        raise oracle_error(exc) from exc


@router.get("/contenidos/{id_contenido}")
def obtener_contenido(id_contenido: int):
    try:
        with get_cursor() as cur:
            cur.execute(
                """
                SELECT c.*,
                       LISTAGG(g.nombre, ', ') WITHIN GROUP (ORDER BY g.nombre) AS generos
                FROM contenido c
                LEFT JOIN contenido_genero cg ON cg.id_contenido = c.id_contenido
                LEFT JOIN genero g ON g.id_genero = cg.id_genero
                WHERE c.id_contenido = :id
                GROUP BY c.id_contenido, c.id_empleado_publica, c.tipo_contenido,
                         c.titulo, c.anio_lanzamiento, c.duracion_minutos, c.sinopsis,
                         c.clasificacion_edad, c.fecha_agregado, c.es_original, c.activo
                """,
                {"id": id_contenido},
            )
            rows = rows_to_list(cur)
            if not rows:
                raise HTTPException(404, "Contenido no encontrado")
            return rows[0]
    except HTTPException:
        raise
    except Exception as exc:
        raise oracle_error(exc) from exc


@router.get("/contenidos/{id_contenido}/temporadas")
def listar_temporadas(id_contenido: int):
    try:
        with get_cursor() as cur:
            cur.execute(
                """
                SELECT * FROM temporada
                WHERE id_contenido = :id
                ORDER BY numero_temporada
                """,
                {"id": id_contenido},
            )
            return rows_to_list(cur)
    except Exception as exc:
        raise oracle_error(exc) from exc


@router.get("/temporadas/{id_temporada}/episodios")
def listar_episodios(id_temporada: int):
    try:
        with get_cursor() as cur:
            cur.execute(
                """
                SELECT * FROM episodio
                WHERE id_temporada = :id
                ORDER BY numero_episodio
                """,
                {"id": id_temporada},
            )
            return rows_to_list(cur)
    except Exception as exc:
        raise oracle_error(exc) from exc
