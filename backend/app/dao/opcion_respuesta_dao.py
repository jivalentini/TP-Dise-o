from sqlalchemy import exists, select

from ..entidades.models import OpcionRespuesta, Pregunta
from .base import BaseDAO


class OpcionRespuestaDAO(BaseDAO):
    def buscar(self, nombre: str | None) -> list[OpcionRespuesta]:
        """CU024: criterio "contiene"; sin nombre devuelve todas."""
        stmt = select(OpcionRespuesta).where(OpcionRespuesta.eliminado.is_(False))
        if nombre:
            stmt = stmt.where(OpcionRespuesta.nombre.ilike(f"%{nombre}%"))
        return list(self.db.scalars(stmt.order_by(OpcionRespuesta.nombre)))

    def obtener(self, nombre: str) -> OpcionRespuesta | None:
        o = self.db.get(OpcionRespuesta, nombre)
        return o if o and not o.eliminado else None

    def existe(self, nombre: str) -> bool:
        """Incluye las dadas de baja (el nombre es la PK)."""
        return self.db.get(OpcionRespuesta, nombre) is not None

    def esta_en_uso(self, opcion: OpcionRespuesta) -> bool:
        """CU031: tiene preguntas (activas) asociadas."""
        return bool(
            self.db.scalar(
                select(exists().where(Pregunta.opcion_respuesta_nombre == opcion.nombre, Pregunta.eliminado.is_(False)))
            )
        )

    def insertar(self, opcion: OpcionRespuesta) -> None:
        self.db.add(opcion)
        self.db.flush()

    def actualizar(self, opcion: OpcionRespuesta) -> None:
        self.db.flush()

    def eliminar(self, opcion: OpcionRespuesta) -> None:
        opcion.eliminado = True  # baja lógica
        self.db.flush()
