from fastapi import APIRouter

from app.database import get_cursor
from app.utils import oracle_error, rows_to_list

router = APIRouter(prefix="/empleados", tags=["Empleados"])


@router.get("/departamentos")
def listar_departamentos():
    try:
        with get_cursor() as cur:
            cur.execute(
                "SELECT * FROM departamento WHERE activo = 'S' ORDER BY nombre"
            )
            return rows_to_list(cur)
    except Exception as exc:
        raise oracle_error(exc) from exc


@router.get("")
def listar_empleados():
    try:
        with get_cursor() as cur:
            cur.execute(
                """
                SELECT e.*, d.nombre AS departamento
                FROM empleado e
                JOIN departamento d ON d.id_departamento = e.id_departamento
                WHERE e.activo = 'S'
                ORDER BY e.apellido, e.nombre
                """
            )
            return rows_to_list(cur)
    except Exception as exc:
        raise oracle_error(exc) from exc
