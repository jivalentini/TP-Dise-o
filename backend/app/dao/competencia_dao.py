from sqlalchemy import exists, or_, select

from ..entidades.models import CaracteristicaPuesto, Competencia, Factor, Puesto
from .base import BaseDAO


class CompetenciaDAO(BaseDAO):
    def buscar(self, nombre: str | None) -> list[Competencia]:
        """CU012: criterio "contiene"; sin nombre devuelve todas."""
        stmt = select(Competencia).where(Competencia.eliminado.is_(False))
        if nombre:
            stmt = stmt.where(Competencia.nombre.ilike(f"%{nombre}%"))
        return list(self.db.scalars(stmt.order_by(Competencia.nombre)))

    def obtener(self, codigo: str) -> Competencia | None:
        c = self.db.get(Competencia, codigo)
        return c if c and not c.eliminado else None

    def existe_codigo_o_nombre(self, codigo: str | None, nombre: str, excluir_codigo: str | None = None) -> Competencia | None:
        """Incluye las dadas de baja: el código y el nombre son únicos en la BD."""
        cond = [Competencia.nombre == nombre]
        if codigo:
            cond.append(Competencia.codigo == codigo)
        stmt = select(Competencia).where(or_(*cond))
        if excluir_codigo:
            stmt = stmt.where(Competencia.codigo != excluir_codigo)
        return self.db.scalars(stmt).first()

    def esta_en_uso(self, competencia: Competencia) -> bool:
        """CU015: tiene factores asociados o está asociada a un puesto (no eliminados)."""
        tiene_factores = exists().where(Factor.competencia_codigo == competencia.codigo, Factor.eliminado.is_(False))
        en_puesto = (
            exists()
            .where(CaracteristicaPuesto.competencia_codigo == competencia.codigo)
            .where(CaracteristicaPuesto.puesto_codigo == Puesto.codigo, Puesto.eliminado.is_(False))
        )
        return bool(self.db.scalar(select(tiene_factores | en_puesto)))

    def insertar(self, competencia: Competencia) -> None:
        self.db.add(competencia)
        self.db.flush()

    def actualizar(self, competencia: Competencia) -> None:
        self.db.flush()

    def eliminar(self, competencia: Competencia) -> None:
        competencia.eliminado = True  # baja lógica
        self.db.flush()
