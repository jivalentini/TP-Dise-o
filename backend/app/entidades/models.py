"""Entidades persistentes, según el DER actualizado.

Agregados que NO figuran en el DER (necesarios por los CU) están marcados con  # fuera del DER
"""
from datetime import date, datetime

from sqlalchemy import (Boolean, Date, DateTime, Float, ForeignKey, ForeignKeyConstraint, Integer, String,
                        UniqueConstraint, func)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..infraestructura.database import Base


class Consultor(Base):
    __tablename__ = "consultor"
    legajo: Mapped[str] = mapped_column(String(20), primary_key=True)
    username: Mapped[str] = mapped_column(String(15), unique=True)


class Puesto(Base):
    __tablename__ = "puesto"
    codigo: Mapped[str] = mapped_column(String(50), primary_key=True)
    nombre_puesto: Mapped[str] = mapped_column(String(100), unique=True)
    descripcion: Mapped[str | None] = mapped_column(String(300))
    empresa: Mapped[str] = mapped_column(String(100))
    eliminado: Mapped[bool] = mapped_column(Boolean, default=False)  # fuera del DER (baja lógica, CU011)

    caracteristicas: Mapped[list["CaracteristicaPuesto"]] = relationship(back_populates="puesto", cascade="all, delete-orphan")
    evaluaciones: Mapped[list["Evaluacion"]] = relationship(back_populates="puesto")


class Competencia(Base):
    __tablename__ = "competencia"
    codigo: Mapped[str] = mapped_column(String(50), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True)
    descripcion: Mapped[str | None] = mapped_column(String(300))
    tipo: Mapped[str] = mapped_column(String(20))
    eliminado: Mapped[bool] = mapped_column(Boolean, default=False)  # fuera del DER (CU015)

    factores: Mapped[list["Factor"]] = relationship(back_populates="competencia")


class CaracteristicaPuesto(Base):
    __tablename__ = "caracteristica_puesto"
    puesto_codigo: Mapped[str] = mapped_column(ForeignKey("puesto.codigo"), primary_key=True)
    competencia_codigo: Mapped[str] = mapped_column(ForeignKey("competencia.codigo"), primary_key=True)
    ponderacion_minima_requerida: Mapped[float] = mapped_column(Float)  # 0 a 10

    puesto: Mapped[Puesto] = relationship(back_populates="caracteristicas")
    competencia: Mapped[Competencia] = relationship()


class Factor(Base):
    __tablename__ = "factor"
    __table_args__ = (UniqueConstraint("competencia_codigo", "nro_orden"),)
    codigo: Mapped[str] = mapped_column(String(50), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True)
    descripcion: Mapped[str | None] = mapped_column(String(300))
    nro_orden: Mapped[int] = mapped_column(Integer)
    competencia_codigo: Mapped[str] = mapped_column(ForeignKey("competencia.codigo"))
    eliminado: Mapped[bool] = mapped_column(Boolean, default=False)  # fuera del DER (CU019)

    competencia: Mapped[Competencia] = relationship(back_populates="factores")
    preguntas: Mapped[list["Pregunta"]] = relationship(back_populates="factor")


class OpcionRespuesta(Base):
    __tablename__ = "opcion_respuesta"
    nombre: Mapped[str] = mapped_column(String(100), primary_key=True)
    descripcion: Mapped[str | None] = mapped_column(String(300))
    eliminado: Mapped[bool] = mapped_column(Boolean, default=False)  # fuera del DER (CU031)

    items: Mapped[list["ItemOpcion"]] = relationship(
        back_populates="opcion", order_by="ItemOpcion.orden", cascade="all, delete-orphan"
    )


class ItemOpcion(Base):
    __tablename__ = "item_opcion"
    opcion_respuesta_nombre: Mapped[str] = mapped_column(ForeignKey("opcion_respuesta.nombre"), primary_key=True)
    orden: Mapped[int] = mapped_column(Integer, primary_key=True)
    descripcion: Mapped[str] = mapped_column(String(300))

    opcion: Mapped[OpcionRespuesta] = relationship(back_populates="items")


class Pregunta(Base):
    __tablename__ = "pregunta"
    id_pregunta: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre_pregunta: Mapped[str] = mapped_column(String(300))
    enunciado: Mapped[str] = mapped_column(String(300))
    descripcion: Mapped[str | None] = mapped_column(String(300))
    factor_codigo: Mapped[str] = mapped_column(ForeignKey("factor.codigo"))
    opcion_respuesta_nombre: Mapped[str] = mapped_column(ForeignKey("opcion_respuesta.nombre"))
    eliminado: Mapped[bool] = mapped_column(Boolean, default=False)  # fuera del DER (baja lógica, CU023)

    factor: Mapped[Factor] = relationship(back_populates="preguntas")
    opcion_respuesta: Mapped[OpcionRespuesta] = relationship()
    ponderaciones: Mapped[list["PonderacionItemPregunta"]] = relationship(
        back_populates="pregunta", order_by="PonderacionItemPregunta.orden", cascade="all, delete-orphan"
    )


