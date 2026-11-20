from sqlalchemy import select

from ..entidades.models import Evaluacion
from ..pendiente import pendiente
from .base import BaseDAO


class EvaluacionDAO(BaseDAO):
    def insertar(self, evaluacion): pendiente("CU025")

    def buscar_por_puesto(self, puesto) -> list[Evaluacion]:
        """CU028 paso 6."""
        stmt = select(Evaluacion).where(Evaluacion.puesto_codigo == puesto.codigo)
        return list(self.db.scalars(stmt.order_by(Evaluacion.fecha_creacion.desc(), Evaluacion.id_evaluacion.desc())))

    def obtener(self, id_evaluacion: int) -> Evaluacion | None:
        return self.db.get(Evaluacion, id_evaluacion)
