"""CU008 a CU011 – Puestos o funciones (alta con GenAI)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..dto import GenerarPuestoIADTO, MensajeDTO, PuedeEliminarDTO, PuestoCriteriosDTO, PuestoDTO
from ..gestores.puestos import GestorPuestos
from ..infraestructura.database import get_db
from .deps import Sesion, consultor

router = APIRouter(prefix="/api/puestos", tags=["CU008-011 Puestos"], dependencies=[Depends(consultor)])


@router.get("", response_model=list[PuestoDTO])
def buscar(codigo: str | None = None, nombre_puesto: str | None = None, empresa: str | None = None,
           db: Session = Depends(get_db)):
    return GestorPuestos(db).buscar_puesto(PuestoCriteriosDTO(codigo=codigo, nombre_puesto=nombre_puesto, empresa=empresa))


@router.post("/generar-ia", response_model=PuestoDTO)
def generar_con_ia(datos: GenerarPuestoIADTO, db: Session = Depends(get_db)):
    return GestorPuestos(db).generar_puesto_ia(datos)


@router.get("/{codigo}", response_model=PuestoDTO)
def obtener(codigo: str, db: Session = Depends(get_db)):
    return GestorPuestos(db).obtener_dto(codigo)


@router.post("", response_model=PuestoDTO, status_code=201)
def dar_alta(datos: PuestoDTO, db: Session = Depends(get_db)):
    return GestorPuestos(db).dar_alta_puesto(datos)


@router.put("/{codigo}", response_model=PuestoDTO)
def modificar(codigo: str, datos: PuestoDTO, db: Session = Depends(get_db)):
    return GestorPuestos(db).modificar_puesto(codigo, datos)


@router.get("/{codigo}/puede-eliminar", response_model=PuedeEliminarDTO)
def puede_eliminar(codigo: str, db: Session = Depends(get_db)):
    return GestorPuestos(db).puede_eliminar(codigo)


@router.delete("/{codigo}", response_model=MensajeDTO)
def dar_baja(codigo: str, db: Session = Depends(get_db), sesion: Sesion = Depends(consultor)):
    return MensajeDTO(mensaje=GestorPuestos(db).dar_baja_puesto(codigo, sesion.sub))
