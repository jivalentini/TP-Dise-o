"""Dependencias comunes de la capa de interfaz: sesión del usuario según su perfil (CU001)."""
from dataclasses import dataclass

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..infraestructura.security import decode_token

_bearer = HTTPBearer(auto_error=False)


@dataclass
class Sesion:
    sub: str  # legajo del consultor o nro de candidato
    perfil: str
    cuestionario_id: int | None = None


def _sesion(cred: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> Sesion:
    datos = decode_token(cred.credentials) if cred else None
    if not datos:
        raise HTTPException(status_code=401, detail="La sesión expiró. Vuelva a ingresar.")
    return Sesion(sub=datos["sub"], perfil=datos["perfil"], cuestionario_id=datos.get("cuestionario_id"))


def consultor(sesion: Sesion = Depends(_sesion)) -> Sesion:
    if sesion.perfil != "CONSULTOR":
        raise HTTPException(status_code=403, detail="Opción disponible solo para el perfil Consultor.")
    return sesion


def candidato(sesion: Sesion = Depends(_sesion)) -> Sesion:
    if sesion.perfil != "CANDIDATO" or sesion.cuestionario_id is None:
        raise HTTPException(status_code=403, detail="Opción disponible solo para candidatos.")
    return sesion
