# QuindioFlix API (FastAPI + Oracle)

Backend liviano que expone el esquema **QuindioFlix** (Oracle XE) para consumirlo desde un frontend en React.

## Requisitos

- Python 3.11+
- Oracle Database XE con el esquema cargado (`quindioflix`)
- Scripts del anexo ejecutados (DDL, población, funciones, procedimientos, vistas materializadas)

## Configuración

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
# Editar .env con tu DSN y credenciales
```

Variables en `.env`:

| Variable | Descripción |
|----------|-------------|
| `ORACLE_USER` | Usuario (`quindioflix`) |
| `ORACLE_PASSWORD` | Contraseña |
| `ORACLE_DSN` | Ej: `localhost:1521/XEPDB1` |
| `CORS_ORIGINS` | URL del frontend React |

## Ejecutar

```powershell
python run.py
```

- API: http://localhost:8000  
- Swagger: http://localhost:8000/docs  
- Salud BD: http://localhost:8000/health/db  

## Módulos expuestos

| Prefijo | Origen en el anexo |
|---------|-------------------|
| `/catalogo` | Tablas `genero`, `contenido`, `temporada`, `episodio` |
| `/usuarios` | `usuario`, `perfil`, `plan_suscripcion`, `rol` |
| `/consumo` | `reproduccion`, favoritos, calificaciones, cursores morosos/popularidad |
| `/pagos` | `pago_suscripcion` |
| `/empleados` | `departamento`, `empleado` |
| `/funciones` | `FN_CALCULAR_MONTO`, `FN_CONTENIDO_RECOMENDADO` |
| `/procedimientos` | `SP_REGISTRAR_USUARIO`, `SP_CAMBIAR_PLAN` |
| `/analytics` | Consultas parametrizadas, MVs, PIVOT/ROLLUP/CUBE |

## Ejemplo desde React

```javascript
const res = await fetch("http://localhost:8000/catalogo/contenidos?limite=20");
const peliculas = await res.json();
```

## Rama de trabajo

Desarrollo en rama `luis` / `sebas` según corresponda al equipo.
