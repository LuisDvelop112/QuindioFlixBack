from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import close_pool, init_pool
from app.routers import (
    analytics,
    catalogo,
    consumo,
    empleados,
    funciones,
    health,
    pagos,
    procedimientos,
    usuarios,
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_pool()
    yield
    close_pool()


app = FastAPI(
    title="QuindioFlix API",
    description=(
        "Backend liviano en FastAPI para Oracle. Expone tablas, vistas materializadas, "
        "consultas analíticas (pivot/rollup/cube), funciones y procedimientos del esquema QuindioFlix."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(catalogo.router)
app.include_router(usuarios.router)
app.include_router(consumo.router)
app.include_router(empleados.router)
app.include_router(pagos.router)
app.include_router(funciones.router)
app.include_router(procedimientos.router)
app.include_router(analytics.router)


@app.get("/")
def root():
    return {
        "proyecto": "QuindioFlix",
        "docs": "/docs",
        "health": "/health",
        "health_db": "/health/db",
    }
