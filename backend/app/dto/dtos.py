"""DTOs del diagrama de clases (los marcados 'secuencia' salen de los diagramas de secuencia)."""
from datetime import date, datetime

from pydantic import BaseModel


# ---- Puesto
class CaracteristicaPuestoDTO(BaseModel):
    codigo_competencia: str
    nombre_competencia: str | None = None
    ponderacion_minima_requerida: float | None = None


class PuestoDTO(BaseModel):
    codigo: str
    nombre_puesto: str
    descripcion: str | None = None
    empresa: str
    caracteristicas: list[CaracteristicaPuestoDTO] = []  # CU025 paso 23


class PuestoCriteriosDTO(BaseModel):
    codigo: str | None = None
    nombre_puesto: str | None = None
    empresa: str | None = None


class PuestoResumenDTO(BaseModel):  # secuencia CU028
    codigo: str
    nombre_puesto: str
    empresa: str
    cantidad_candidatos: int
    cantidad_evaluaciones_completas: int


# ---- Candidato
class CandidatoDTO(BaseModel):
    nro_candidato: str
    tipo_documento: str
    nro_documento: str
    apellido: str
    nombre: str
    fecha_nacimiento: date | None = None
    genero: str | None = None
    nacionalidad: str | None = None
    email: str | None = None
    escolaridad: str | None = None


class CandidatoCriteriosDTO(BaseModel):
    apellido: str | None = None
    nombre: str | None = None
    nro_candidato: str | None = None


class ImportacionResultadoDTO(BaseModel):
    cantidad_creados: int
    cantidad_actualizados: int
    cantidad_eliminados: int


class CandidatoClaveDTO(BaseModel):
    nro_candidato: str
    apellido: str
    nombre: str
    tipo_documento: str
    nro_documento: str
    clave_ingreso: str


# ---- Competencia / Factor
class CompetenciaDTO(BaseModel):
    codigo: str
    nombre: str
    descripcion: str | None = None
    tipo: str


class FactorDTO(BaseModel):
    codigo: str
    nombre: str
    descripcion: str | None = None
    nro_orden: int | None = None
    codigo_competencia: str
    nombre_competencia: str | None = None


class FactorCriteriosDTO(BaseModel):
    nombre_competencia: str | None = None
    nombre_factor: str | None = None


# ---- Opción de respuesta / Pregunta
class ItemOpcionDTO(BaseModel):
    orden: int | None = None
    descripcion: str
    ponderacion: float | None = None


class OpcionRespuestaDTO(BaseModel):
    nombre: str
    descripcion: str | None = None
    items: list[ItemOpcionDTO] = []


class PreguntaDTO(BaseModel):
    id_pregunta: int | None = None
    nombre_pregunta: str
    enunciado: str
    descripcion: str | None = None
    codigo_competencia: str
    nombre_competencia: str | None = None
    codigo_factor: str
    nombre_factor: str | None = None
    nombre_opcion_respuesta: str
    ponderaciones: list[ItemOpcionDTO] = []  # deben sumar 10


class PreguntaCriteriosDTO(BaseModel):
    nombre_competencia: str | None = None
    nombre_factor: str | None = None
    nombre_pregunta: str | None = None


# ---- Cuestionario (CU026)
class RespuestaDTO(BaseModel):
    id_pregunta: str
    orden_opcion_seleccionada: int


class BloqueRespuestasDTO(BaseModel):
    id_cuestionario: str
    nro_bloque: int
    respuestas: list[RespuestaDTO] = []


class PreguntaCuestionarioDTO(BaseModel):  # CU026: lo que ve el candidato (sin ponderaciones ni competencia/factor)
    id_pregunta: str
    enunciado: str
    opciones: list[ItemOpcionDTO] = []


class BloqueDTO(BaseModel):  # secuencia CU026
    nro_bloque: int
    total_bloques: int
    preguntas: list[PreguntaCuestionarioDTO] = []