class PonderacionItemPregunta(Base):
    __tablename__ = "ponderacion_item_pregunta"
    __table_args__ = (
        ForeignKeyConstraint(["nombre_opcion_respuesta", "orden"], ["item_opcion.opcion_respuesta_nombre", "item_opcion.orden"]),
    )
    id_pregunta: Mapped[int] = mapped_column(ForeignKey("pregunta.id_pregunta"), primary_key=True)
    nombre_opcion_respuesta: Mapped[str] = mapped_column(String(100), primary_key=True)
    orden: Mapped[int] = mapped_column(Integer, primary_key=True)
    ponderacion: Mapped[float] = mapped_column(Float)  # las de una pregunta suman 10

    pregunta: Mapped[Pregunta] = relationship(back_populates="ponderaciones")


class Candidato(Base):
    __tablename__ = "candidato"
    __table_args__ = (UniqueConstraint("tipo_documento", "nro_documento"),)
    nro_candidato: Mapped[str] = mapped_column(String(20), primary_key=True)
    tipo_documento: Mapped[str] = mapped_column(String(3))  # DNI, LE, LC, PP
    nro_documento: Mapped[str] = mapped_column(String(15))
    apellido: Mapped[str] = mapped_column(String(100))
    nombre: Mapped[str] = mapped_column(String(100))
    fecha_nacimiento: Mapped[date | None] = mapped_column(Date)
    genero: Mapped[str | None] = mapped_column(String(1))  # H / M
    nacionalidad: Mapped[str | None] = mapped_column(String(50))
    email: Mapped[str | None] = mapped_column(String(150))
    escolaridad: Mapped[str | None] = mapped_column(String(100))
    eliminado: Mapped[bool] = mapped_column(Boolean, default=False)


class Evaluacion(Base):
    __tablename__ = "evaluacion"
    id_evaluacion: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    fecha_creacion: Mapped[date] = mapped_column(Date)
    estado: Mapped[str] = mapped_column(String(20))
    puesto_codigo: Mapped[str] = mapped_column(ForeignKey("puesto.codigo"))

    puesto: Mapped[Puesto] = relationship(back_populates="evaluaciones")
    cuestionarios: Mapped[list["Cuestionario"]] = relationship(back_populates="evaluacion")


class Cuestionario(Base):
    __tablename__ = "cuestionario"
    id_cuestionario: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())  # fuera del DER (lo usa CU026)
    fecha_inicio: Mapped[datetime | None] = mapped_column(DateTime)
    fecha_fin: Mapped[datetime | None] = mapped_column(DateTime)
    ultimo_ingreso: Mapped[datetime | None] = mapped_column(DateTime)
    cantidad_accesos: Mapped[int] = mapped_column(Integer, default=0)
    estado: Mapped[str] = mapped_column(String(20))
    clave_ingreso: Mapped[str] = mapped_column(String(8))  # se exporta a Excel en CU025, por eso no se hashea
    evaluacion_id: Mapped[int] = mapped_column(ForeignKey("evaluacion.id_evaluacion"))
    candidato_nro_candidato: Mapped[str] = mapped_column(ForeignKey("candidato.nro_candidato"))

    evaluacion: Mapped[Evaluacion] = relationship(back_populates="cuestionarios")
    candidato: Mapped[Candidato] = relationship()
    preguntas: Mapped[list["PreguntaCuestionario"]] = relationship(order_by="PreguntaCuestionario.numero_bloque")
    respuestas: Mapped[list["RespuestaCandidato"]] = relationship(
        primaryjoin="Cuestionario.id_cuestionario == foreign(RespuestaCandidato.id_cuestionario)"
    )
    puntajes_competencia: Mapped[list["PuntajeCompetenciaLogrado"]] = relationship()
    puntajes_factor: Mapped[list["PuntajeFactorLogrado"]] = relationship()

    def calcular_puntaje(self) -> tuple[dict[str, float], dict[str, float]]:
        """CU026, observación (3).

        Por cada competencia, por cada factor: total del factor = suma de las ponderaciones de las opciones
        elegidas en las preguntas de ese factor / 2. Total de la competencia = suma de los totales de sus
        factores / cantidad de factores evaluados.  Devuelve ({factor: total}, {competencia: total}).
        """
        ponderacion = {}  # (id_pregunta, orden) -> ponderación
        factor_de = {}  # id_pregunta -> Factor
        for pc in self.preguntas:
            factor_de[pc.id_pregunta] = pc.pregunta.factor
            for p in pc.pregunta.ponderaciones:
                ponderacion[(p.id_pregunta, p.orden)] = p.ponderacion

        suma_factor: dict[str, float] = {}
        competencia_de: dict[str, str] = {}
        for pc in self.preguntas:
            f = factor_de[pc.id_pregunta]
            suma_factor.setdefault(f.codigo, 0.0)
            competencia_de[f.codigo] = f.competencia_codigo
        for r in self.respuestas:
            if r.item_opcion_orden is not None:
                suma_factor[factor_de[r.id_pregunta].codigo] += ponderacion.get((r.id_pregunta, r.item_opcion_orden), 0.0)

        totales_factor = {f: round(s / 2, 2) for f, s in suma_factor.items()}
        por_competencia: dict[str, list[float]] = {}
        for f, total in totales_factor.items():
            por_competencia.setdefault(competencia_de[f], []).append(total)
        totales_competencia = {c: round(sum(v) / len(v), 2) for c, v in por_competencia.items()}
        return totales_factor, totales_competencia


