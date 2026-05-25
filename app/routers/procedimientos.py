from fastapi import APIRouter

from app.database import get_cursor
from app.schemas.usuario import CambiarPlanRequest, RegistrarUsuarioRequest
from app.utils import oracle_error

router = APIRouter(prefix="/procedimientos", tags=["Procedimientos Oracle"])


@router.post("/registrar-usuario", status_code=201)
def registrar_usuario(body: RegistrarUsuarioRequest):
    """SP_REGISTRAR_USUARIO."""
    try:
        with get_cursor() as cur:
            cur.callproc(
                "sp_registrar_usuario",
                [
                    body.id_plan,
                    body.id_usuario_referidor,
                    body.nombre,
                    body.apellido,
                    body.email,
                    body.telefono,
                    body.fecha_nacimiento,
                    body.ciudad_residencia,
                    body.fecha_vencimiento_pago,
                ],
            )
        return {"message": "Usuario registrado correctamente"}
    except Exception as exc:
        raise oracle_error(exc) from exc


@router.put("/cambiar-plan")
def cambiar_plan(body: CambiarPlanRequest):
    """SP_CAMBIAR_PLAN."""
    try:
        with get_cursor() as cur:
            cur.callproc(
                "sp_cambiar_plan",
                [body.id_usuario, body.nuevo_id_plan],
            )
        return {"message": "Plan actualizado correctamente"}
    except Exception as exc:
        raise oracle_error(exc) from exc