class EstadoCuestionarioDTO(BaseModel):  # CU026: qué pantalla presentar
    accion: str  # "INSTRUCCIONES" | "BLOQUE" | "FINALIZADO"
    estado: str
    mensaje: str | None = None
    instrucciones: str | None = None
    bloque: BloqueDTO | None = None


class ConfiguracionDTO(BaseModel):  # secuencia CU026 (RepositorioConfiguracionDAO)
    tiempo_maximo_activo: int
    tiempo_maximo_cuestionario: int
    cantidad_maxima_accesos: int
    cantidad_preguntas_por_bloque: int
    instrucciones: str


# ---- Generación con IA (CU033 / CU009)
class GenerarPreguntaIADTO(BaseModel):
    codigo_competencia: str | None = None
    codigo_factor: str | None = None


class GenerarPuestoIADTO(BaseModel):
    descripcion: str | None = None
    empresa: str | None = None


# ---- Respuestas genéricas de la interfaz
class MensajeDTO(BaseModel):
    mensaje: str


class PuedeEliminarDTO(BaseModel):
    puede: bool
    mensaje: str


# ---- Evaluaciones y candidatos evaluados (CU007 / CU027 / CU028)
class CandidatoEvaluadoDTO(BaseModel):
    nro_candidato: str
    apellido: str
    nombre: str
    tipo_documento: str
    nro_documento: str
    fecha_finalizacion_cuestionario: datetime | None = None


class EvaluacionDTO(BaseModel):
    id_evaluacion: int
    fecha_creacion: date
    estado: str
    cantidad_cuestionarios: int
    cantidad_completos: int


class OrdenMeritoSolicitudDTO(BaseModel):
    codigo_puesto: str
    evaluaciones: list[int] | None = None  # None = TODAS


# ---- Exportación (CU007)
class ExportacionCriteriosDTO(BaseModel):
    nombre_funcion: str | None = None
    empresa: str | None = None
    fecha_desde: date | None = None
    fecha_hasta: date | None = None


class ResultadoExportadoDTO(BaseModel):
    nro_candidato: str
    apellido: str
    nombre: str
    tipo_documento: str
    nro_documento: str
    codigo_competencia: str
    resultado: float
    nombre_puesto: str
    codigo_puesto: str
    fecha_finalizacion_cuestionario: datetime | None = None


# ---- Reportes (CU027 / CU028)
class ItemComparativoDTO(BaseModel):
    nombre_competencia: str
    ponderacion_requerida: float
    puntaje_obtenido: float


class ReporteComparativoDTO(BaseModel):
    nombre_puesto: str
    empresa: str
    candidato: str | None = None  # "APELLIDO, NOMBRE (DNI 123)"
    fecha_finalizacion_cuestionario: datetime | None = None
    items: list[ItemComparativoDTO] = []


class ItemOrdenMeritoDTO(BaseModel):
    posicion: int
    tipo_documento: str
    nro_documento: str
    apellido: str
    nombre: str
    puntaje_total: float | None = None  # no se muestra si el cuestionario no está Completo
    estado_cuestionario: str
    fecha_inicio: datetime | None = None
    fecha_fin_o_ultimo_ingreso: datetime | None = None
    cantidad_accesos: int = 0
    supera_minimos: bool | None = None  # solo para cuestionarios Completos


class OrdenDeMeritoDTO(BaseModel):
    nombre_puesto: str
    codigo_puesto: str | None = None
    empresa: str | None = None
    fecha_generacion: date
    evaluaciones: list[int] = []
    items: list[ItemOrdenMeritoDTO] = []  # orden de mérito (completos que superan mínimos), por puntaje desc
    no_alcanzan_minimos: list[ItemOrdenMeritoDTO] = []  # completos que no alcanzan los mínimos
    otros_por_estado: dict[str, list[ItemOrdenMeritoDTO]] = {}  # resto, agrupado por estado del cuestionario
