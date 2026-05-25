from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class ReproduccionCreate(BaseModel):
    id_perfil: int
    id_contenido: int
    fecha_hora_inicio: datetime
    dispositivo: Literal["CELULAR", "TABLET", "TV", "COMPUTADOR"]
    id_episodio: Optional[int] = None
    fecha_hora_fin: Optional[datetime] = None
    porcentaje_avance: float = Field(default=0, ge=0, le=100)


class CalificacionCreate(BaseModel):
    id_perfil: int
    id_contenido: int
    estrellas: int = Field(ge=1, le=5)
    resena: Optional[str] = Field(default=None, max_length=1000)
