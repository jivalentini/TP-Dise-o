from datetime import date, datetime, time

from sqlalchemy import exists, or_, select

from ..dto import PuestoCriteriosDTO
from ..entidades.estados import EstadoCuestionario
from ..entidades.models import CaracteristicaPuesto, Cuestionario, Evaluacion, Puesto
from .base import BaseDAO


class PuestoDAO(BaseDAO):
    def buscar(self, criterios: PuestoCriteriosDTO) -> list[Puesto]:
        """CU008 / CU027 / CU028: criterio "contiene"."""
        stmt = select(Puesto).where(Puesto.eliminado.is_(False))
        if criterios.codigo:
            stmt = stmt.where(Puesto.codigo.ilike(f"%{criterios.codigo}%"))
        if criterios.nombre_puesto:
            stmt = stmt.where(Puesto.nombre_puesto.ilike(f"%{criterios.nombre_puesto}%"))
        if criterios.empresa:
            stmt = stmt.where(Puesto.empresa.ilike(f"%{criterios.empresa}%"))
        return list(self.db.scalars(stmt.order_by(Puesto.nombre_puesto)))

    def buscar_con_completos(self, nombre: str | None, empresa: str | None,
                             desde: date | None, hasta: date | None) -> list[Puesto]:
        """CU007: funciones con candidatos evaluados (cuestionario Completo) en el rango de fecha de finalización."""
        cond = [
            Evaluacion.puesto_codigo == Puesto.codigo,
            Cuestionario.evaluacion_id == Evaluacion.id_evaluacion,
            Cuestionario.estado == EstadoCuestionario.COMPLETO,
        ]
        if desde:
            cond.append(Cuestionario.fecha_fin >= datetime.combine(desde, time.min))
        if hasta:
            cond.append(Cuestionario.fecha_fin <= datetime.combine(hasta, time.max))
        stmt = select(Puesto).where(Puesto.eliminado.is_(False), exists().where(*cond))
        if nombre:
            stmt = stmt.where(Puesto.nombre_puesto.ilike(f"%{nombre}%"))
        if empresa:
            stmt = stmt.where(Puesto.empresa.ilike(f"%{empresa}%"))
        return list(self.db.scalars(stmt.order_by(Puesto.nombre_puesto)))

    def obtener(self, codigo: str) -> Puesto | None:
        p = self.db.get(Puesto, codigo)
        return p if p and not p.eliminado else None

    def existe_codigo_o_nombre(self, codigo: str | None, nombre: str, excluir_codigo: str | None = None) -> Puesto | None:
        cond = [Puesto.nombre_puesto == nombre]
        if codigo:
            cond.append(Puesto.codigo == codigo)
        stmt = select(Puesto).where(or_(*cond))
        if excluir_codigo:
            stmt = stmt.where(Puesto.codigo != excluir_codigo)
        return self.db.scalars(stmt).first()

    def existe_en_uso(self, puesto: Puesto) -> bool:
        """CU011: tiene evaluaciones asociadas."""
        return bool(self.db.scalar(select(exists().where(Evaluacion.puesto_codigo == puesto.codigo))))

    def tiene_cuestionarios(self, puesto: Puesto) -> bool:
        """CU010 2.C: ya existen cuestionarios generados para el puesto."""
        return bool(
            self.db.scalar(
                select(
                    exists().where(Evaluacion.puesto_codigo == puesto.codigo, Cuestionario.evaluacion_id == Evaluacion.id_evaluacion)
                )
            )
        )

    def insertar(self, puesto: Puesto) -> None:
        self.db.add(puesto)
        self.db.flush()

    def actualizar(self, puesto: Puesto) -> None:
        self.db.flush()

    def eliminar(self, puesto: Puesto) -> None:
        puesto.eliminado = True  # baja lógica
        self.db.flush()

    def obtener_caracteristicas(self, puesto: Puesto) -> list[CaracteristicaPuesto]:
        """CU027 / CU028: ponderación mínima requerida por competencia."""
        stmt = select(CaracteristicaPuesto).where(CaracteristicaPuesto.puesto_codigo == puesto.codigo)
        return list(self.db.scalars(stmt))
