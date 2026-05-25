from datetime import date
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class RegistrarUsuarioRequest(BaseModel):
    id_plan: int
    nombre: str = Field(max_length=80)
    apellido: str = Field(max_length=80)
    email: EmailStr
    fecha_nacimiento: date
    ciudad_residencia: str = Field(max_length=80)
    id_usuario_referidor: Optional[int] = None
    telefono: Optional[str] = Field(default=None, max_length=20)
    fecha_vencimiento_pago: Optional[date] = None


class CambiarPlanRequest(BaseModel):
    id_usuario: int
    nuevo_id_plan: int
