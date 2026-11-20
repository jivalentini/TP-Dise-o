"""CU016 a CU019 – Factores."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..dto import FactorCriteriosDTO, FactorDTO, MensajeDTO, PuedeEliminarDTO
from ..gestores.factores import GestorFactores, a_dto
from ..infraestructura.database import get_db
from .deps import Sesion, consultor

router = APIRouter(prefix="/api/factores", tags=["CU016-019 Factores"], dependencies=[Depends(consultor)])


@router.get("", response_model=list[FactorDTO])
def buscar(nombre_competencia: str | None = None, nombre_factor: str | None = None, codigo_competencia: str | None = None,
           db: Session = Depends(get_db)):
    criterios = FactorCriteriosDTO(nombre_competencia=nombre_competencia, nombre_factor=nombre_factor)
    return GestorFactores(db).buscar_factor(criterios, codigo_competencia)


@router.get("/ordenes/{codigo_competencia}")
def ordenes(codigo_competencia: str, db: Session = Depends(get_db)):
    """Nros de orden ocupados en la competencia (para elegir el orden del factor)."""
    return GestorFactores(db).ordenes_de_competencia(codigo_competencia)


@router.get("/{codigo}", response_model=FactorDTO)
def obtener(codigo: str, db: Session = Depends(get_db)):
    return a_dto(GestorFactores(db).obtener(codigo))


@router.post("", response_model=FactorDTO, status_code=201)
def dar_alta(datos: FactorDTO, db: Session = Depends(get_db)):
    return GestorFactores(db).dar_alta_factor(datos)


@router.put("/{codigo}", response_model=FactorDTO)
def modificar(codigo: str, datos: FactorDTO, db: Session = Depends(get_db)):
    return GestorFactores(db).modificar_factor(codigo, datos)


@router.get("/{codigo}/puede-eliminar", response_model=PuedeEliminarDTO)
def puede_eliminar(codigo: str, db: Session = Depends(get_db)):
    return PuedeEliminarDTO(puede=True, mensaje=GestorFactores(db).mensaje_baja(codigo))


@router.delete("/{codigo}", response_model=MensajeDTO)
def dar_baja(codigo: str, db: Session = Depends(get_db), sesion: Sesion = Depends(consultor)):
    return MensajeDTO(mensaje=GestorFactores(db).dar_baja_factor(codigo, sesion.sub))
