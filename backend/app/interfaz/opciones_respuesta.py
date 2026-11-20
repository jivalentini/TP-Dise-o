"""CU024, CU029 a CU031 – Opciones de respuesta."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..dto import MensajeDTO, OpcionRespuestaDTO, PuedeEliminarDTO
from ..gestores.opciones_respuesta import GestorOpcionesRespuesta, a_dto
from ..infraestructura.database import get_db
from .deps import Sesion, consultor

router = APIRouter(prefix="/api/opciones-respuesta", tags=["CU024/029-031 Opciones de respuesta"], dependencies=[Depends(consultor)])


@router.get("", response_model=list[OpcionRespuestaDTO])
def buscar(nombre: str | None = None, db: Session = Depends(get_db)):
    return GestorOpcionesRespuesta(db).buscar_opcion(nombre)


@router.get("/{nombre}", response_model=OpcionRespuestaDTO)
def obtener(nombre: str, db: Session = Depends(get_db)):
    return a_dto(GestorOpcionesRespuesta(db).obtener(nombre))


@router.post("", response_model=OpcionRespuestaDTO, status_code=201)
def dar_alta(datos: OpcionRespuestaDTO, db: Session = Depends(get_db)):
    return GestorOpcionesRespuesta(db).dar_alta_opcion(datos)


@router.put("/{nombre}", response_model=OpcionRespuestaDTO)
def modificar(nombre: str, datos: OpcionRespuestaDTO, db: Session = Depends(get_db)):
    return GestorOpcionesRespuesta(db).modificar_opcion(nombre, datos)


@router.get("/{nombre}/puede-eliminar", response_model=PuedeEliminarDTO)
def puede_eliminar(nombre: str, db: Session = Depends(get_db)):
    return GestorOpcionesRespuesta(db).puede_eliminar(nombre)


@router.delete("/{nombre}", response_model=MensajeDTO)
def dar_baja(nombre: str, db: Session = Depends(get_db), sesion: Sesion = Depends(consultor)):
    return MensajeDTO(mensaje=GestorOpcionesRespuesta(db).dar_baja_opcion(nombre, sesion.sub))
