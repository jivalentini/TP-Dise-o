"""CU020 – Gestionar Preguntas, CU021 – Alta, CU022 – Modificar, CU023 – Baja, CU033 – Generar con IA."""
from ..dao import CompetenciaDAO, FactorDAO, OpcionRespuestaDAO, PreguntaDAO
from ..dto import GenerarPreguntaIADTO, ItemOpcionDTO, PreguntaCriteriosDTO, PreguntaDTO
from ..entidades.models import PonderacionItemPregunta, Pregunta
from ..infraestructura.ia_client import ErrorServicioIA, ServicioIA
from .base import BaseGestor
from .excepciones import ErrorNegocio, NoEncontrado, ServicioNoDisponible, YaExiste
from .validacion import Validador, mayus

MSG_IA = "Ocurrió un error al comunicarse con el servicio de IA. Intente nuevamente más tarde"


def a_dto(p: Pregunta) -> PreguntaDTO:
    pond = {x.orden: x.ponderacion for x in p.ponderaciones}
    return PreguntaDTO(
        id_pregunta=p.id_pregunta, nombre_pregunta=p.nombre_pregunta, enunciado=p.enunciado, descripcion=p.descripcion,
        codigo_competencia=p.factor.competencia_codigo, nombre_competencia=p.factor.competencia.nombre,
        codigo_factor=p.factor_codigo, nombre_factor=p.factor.nombre, nombre_opcion_respuesta=p.opcion_respuesta_nombre,
        ponderaciones=[ItemOpcionDTO(orden=i.orden, descripcion=i.descripcion, ponderacion=pond.get(i.orden))
                       for i in p.opcion_respuesta.items],
    )


