from datetime import datetime

from sqlalchemy.orm import Session

from ..dao import RegistroAuditoriaDAO
from ..entidades.models import RegistroAuditoria


class BaseGestor:
    def __init__(self, db: Session):
        self.db = db

    def auditar(self, accion: str, entidad: str, id_entidad, legajo: str | None) -> None:
        """Registro de auditoría: usuario, fecha y hora (bajas CU011/015/019/023/031 y ejecución del CU032)."""
        ahora = datetime.now()
        RegistroAuditoriaDAO(self.db).insertar(
            RegistroAuditoria(
                fecha=ahora.date(), hora=ahora.strftime("%H:%M:%S"), accion=accion, entidad_afectada=entidad,
                id_entidad_afectada=str(id_entidad), consultor_legajo=legajo,
            )
        )


def mensaje_duplicado(existente, codigo: str | None, nombre: str, entidad: str, campo_codigo="codigo",
                      campo_nombre="nombre", articulo="un") -> tuple[str, str]:
    """Arma el aviso del flujo 2.B (código y/o nombre ya existen). Devuelve (mensaje, campo con foco)."""
    partes, campo = [], campo_nombre
    if codigo and getattr(existente, campo_codigo) == codigo:
        partes.append(f"el código {codigo}")
        campo = campo_codigo
    if getattr(existente, campo_nombre) == nombre:
        partes.append(f"el nombre {nombre}")
    baja = " (dado de baja; no puede reutilizarse)" if getattr(existente, "eliminado", False) else ""
    return f"Ya existe {articulo} {entidad} con {' y '.join(partes)}{baja}.", campo