class PreguntaCuestionario(Base):
    __tablename__ = "pregunta_cuestionario"
    id_pregunta: Mapped[int] = mapped_column(ForeignKey("pregunta.id_pregunta"), primary_key=True)
    id_cuestionario: Mapped[int] = mapped_column(ForeignKey("cuestionario.id_cuestionario"), primary_key=True)
    numero_bloque: Mapped[int] = mapped_column(Integer)

    pregunta: Mapped[Pregunta] = relationship()


class RespuestaCandidato(Base):
    __tablename__ = "respuesta_candidato"
    __table_args__ = (
        ForeignKeyConstraint(["id_pregunta", "id_cuestionario"], ["pregunta_cuestionario.id_pregunta", "pregunta_cuestionario.id_cuestionario"]),
        ForeignKeyConstraint(["item_opcion_nombre", "item_opcion_orden"], ["item_opcion.opcion_respuesta_nombre", "item_opcion.orden"]),
    )
    id_cuestionario: Mapped[int] = mapped_column(primary_key=True)
    id_pregunta: Mapped[int] = mapped_column(primary_key=True)
    item_opcion_nombre: Mapped[str | None] = mapped_column(String(100))
    item_opcion_orden: Mapped[int | None] = mapped_column(Integer)


class PuntajeCompetenciaLogrado(Base):
    __tablename__ = "puntaje_competencia_logrado"
    id_cuestionario: Mapped[int] = mapped_column(ForeignKey("cuestionario.id_cuestionario"), primary_key=True)
    competencia_codigo: Mapped[str] = mapped_column(ForeignKey("competencia.codigo"), primary_key=True)
    puntaje_obtenido: Mapped[float] = mapped_column(Float)
    fecha_evaluacion: Mapped[date] = mapped_column(Date)

    competencia: Mapped[Competencia] = relationship()


class PuntajeFactorLogrado(Base):
    __tablename__ = "puntaje_factor_logrado"
    id_cuestionario: Mapped[int] = mapped_column(ForeignKey("cuestionario.id_cuestionario"), primary_key=True)
    factor_codigo: Mapped[str] = mapped_column(ForeignKey("factor.codigo"), primary_key=True)
    puntaje_obtenido: Mapped[float] = mapped_column(Float)
    fecha_evaluacion: Mapped[date] = mapped_column(Date)


class OrdenDeMerito(Base):
    __tablename__ = "orden_de_merito"
    id_orden_merito: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    fecha_generacion: Mapped[date] = mapped_column(Date)
    evaluacion_id: Mapped[int] = mapped_column(ForeignKey("evaluacion.id_evaluacion"))

    items: Mapped[list["ItemOrdenMerito"]] = relationship(back_populates="orden", order_by="ItemOrdenMerito.posicion")


class ItemOrdenMerito(Base):
    __tablename__ = "item_orden_merito"
    id_orden_merito: Mapped[int] = mapped_column(ForeignKey("orden_de_merito.id_orden_merito"), primary_key=True)
    posicion: Mapped[int] = mapped_column(Integer, primary_key=True)
    puntaje_total: Mapped[float] = mapped_column(Float)
    supera_minimos_requeridos: Mapped[bool] = mapped_column(Boolean)
    candidato_nro_candidato: Mapped[str] = mapped_column(ForeignKey("candidato.nro_candidato"))

    orden: Mapped[OrdenDeMerito] = relationship(back_populates="items")


class ParametroConfiguracion(Base):
    """Fuera del DER: repositorio de configuraciones del sistema (CU026: instrucciones y parámetros)."""

    __tablename__ = "parametro_configuracion"
    clave: Mapped[str] = mapped_column(String(50), primary_key=True)
    valor: Mapped[str] = mapped_column(String(4000))


class RegistroAuditoria(Base):
    __tablename__ = "registro_auditoria"
    id_auditoria: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    fecha: Mapped[date] = mapped_column(Date)
    hora: Mapped[str] = mapped_column(String(8))  # HH:MM:SS
    accion: Mapped[str] = mapped_column(String(50))  # p. ej. BAJA_PREGUNTA
    entidad_afectada: Mapped[str] = mapped_column(String(50))
    id_entidad_afectada: Mapped[str] = mapped_column(String(50))
    consultor_legajo: Mapped[str | None] = mapped_column(ForeignKey("consultor.legajo"))
