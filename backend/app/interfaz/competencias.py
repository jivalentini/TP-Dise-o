"""CU012 a CU015 – Competencias."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..dto import CompetenciaDTO, MensajeDTO, PuedeEliminarDTO
from ..gestores.competencias import GestorCompetencias, a_dto
from ..infraestructura.database import get_db
from .deps import Sesion, consultor

router = APIRouter(prefix="/api/competencias", tags=["CU012-015 Competencias"], dependencies=[Depends(consultor)])


@router.get("", response_model=list[CompetenciaDTO])
def buscar(nombre: str | None = None, db: Session = Depends(get_db)):
    return GestorCompetencias(db).buscar_competencia(nombre)


@router.get("/{codigo}", response_model=CompetenciaDTO)
def obtener(codigo: str, db: Session = Depends(get_db)):
    return a_dto(GestorCompetencias(db).obtener(codigo))


@router.post("", response_model=CompetenciaDTO, status_code=201)
def dar_alta(datos: CompetenciaDTO, db: Session = Depends(get_db)):
    return GestorCompetencias(db).dar_alta_competencia(datos)


@router.put("/{codigo}", response_model=CompetenciaDTO)
def modificar(codigo: str, datos: CompetenciaDTO, db: Session = Depends(get_db)):
    return GestorCompetencias(db).modificar_competencia(codigo, datos)


@router.get("/{codigo}/puede-eliminar", response_model=PuedeEliminarDTO)
def puede_eliminar(codigo: str, db: Session = Depends(get_db)):
    return GestorCompetencias(db).puede_eliminar(codigo)


@router.delete("/{codigo}", response_model=MensajeDTO)
def dar_baja(codigo: str, db: Session = Depends(get_db), sesion: Sesion = Depends(consultor)):
    return MensajeDTO(mensaje=GestorCompetencias(db).dar_baja_competencia(codigo, sesion.sub))
