"""CU026 – Completar cuestionario (perfil Candidato)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..dto import BloqueRespuestasDTO, EstadoCuestionarioDTO
from ..gestores.evaluaciones import GestorEvaluaciones
from ..infraestructura.database import get_db
from .deps import Sesion, candidato

router = APIRouter(prefix="/api/cuestionario", tags=["CU026 Completar cuestionario"])


@router.post("/ingresar", response_model=EstadoCuestionarioDTO)
def ingresar(db: Session = Depends(get_db), sesion: Sesion = Depends(candidato)):
    """Se invoca una vez por ingreso (después del CU001): cuenta el acceso y decide qué pantalla mostrar."""
    return GestorEvaluaciones(db).obtener_cuestionario_para_completar(sesion.cuestionario_id, registrar_acceso=True)


@router.get("/estado", response_model=EstadoCuestionarioDTO)
def estado(db: Session = Depends(get_db), sesion: Sesion = Depends(candidato)):
    """Recupera la pantalla actual sin contar un nuevo acceso (p. ej. al recargar la página)."""
    return GestorEvaluaciones(db).obtener_cuestionario_para_completar(sesion.cuestionario_id)


@router.post("/comenzar", response_model=EstadoCuestionarioDTO)
def comenzar(db: Session = Depends(get_db), sesion: Sesion = Depends(candidato)):
    """El candidato aceptó las instrucciones: se arma el cuestionario y pasa a En Proceso."""
    return GestorEvaluaciones(db).armar_cuestionario(sesion.cuestionario_id)


@router.post("/bloque", response_model=EstadoCuestionarioDTO)
def responder_bloque(bloque: BloqueRespuestasDTO, db: Session = Depends(get_db), sesion: Sesion = Depends(candidato)):
    return GestorEvaluaciones(db).registrar_respuesta_bloque(sesion.cuestionario_id, bloque)
