from sqlalchemy import or_, select

from ..dto import PreguntaCriteriosDTO
from ..entidades.models import Competencia, Factor, Pregunta
from .base import BaseDAO


class PreguntaDAO(BaseDAO):
    def buscar(self, criterios: PreguntaCriteriosDTO) -> list[Pregunta]:
        """CU020: criterio "contiene" sobre competencia, factor y nombre de la pregunta."""
        stmt = (
            select(Pregunta)
            .join(Factor)
            .join(Competencia)
            .where(Pregunta.eliminado.is_(False), Factor.eliminado.is_(False), Competencia.eliminado.is_(False))
        )
        if criterios.nombre_competencia:
            stmt = stmt.where(Competencia.nombre.ilike(f"%{criterios.nombre_competencia}%"))
        if criterios.nombre_factor:
            stmt = stmt.where(Factor.nombre.ilike(f"%{criterios.nombre_factor}%"))
        if criterios.nombre_pregunta:
            stmt = stmt.where(Pregunta.nombre_pregunta.ilike(f"%{criterios.nombre_pregunta}%"))
        return list(self.db.scalars(stmt.order_by(Competencia.nombre, Factor.nro_orden, Pregunta.nombre_pregunta)))

    def buscar_por_factor(self, codigo_factor: str) -> list[Pregunta]:
        """CU026 paso 3: preguntas activas del factor."""
        stmt = select(Pregunta).where(Pregunta.factor_codigo == codigo_factor, Pregunta.eliminado.is_(False))
        return list(self.db.scalars(stmt.order_by(Pregunta.id_pregunta)))

    def obtener(self, id_pregunta: int) -> Pregunta | None:
        p = self.db.get(Pregunta, id_pregunta)
        return p if p and not p.eliminado else None

    def existe_pregunta(self, nombre: str, enunciado: str, competencia: str, factor: str,
                        excluir_id: int | None = None) -> Pregunta | None:
        """CU021/022 2.C: ya existe (por nombre o por enunciado) para esa competencia y factor."""
        stmt = (
            select(Pregunta)
            .join(Factor)
            .where(
                Pregunta.eliminado.is_(False),
                Pregunta.factor_codigo == factor,
                Factor.competencia_codigo == competencia,
                or_(Pregunta.nombre_pregunta == nombre, Pregunta.enunciado == enunciado),
            )
        )
        if excluir_id is not None:
            stmt = stmt.where(Pregunta.id_pregunta != excluir_id)
        return self.db.scalars(stmt).first()

    def insertar(self, pregunta: Pregunta) -> None:
        self.db.add(pregunta)
        self.db.flush()

    def actualizar(self, pregunta: Pregunta) -> None:
        self.db.flush()

    def eliminar(self, pregunta: Pregunta) -> None:
        pregunta.eliminado = True  # baja lógica
        self.db.flush()
