from sqlalchemy import select

from ..entidades.models import OrdenDeMerito
from .base import BaseDAO


class OrdenDeMeritoDAO(BaseDAO):
    def insertar(self, orden_de_merito: OrdenDeMerito) -> None:
        self.db.add(orden_de_merito)
        self.db.flush()

    def obtener_por_evaluaciones(self, evaluaciones) -> list[OrdenDeMerito]:
        ids = [e.id_evaluacion for e in evaluaciones]
        stmt = select(OrdenDeMerito).where(OrdenDeMerito.evaluacion_id.in_(ids)).order_by(OrdenDeMerito.id_orden_merito.desc())
        return list(self.db.scalars(stmt))