class GestorPreguntas(BaseGestor):
    def __init__(self, db, ia: ServicioIA | None = None):
        super().__init__(db)
        self.dao = PreguntaDAO(db)
        self.factor_dao = FactorDAO(db)
        self.competencia_dao = CompetenciaDAO(db)
        self.opcion_dao = OpcionRespuestaDAO(db)
        self.ia = ia or ServicioIA()

    def buscar_pregunta(self, criterios: PreguntaCriteriosDTO) -> list[PreguntaDTO]:
        c = PreguntaCriteriosDTO(nombre_competencia=mayus(criterios.nombre_competencia),
                                 nombre_factor=mayus(criterios.nombre_factor), nombre_pregunta=mayus(criterios.nombre_pregunta))
        if not (c.nombre_competencia or c.nombre_factor or c.nombre_pregunta):
            raise ErrorNegocio("Ingrese al menos un criterio de búsqueda.", "nombre_competencia")
        return [a_dto(p) for p in self.dao.buscar(c)]

    def obtener(self, id_pregunta: int) -> Pregunta:
        p = self.dao.obtener(id_pregunta)
        if p is None:
            raise NoEncontrado("La pregunta no existe.")
        return p

    def obtener_dto(self, id_pregunta: int) -> PreguntaDTO:
        return a_dto(self.obtener(id_pregunta))

    # ---- validaciones comunes a CU021 y CU022
    @staticmethod
    def _normalizar(d: PreguntaDTO) -> PreguntaDTO:
        return d.model_copy(update={
            "nombre_pregunta": mayus(d.nombre_pregunta) or "", "enunciado": mayus(d.enunciado) or "",
            "descripcion": mayus(d.descripcion), "codigo_competencia": (d.codigo_competencia or "").strip(),
            "codigo_factor": (d.codigo_factor or "").strip(), "nombre_opcion_respuesta": (d.nombre_opcion_respuesta or "").strip(),
        })

    def _validar(self, d: PreguntaDTO):
        v = Validador()
        (v.requerido("codigo_competencia", "Competencia", d.codigo_competencia)
          .requerido("codigo_factor", "Factor", d.codigo_factor)
          .requerido("nombre_pregunta", "Nombre de Pregunta", d.nombre_pregunta)
          .requerido("enunciado", "Pregunta", d.enunciado)
          .requerido("nombre_opcion_respuesta", "Opción de Respuesta", d.nombre_opcion_respuesta))
        v.verificar()  # 2.A: primero todas las omisiones
        (v.longitud("nombre_pregunta", "Nombre de Pregunta", d.nombre_pregunta, 300)
          .longitud("enunciado", "Pregunta", d.enunciado, 300)
          .longitud("descripcion", "Descripción", d.descripcion, 300))
        v.verificar()  # 2.B: longitudes

        factor = self.factor_dao.obtener(d.codigo_factor)
        if factor is None or factor.competencia_codigo != d.codigo_competencia:
            raise ErrorNegocio("El factor seleccionado no pertenece a la competencia seleccionada.", "codigo_factor")
        opcion = self.opcion_dao.obtener(d.nombre_opcion_respuesta)
        if opcion is None:
            raise ErrorNegocio("La opción de respuesta seleccionada no existe.", "nombre_opcion_respuesta")

        pond = {i.orden: i.ponderacion for i in d.ponderaciones}
        faltan = [i.descripcion for i in opcion.items if pond.get(i.orden) is None]
        if faltan:
            raise ErrorNegocio(f"Falta ingresar la ponderación de: {', '.join(faltan)}.", "ponderaciones")
        valores = [pond[i.orden] for i in opcion.items]
        if any(x < 0 for x in valores):
            raise ErrorNegocio("Las ponderaciones de las opciones de respuesta deben ser 0 o positivas.", "ponderaciones")
        if abs(sum(valores) - 10) > 0.001:
            raise ErrorNegocio(f"Las ponderaciones de las opciones de respuesta deben sumar 10 puntos (suman {sum(valores):g}).", "ponderaciones")
        return opcion, pond

    def _validar_existencia(self, d: PreguntaDTO, excluir_id: int | None = None):
        otra = self.dao.existe_pregunta(d.nombre_pregunta, d.enunciado, d.codigo_competencia, d.codigo_factor, excluir_id)
        if otra:
            if otra.nombre_pregunta == d.nombre_pregunta:
                raise YaExiste("Ya existe una pregunta con ese NOMBRE para la competencia y factor seleccionados.", "nombre_pregunta")
            raise YaExiste("Ya existe una pregunta con ese ENUNCIADO (pregunta) para la competencia y factor seleccionados.", "enunciado")

    # ---- CU021
    def dar_alta_pregunta(self, datos: PreguntaDTO) -> PreguntaDTO:
        d = self._normalizar(datos)
        opcion, pond = self._validar(d)
        self._validar_existencia(d)
        p = Pregunta(nombre_pregunta=d.nombre_pregunta, enunciado=d.enunciado, descripcion=d.descripcion,
                     factor_codigo=d.codigo_factor, opcion_respuesta_nombre=opcion.nombre)
        p.ponderaciones = [PonderacionItemPregunta(nombre_opcion_respuesta=opcion.nombre, orden=i.orden, ponderacion=pond[i.orden])
                           for i in opcion.items]
        self.dao.insertar(p)
        self.db.commit()
        self.db.refresh(p)
        return a_dto(p)

    # ---- CU022 (competencia y factor son de solo lectura)
    def modificar_pregunta(self, id_pregunta: int, nuevos_datos: PreguntaDTO) -> PreguntaDTO:
        p = self.obtener(id_pregunta)
        d = self._normalizar(nuevos_datos.model_copy(update={
            "codigo_competencia": p.factor.competencia_codigo, "codigo_factor": p.factor_codigo}))
        opcion, pond = self._validar(d)
        self._validar_existencia(d, excluir_id=p.id_pregunta)
        p.nombre_pregunta, p.enunciado, p.descripcion = d.nombre_pregunta, d.enunciado, d.descripcion
        if p.opcion_respuesta_nombre != opcion.nombre:
            p.ponderaciones.clear()
            self.db.flush()
            p.opcion_respuesta_nombre = opcion.nombre
            p.ponderaciones = [PonderacionItemPregunta(nombre_opcion_respuesta=opcion.nombre, orden=i.orden, ponderacion=pond[i.orden])
                               for i in opcion.items]
        else:
            for x in p.ponderaciones:
                x.ponderacion = pond[x.orden]
        self.dao.actualizar(p)
        self.db.commit()
        self.db.refresh(p)
        return a_dto(p)

    # ---- CU023
    def mensaje_baja(self, id_pregunta: int) -> str:
        return f"Los datos de la pregunta {self.obtener(id_pregunta).nombre_pregunta} serán eliminados del sistema."

    def dar_baja_pregunta(self, id_pregunta: int, legajo: str) -> str:
        p = self.obtener(id_pregunta)
        self.dao.eliminar(p)
        self.auditar("BAJA_PREGUNTA", "Pregunta", p.id_pregunta, legajo)
        self.db.commit()
        return f"Los datos de la pregunta {p.nombre_pregunta} han sido eliminados del sistema."

    # ---- CU033
    def generar_pregunta_ia(self, datos: GenerarPreguntaIADTO) -> PreguntaDTO:
        v = Validador()
        v.requerido("codigo_competencia", "Competencia", datos.codigo_competencia).requerido("codigo_factor", "Factor", datos.codigo_factor)
        v.verificar()
        competencia = self.competencia_dao.obtener(datos.codigo_competencia)
        factor = self.factor_dao.obtener(datos.codigo_factor)
        if competencia is None or factor is None or factor.competencia_codigo != competencia.codigo:
            raise ErrorNegocio("El factor seleccionado no pertenece a la competencia seleccionada.", "codigo_factor")
        opciones = [{"nombre": o.nombre, "descripcion": o.descripcion,
                     "items": [{"orden": i.orden, "descripcion": i.descripcion} for i in o.items]}
                    for o in self.opcion_dao.buscar(None)]
        try:
            r = self.ia.generar_pregunta(
                {"codigo": competencia.codigo, "nombre": competencia.nombre, "descripcion": competencia.descripcion, "tipo": competencia.tipo},
                {"codigo": factor.codigo, "nombre": factor.nombre, "descripcion": factor.descripcion},
                opciones,
            )
            nombre_opcion = str(r.get("nombre_opcion_respuesta") or "").strip()
            opcion = self.opcion_dao.obtener(nombre_opcion.upper()) or self.opcion_dao.obtener(nombre_opcion)
            pond = {int(x["orden"]): float(x["ponderacion"]) for x in r.get("ponderaciones", [])}
        except (ErrorServicioIA, KeyError, TypeError, ValueError) as e:
            raise ServicioNoDisponible(MSG_IA) from e
        return PreguntaDTO(
            nombre_pregunta=(mayus(r.get("nombre_pregunta")) or "")[:300], enunciado=(mayus(r.get("enunciado")) or "")[:300],
            descripcion=(mayus(r.get("descripcion")) or "")[:300] or None,
            codigo_competencia=competencia.codigo, nombre_competencia=competencia.nombre,
            codigo_factor=factor.codigo, nombre_factor=factor.nombre,
            nombre_opcion_respuesta=opcion.nombre if opcion else "",
            ponderaciones=[ItemOpcionDTO(orden=i.orden, descripcion=i.descripcion, ponderacion=pond.get(i.orden))
                           for i in (opcion.items if opcion else [])],
        )
