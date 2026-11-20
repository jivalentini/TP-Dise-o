from sqlalchemy import func, or_, select

from ..dto import FactorCriteriosDTO
from ..entidades.models import Competencia, Factor, Pregunta
from .base import BaseDAO


class FactorDAO(BaseDAO):
    def buscar(self, criterios: FactorCriteriosDTO, codigo_competencia: str | None = None) -> list[Factor]:
        """CU016 (criterio "contiene", ordenado por nombre) / CU021 (factores de una competencia)."""
        stmt = (
            select(Factor)
            .join(Competencia)
            .where(Factor.eliminado.is_(False), Competencia.eliminado.is_(False))
        )
        if criterios.nombre_competencia:
            stmt = stmt.where(Competencia.nombre.ilike(f"%{criterios.nombre_competencia}%"))
        if criterios.nombre_factor:
            stmt = stmt.where(Factor.nombre.ilike(f"%{criterios.nombre_factor}%"))
        if codigo_competencia:
            stmt = stmt.where(Factor.competencia_codigo == codigo_competencia)
            return list(self.db.scalars(stmt.order_by(Factor.nro_orden)))
        return list(self.db.scalars(stmt.order_by(Factor.nombre)))

    def obtener(self, codigo: str) -> Factor | None:
        f = self.db.get(Factor, codigo)
        return f if f and not f.eliminado else None

    def existe_codigo_o_nombre(self, codigo: str | None, nombre: str, excluir_codigo: str | None = None) -> Factor | None:
        cond = [Factor.nombre == nombre]
        if codigo:
            cond.append(Factor.codigo == codigo)
        stmt = select(Factor).where(or_(*cond))
        if excluir_codigo:
            stmt = stmt.where(Factor.codigo != excluir_codigo)
        return self.db.scalars(stmt).first()

    def obtener_por_orden(self, codigo_competencia: str, nro_orden: int) -> Factor | None:
        """El par (competencia, nro_orden) es único en la BD, incluso para factores dados de baja."""
        return self.db.scalar(
            select(Factor).where(Factor.competencia_codigo == codigo_competencia, Factor.nro_orden == nro_orden)
        )

    def ordenes_usados(self, codigo_competencia: str) -> list[Factor]:
        return list(self.db.scalars(select(Factor).where(Factor.competencia_codigo == codigo_competencia).order_by(Factor.nro_orden)))

    def factores_evaluables(self, codigo_competencia: str) -> list[Factor]:
        """Factores no eliminados con al menos 2 preguntas activas (CU026 paso 3 / CU025 9.A)."""
        cant = (
            select(func.count(Pregunta.id_pregunta))
            .where(Pregunta.factor_codigo == Factor.codigo, Pregunta.eliminado.is_(False))
            .scalar_subquery()
        )
        stmt = select(Factor).where(Factor.competencia_codigo == codigo_competencia, Factor.eliminado.is_(False), cant >= 2)
        return list(self.db.scalars(stmt.order_by(Factor.nro_orden)))

    def insertar(self, factor: Factor) -> None:
        self.db.add(factor)
        self.db.flush()

    def actualizar(self, factor: Factor) -> None:
        self.db.flush()

    def eliminar(self, factor: Factor) -> None:
        factor.eliminado = True  # baja lógica
        self.db.flush()
