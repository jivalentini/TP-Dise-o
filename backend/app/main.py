import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .entidades import models  # noqa: F401  (registra las tablas)
from .gestores.excepciones import DatosInvalidos, ErrorNegocio
from .gestores.proceso_batch import ProcesoBatchFinalizacionCuestionarios
from .infraestructura.database import Base, engine
from .interfaz import (auth, competencias, cuestionario, factores, opciones_respuesta, preguntas, puestos,
                       reportes)

log = logging.getLogger("uvicorn.error")


async def _batch_periodico():
    """CU032: el actor Sistema ejecuta periódicamente la finalización de cuestionarios."""
    while True:
        try:
            r = await asyncio.to_thread(ProcesoBatchFinalizacionCuestionarios().ejecutar)
            log.info("CU032 Finalizar cuestionarios: %s", r)
        except Exception:  # noqa: BLE001 – el proceso periódico no debe tirar abajo la aplicación
            log.exception("CU032: error en la ejecución del proceso batch")
        await asyncio.sleep(settings.batch_intervalo_minutos * 60)


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)  # en desarrollo; luego migrar a Alembic
    tarea = asyncio.create_task(_batch_periodico()) if settings.batch_intervalo_minutos > 0 else None
    yield
    if tarea:
        tarea.cancel()


app = FastAPI(title="Capit@l Humano – Evaluaciones", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Nombre-Archivo"],
)


@app.exception_handler(ErrorNegocio)
async def error_negocio(_: Request, e: ErrorNegocio):
    cuerpo = {"detail": e.mensaje, "campo": e.campo}
    if isinstance(e, DatosInvalidos):
        cuerpo.update(errores=e.errores, campos=e.campos)
    return JSONResponse(status_code=e.status_code, content=cuerpo)


@app.exception_handler(RequestValidationError)
async def datos_mal_formados(_: Request, e: RequestValidationError):
    errores = [f"{'.'.join(str(x) for x in err['loc'][1:])}: valor inválido" for err in e.errors()]
    return JSONResponse(status_code=422, content={"detail": "Hay datos con formato inválido.", "errores": errores})


for r in (auth, puestos, competencias, factores, preguntas, opciones_respuesta, cuestionario, reportes):
    app.include_router(r.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
