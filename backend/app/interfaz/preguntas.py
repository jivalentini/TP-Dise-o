"""CU020 a CU023 – Preguntas, CU033 – Generar pregunta con IA."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..dto import GenerarPreguntaIADTO, MensajeDTO, PreguntaCriteriosDTO, PreguntaDTO, PuedeEliminarDTO
from ..gestores.preguntas import GestorPreguntas
from ..infraestructura.database import get_db
from .deps import Sesion, consultor

router = APIRouter(prefix="/api/preguntas", tags=["CU020-023 / CU033 Preguntas"], dependencies=[Depends(consultor)])


@router.get("", response_model=list[PreguntaDTO])
def buscar(nombre_competencia: str | None = None, nombre_factor: str | None = None, nombre_pregunta: str | None = None,
           db: Session = Depends(get_db)):
    criterios = PreguntaCriteriosDTO(nombre_competencia=nombre_competencia, nombre_factor=nombre_factor, nombre_pregunta=nombre_pregunta)
    return GestorPreguntas(db).buscar_pregunta(criterios)


@router.post("/generar-ia", response_model=PreguntaDTO)
def generar_con_ia(datos: GenerarPreguntaIADTO, db: Session = Depends(get_db)):
    return GestorPreguntas(db).generar_pregunta_ia(datos)


@router.get("/{id_pregunta}", response_model=PreguntaDTO)
def obtener(id_pregunta: int, db: Session = Depends(get_db)):
    return GestorPreguntas(db).obtener_dto(id_pregunta)


@router.post("", response_model=PreguntaDTO, status_code=201)
def dar_alta(datos: PreguntaDTO, db: Session = Depends(get_db)):
    return GestorPreguntas(db).dar_alta_pregunta(datos)


@router.put("/{id_pregunta}", response_model=PreguntaDTO)
def modificar(id_pregunta: int, datos: PreguntaDTO, db: Session = Depends(get_db)):
    return GestorPreguntas(db).modificar_pregunta(id_pregunta, datos)


@router.get("/{id_pregunta}/puede-eliminar", response_model=PuedeEliminarDTO)
def puede_eliminar(id_pregunta: int, db: Session = Depends(get_db)):
    return PuedeEliminarDTO(puede=True, mensaje=GestorPreguntas(db).mensaje_baja(id_pregunta))


@router.delete("/{id_pregunta}", response_model=MensajeDTO)
def dar_baja(id_pregunta: int, db: Session = Depends(get_db), sesion: Sesion = Depends(consultor)):
    return MensajeDTO(mensaje=GestorPreguntas(db).dar_baja_pregunta(id_pregunta, sesion.sub))
