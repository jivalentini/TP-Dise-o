from sqlalchemy import func, select

from ..entidades.models import Candidato, Cuestionario, Evaluacion
from ..pendiente import pendiente
from .base import BaseDAO


class CandidatoDAO(BaseDAO):
    def obtener_por_documento(self, tipo_documento: str, nro_documento: str) -> Candidato | None:
        return self.db.scalar(
            select(Candidato).where(Candidato.tipo_documento == tipo_documento, Candidato.nro_documento == nro_documento)
        )

    def obtener(self, nro_candidato: str) -> Candidato | None:
        return self.db.get(Candidato, nro_candidato)

    def contar_por_puesto(self, puesto) -> int:
        """CU028: candidatos con cuestionario en alguna evaluación del puesto."""
        stmt = (
            select(func.count(func.distinct(Cuestionario.candidato_nro_candidato)))
            .join(Evaluacion, Cuestionario.evaluacion_id == Evaluacion.id_evaluacion)
            .where(Evaluacion.puesto_codigo == puesto.codigo)
        )
        return self.db.scalar(stmt) or 0

    def buscar(self, criterios): pendiente("CU025 / CU002")
    def insertar(self, candidato): pendiente("CU003 / CU006")
    def actualizar(self, candidato): pendiente("CU004 / CU006")
    def eliminar(self, candidato): pendiente("CU005")
