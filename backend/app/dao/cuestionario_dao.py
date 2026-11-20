import hmac
from datetime import date, datetime, time, timedelta

from sqlalchemy import exists, func, select

from ..dto import ResultadoExportadoDTO
from ..entidades.estados import EstadoCuestionario
from ..entidades.models import (Candidato, Competencia, Cuestionario, Evaluacion, PreguntaCuestionario, Puesto,
                                PuntajeCompetenciaLogrado, PuntajeFactorLogrado, RespuestaCandidato)
from ..pendiente import pendiente
from .base import BaseDAO


class CuestionarioDAO(BaseDAO):
    # ---- CU001
    def obtener_por_clave(self, tipo_documento: str, nro_documento: str, clave_ingreso: str) -> Cuestionario | None:
        """Cuestionario activo o en proceso del candidato cuya clave coincide (CU001 paso 3.A.2)."""
        stmt = (
            select(Cuestionario)
            .join(Candidato, Cuestionario.candidato_nro_candidato == Candidato.nro_candidato)
            .where(
                Candidato.tipo_documento == tipo_documento,
                Candidato.nro_documento == nro_documento,
                Candidato.eliminado.is_(False),
                Cuestionario.estado.in_(EstadoCuestionario.ABIERTOS),
            )
        )
        for c in self.db.scalars(stmt):
            if hmac.compare_digest(c.clave_ingreso.encode(), clave_ingreso.encode()):
                return c
        return None

    def obtener(self, id_cuestionario: int) -> Cuestionario | None:
        return self.db.get(Cuestionario, id_cuestionario)

    def obtener_activo_o_en_proceso(self, candidato) -> Cuestionario | None:
        stmt = select(Cuestionario).where(
            Cuestionario.candidato_nro_candidato == candidato.nro_candidato,
            Cuestionario.estado.in_(EstadoCuestionario.ABIERTOS),
        )
        return self.db.scalars(stmt).first()

    # ---- CU026 – Completar cuestionario
    def actualizar_estado(self, cuestionario: Cuestionario, nuevo_estado: str, fecha: datetime | None = None) -> None:
        """Al pasar a un estado final (Completo / Incompleto / Sin Contestar) se registra la fecha y hora del cambio."""
        cuestionario.estado = nuevo_estado
        if nuevo_estado not in EstadoCuestionario.ABIERTOS:
            cuestionario.fecha_fin = fecha or datetime.now()
        self.db.flush()

    def guardar_estructura(self, cuestionario: Cuestionario, bloques: list[list[int]], fecha_inicio: datetime) -> None:
        """Asocia al cuestionario las preguntas elegidas, agrupadas por bloque, y registra el comienzo."""
        for nro, ids in enumerate(bloques, start=1):
            for id_pregunta in ids:
                self.db.add(PreguntaCuestionario(id_cuestionario=cuestionario.id_cuestionario, id_pregunta=id_pregunta, numero_bloque=nro))
        cuestionario.fecha_inicio = fecha_inicio
        cuestionario.estado = EstadoCuestionario.EN_PROCESO
        self.db.flush()
        self.db.refresh(cuestionario)

    def obtener_bloque_pendiente(self, cuestionario: Cuestionario) -> int | None:
        """Primer bloque con preguntas sin responder (None = todos respondidos)."""
        respondida = exists().where(
            RespuestaCandidato.id_cuestionario == PreguntaCuestionario.id_cuestionario,
            RespuestaCandidato.id_pregunta == PreguntaCuestionario.id_pregunta,
        )
        stmt = select(func.min(PreguntaCuestionario.numero_bloque)).where(
            PreguntaCuestionario.id_cuestionario == cuestionario.id_cuestionario, ~respondida
        )
        return self.db.scalar(stmt)

    def total_bloques(self, cuestionario: Cuestionario) -> int:
        stmt = select(func.max(PreguntaCuestionario.numero_bloque)).where(
            PreguntaCuestionario.id_cuestionario == cuestionario.id_cuestionario
        )
        return self.db.scalar(stmt) or 0

    def preguntas_del_bloque(self, cuestionario: Cuestionario, nro_bloque: int) -> list[PreguntaCuestionario]:
        stmt = select(PreguntaCuestionario).where(
            PreguntaCuestionario.id_cuestionario == cuestionario.id_cuestionario,
            PreguntaCuestionario.numero_bloque == nro_bloque,
        )
        return list(self.db.scalars(stmt))

    def guardar_bloque_respuestas(self, cuestionario: Cuestionario, respuestas: list[RespuestaCandidato]) -> None:
        for r in respuestas:
            self.db.add(r)
        self.db.flush()
        self.db.expire(cuestionario, ["respuestas"])

    def guardar_resultados(self, cuestionario: Cuestionario, puntajes_factor: dict[str, float],
                           puntajes_competencia: dict[str, float]) -> None:
        hoy = date.today()
        for codigo, puntaje in puntajes_factor.items():
            self.db.add(PuntajeFactorLogrado(id_cuestionario=cuestionario.id_cuestionario, factor_codigo=codigo,
                                             puntaje_obtenido=puntaje, fecha_evaluacion=hoy))
        for codigo, puntaje in puntajes_competencia.items():
            self.db.add(PuntajeCompetenciaLogrado(id_cuestionario=cuestionario.id_cuestionario, competencia_codigo=codigo,
                                                  puntaje_obtenido=puntaje, fecha_evaluacion=hoy))
        self.db.flush()

    # ---- CU032 – Finalizar cuestionarios
    def buscar_vencidos(self, tiempo_maximo_cuestionario: int, ahora: datetime) -> list[Cuestionario]:
        """En Proceso con el tiempo máximo para completarlo superado (desde el primer ingreso)."""
        limite = ahora - timedelta(minutes=tiempo_maximo_cuestionario)
        stmt = select(Cuestionario).where(
            Cuestionario.estado == EstadoCuestionario.EN_PROCESO, Cuestionario.fecha_inicio < limite
        )
        return list(self.db.scalars(stmt))

    def buscar_activos_vencidos(self, tiempo_maximo_activo: int, ahora: datetime) -> list[Cuestionario]:
        """Activos (nunca comenzados) que superaron el tiempo máximo permitido en ese estado."""
        limite = ahora - timedelta(minutes=tiempo_maximo_activo)
        stmt = select(Cuestionario).where(
            Cuestionario.estado == EstadoCuestionario.ACTIVO, Cuestionario.fecha_creacion < limite
        )
        return list(self.db.scalars(stmt))

    # ---- CU007 / CU027 – candidatos evaluados (cuestionario Completo) en un puesto
    def buscar_completos_por_puesto(self, puesto, desde: date | None = None, hasta: date | None = None) -> list[Cuestionario]:
        stmt = (
            select(Cuestionario)
            .join(Evaluacion, Cuestionario.evaluacion_id == Evaluacion.id_evaluacion)
            .join(Candidato, Cuestionario.candidato_nro_candidato == Candidato.nro_candidato)
            .where(Evaluacion.puesto_codigo == puesto.codigo, Cuestionario.estado == EstadoCuestionario.COMPLETO)
        )
        if desde:
            stmt = stmt.where(Cuestionario.fecha_fin >= datetime.combine(desde, time.min))
        if hasta:
            stmt = stmt.where(Cuestionario.fecha_fin <= datetime.combine(hasta, time.max))
        return list(self.db.scalars(stmt.order_by(Candidato.apellido, Candidato.nombre, Cuestionario.fecha_fin.desc())))

    def buscar_resultados(self, codigo_puesto: str, desde: date | None = None, hasta: date | None = None) -> list[ResultadoExportadoDTO]:
        """CU007: una fila por candidato y competencia evaluada."""
        stmt = (
            select(Candidato, Competencia.codigo, PuntajeCompetenciaLogrado.puntaje_obtenido, Puesto, Cuestionario.fecha_fin)
            .select_from(PuntajeCompetenciaLogrado)
            .join(Cuestionario, PuntajeCompetenciaLogrado.id_cuestionario == Cuestionario.id_cuestionario)
            .join(Competencia, PuntajeCompetenciaLogrado.competencia_codigo == Competencia.codigo)
            .join(Evaluacion, Cuestionario.evaluacion_id == Evaluacion.id_evaluacion)
            .join(Puesto, Evaluacion.puesto_codigo == Puesto.codigo)
            .join(Candidato, Cuestionario.candidato_nro_candidato == Candidato.nro_candidato)
            .where(Puesto.codigo == codigo_puesto, Cuestionario.estado == EstadoCuestionario.COMPLETO)
        )
        if desde:
            stmt = stmt.where(Cuestionario.fecha_fin >= datetime.combine(desde, time.min))
        if hasta:
            stmt = stmt.where(Cuestionario.fecha_fin <= datetime.combine(hasta, time.max))
        stmt = stmt.order_by(Candidato.apellido, Candidato.nombre, Cuestionario.fecha_fin, Competencia.codigo)
        return [
            ResultadoExportadoDTO(
                nro_candidato=c.nro_candidato, apellido=c.apellido, nombre=c.nombre, tipo_documento=c.tipo_documento,
                nro_documento=c.nro_documento, codigo_competencia=cod, resultado=puntaje, nombre_puesto=p.nombre_puesto,
                codigo_puesto=p.codigo, fecha_finalizacion_cuestionario=fin,
            )
            for c, cod, puntaje, p, fin in self.db.execute(stmt)
        ]

    # ---- CU028 – Orden de mérito
    def contar_completos_por_puesto(self, puesto) -> int:
        stmt = (
            select(func.count(Cuestionario.id_cuestionario))
            .join(Evaluacion, Cuestionario.evaluacion_id == Evaluacion.id_evaluacion)
            .where(Evaluacion.puesto_codigo == puesto.codigo, Cuestionario.estado == EstadoCuestionario.COMPLETO)
        )
        return self.db.scalar(stmt) or 0

    def _por_evaluaciones(self, evaluaciones, *cond):
        ids = [e.id_evaluacion for e in evaluaciones]
        stmt = select(Cuestionario).where(Cuestionario.evaluacion_id.in_(ids), *cond)
        return list(self.db.scalars(stmt))

    def buscar_completos_por_evaluaciones(self, evaluaciones) -> list[Cuestionario]:
        return self._por_evaluaciones(evaluaciones, Cuestionario.estado == EstadoCuestionario.COMPLETO)

    def buscar_no_completos_por_evaluaciones(self, evaluaciones) -> list[Cuestionario]:
        return self._por_evaluaciones(evaluaciones, Cuestionario.estado != EstadoCuestionario.COMPLETO)

    def obtener_puntajes_competencia(self, cuestionario: Cuestionario) -> dict[str, float]:
        stmt = select(PuntajeCompetenciaLogrado).where(PuntajeCompetenciaLogrado.id_cuestionario == cuestionario.id_cuestionario)
        return {p.competencia_codigo: p.puntaje_obtenido for p in self.db.scalars(stmt)}

    # ---- Pendientes de otros CU
    def insertar(self, cuestionario): pendiente("CU025")
