"""GestorEvaluaciones: CU026 – Completar cuestionario, CU027 – Reporte comparativo, CU028 – Orden de mérito,
CU007 – Exportar resultados.  Los métodos del CU025 – Evaluar candidatos quedan a cargo de su implementación."""
import csv
import io
import random
import re
from datetime import date, datetime, timedelta

from ..dao import (CandidatoDAO, CuestionarioDAO, EvaluacionDAO, FactorDAO, OrdenDeMeritoDAO, PreguntaDAO, PuestoDAO,
                   RepositorioConfiguracionDAO)
from ..dto import (BloqueDTO, BloqueRespuestasDTO, CandidatoEvaluadoDTO, EstadoCuestionarioDTO, EvaluacionDTO,
                   ExportacionCriteriosDTO, ItemComparativoDTO, ItemOpcionDTO, ItemOrdenMeritoDTO, OrdenDeMeritoDTO,
                   PreguntaCuestionarioDTO, PuestoDTO, ReporteComparativoDTO, ResultadoExportadoDTO)
from ..entidades.estados import EstadoCuestionario
from ..entidades.models import Cuestionario, ItemOrdenMerito, OrdenDeMerito, RespuestaCandidato
from ..pendiente import pendiente
from .base import BaseGestor
from .excepciones import DatosInvalidos, ErrorNegocio, NoEncontrado
from .validacion import mayus

MSG_COMPLETO = "El cuestionario ha sido completado con éxito. ¡Gracias por su participación!"
MSG_POR_ESTADO = {
    EstadoCuestionario.COMPLETO: "El cuestionario ya fue completado.",
    EstadoCuestionario.INCOMPLETO: "El cuestionario se encuentra en estado Incompleto y no puede continuarse.",
    EstadoCuestionario.SIN_CONTESTAR: "El cuestionario se encuentra en estado Sin Contestar y no puede realizarse.",
}


class GestorEvaluaciones(BaseGestor):
    def __init__(self, db):
        super().__init__(db)
        self.cuestionario_dao = CuestionarioDAO(db)
        self.evaluacion_dao = EvaluacionDAO(db)
        self.puesto_dao = PuestoDAO(db)

    # ================================================================== CU025 (otro integrante)
    def crear_evaluacion(self, puesto, lista_candidatos): pendiente("CU025 paso 35")
    def exportar_claves(self, evaluacion): pendiente("CU025 paso 46")
    def validar_competencias_evaluables(self, puesto): pendiente("CU025 paso 25 (factores con >= 2 preguntas)")
    def generar_clave_aleatoria(self) -> str: pendiente("CU025 paso 39 (8 caracteres: letras y dígitos)")

    # ================================================================== CU026 – Completar cuestionario
    def _cuestionario(self, id_cuestionario: int) -> Cuestionario:
        c = self.cuestionario_dao.obtener(id_cuestionario)
        if c is None:
            raise NoEncontrado("El cuestionario no existe.")
        return c

    def _finalizar(self, c: Cuestionario, estado: str, mensaje: str, ahora: datetime) -> EstadoCuestionarioDTO:
        self.cuestionario_dao.actualizar_estado(c, estado, ahora)
        self.db.commit()
        return EstadoCuestionarioDTO(accion="FINALIZADO", estado=estado, mensaje=mensaje)

    def _verificar_tiempos(self, c: Cuestionario, ahora: datetime) -> EstadoCuestionarioDTO | None:
        """1.B (Activo: tiempo máximo en ese estado) y 1.A (En Proceso: tiempo máximo desde el primer ingreso)."""
        cfg = RepositorioConfiguracionDAO(self.db).obtener_parametros()
        if c.estado == EstadoCuestionario.ACTIVO and c.fecha_creacion and ahora - c.fecha_creacion > timedelta(minutes=cfg.tiempo_maximo_activo):
            return self._finalizar(c, EstadoCuestionario.SIN_CONTESTAR,
                                   "El cuestionario superó el tiempo máximo permitido para ser comenzado y pasó a estado Sin Contestar.", ahora)
        if c.estado == EstadoCuestionario.EN_PROCESO and c.fecha_inicio and ahora - c.fecha_inicio > timedelta(minutes=cfg.tiempo_maximo_cuestionario):
            return self._finalizar(c, EstadoCuestionario.INCOMPLETO,
                                   "Se superó el tiempo máximo para completar el cuestionario. El cuestionario pasó a estado Incompleto.", ahora)
        return None

    def obtener_cuestionario_para_completar(self, id_cuestionario: int, registrar_acceso: bool = False) -> EstadoCuestionarioDTO:
        """Paso 1 del CU026. Con registrar_acceso=True cuenta un nuevo ingreso del candidato (precondición de accesos)."""
        c = self._cuestionario(id_cuestionario)
        ahora = datetime.now()
        if c.estado not in EstadoCuestionario.ABIERTOS:
            return EstadoCuestionarioDTO(accion="FINALIZADO", estado=c.estado, mensaje=MSG_POR_ESTADO.get(c.estado))
        cfg = RepositorioConfiguracionDAO(self.db).obtener_parametros()
        if registrar_acceso:
            c.cantidad_accesos = (c.cantidad_accesos or 0) + 1
            c.ultimo_ingreso = ahora
            if c.cantidad_accesos > cfg.cantidad_maxima_accesos:
                return self._finalizar(c, EstadoCuestionario.INCOMPLETO,
                                       f"Se superó la cantidad máxima de accesos permitidos ({cfg.cantidad_maxima_accesos}). "
                                       "El cuestionario pasó a estado Incompleto.", ahora)
            self.db.commit()
        vencido = self._verificar_tiempos(c, ahora)
        if vencido:
            return vencido
        if c.estado == EstadoCuestionario.ACTIVO:
            return EstadoCuestionarioDTO(accion="INSTRUCCIONES", estado=c.estado, instrucciones=cfg.instrucciones)
        # 1.C: ya había ingresado: se posiciona en el bloque que aún no respondió
        nro = self.obtener_bloque_pendiente(c)
        if nro is None:
            return self.calcular_resultados_cuestionario(c)
        return EstadoCuestionarioDTO(accion="BLOQUE", estado=c.estado, bloque=self._bloque(c, nro))

    def armar_cuestionario(self, id_cuestionario: int) -> EstadoCuestionarioDTO:
        """Paso 3: 2 preguntas al azar por factor (con >= 2 preguntas) de cada competencia del puesto, mezcladas y en bloques."""
        c = self._cuestionario(id_cuestionario)
        ahora = datetime.now()
        if c.estado != EstadoCuestionario.ACTIVO:
            return self.obtener_cuestionario_para_completar(id_cuestionario)
        vencido = self._verificar_tiempos(c, ahora)
        if vencido:
            return vencido
        cfg = RepositorioConfiguracionDAO(self.db).obtener_parametros()
        factor_dao, pregunta_dao = FactorDAO(self.db), PreguntaDAO(self.db)
        elegidas: list[int] = []
        for caracteristica in self.puesto_dao.obtener_caracteristicas(c.evaluacion.puesto):
            for factor in factor_dao.factores_evaluables(caracteristica.competencia_codigo):
                preguntas = pregunta_dao.buscar_por_factor(factor.codigo)
                elegidas += [p.id_pregunta for p in random.sample(preguntas, 2)]
        if not elegidas:
            raise ErrorNegocio("El puesto no tiene competencias que puedan ser evaluadas. Comuníquese con la consultora.")
        random.shuffle(elegidas)
        n = cfg.cantidad_preguntas_por_bloque
        bloques = [elegidas[i:i + n] for i in range(0, len(elegidas), n)]
        self.cuestionario_dao.guardar_estructura(c, bloques, ahora)  # estado -> En Proceso, fecha de inicio
        self.db.commit()
        return EstadoCuestionarioDTO(accion="BLOQUE", estado=c.estado, bloque=self._bloque(c, 1))

    def obtener_bloque_pendiente(self, cuestionario: Cuestionario) -> int | None:
        return self.cuestionario_dao.obtener_bloque_pendiente(cuestionario)

    def _bloque(self, c: Cuestionario, nro: int) -> BloqueDTO:
        preguntas = sorted(self.cuestionario_dao.preguntas_del_bloque(c, nro), key=lambda pc: pc.id_pregunta)
        random.Random(f"{c.id_cuestionario}-{nro}").shuffle(preguntas)  # orden aleatorio pero idéntico al volver a ingresar
        return BloqueDTO(
            nro_bloque=nro, total_bloques=self.cuestionario_dao.total_bloques(c),
            preguntas=[PreguntaCuestionarioDTO(
                id_pregunta=str(pc.id_pregunta), enunciado=pc.pregunta.enunciado,
                opciones=[ItemOpcionDTO(orden=i.orden, descripcion=i.descripcion) for i in pc.pregunta.opcion_respuesta.items],
            ) for pc in preguntas],
        )

    def registrar_respuesta_bloque(self, id_cuestionario: int, bloque: BloqueRespuestasDTO) -> EstadoCuestionarioDTO:
        """Pasos 5 a 8: valida que estén todas respondidas, guarda el bloque y avanza (o finaliza)."""
        c = self._cuestionario(id_cuestionario)
        ahora = datetime.now()
        if c.estado != EstadoCuestionario.EN_PROCESO:
            return self.obtener_cuestionario_para_completar(id_cuestionario)
        vencido = self._verificar_tiempos(c, ahora)
        if vencido:
            return vencido
        pendiente_nro = self.obtener_bloque_pendiente(c)
        if pendiente_nro != bloque.nro_bloque:
            raise ErrorNegocio("Ese bloque ya fue respondido y no puede modificarse.")
        respuestas = {int(r.id_pregunta): r.orden_opcion_seleccionada for r in bloque.respuestas}
        faltan, invalidas, nuevas = [], [], []
        dto = self._bloque(c, pendiente_nro)
        for n, p in enumerate(dto.preguntas, start=1):
            orden = respuestas.get(int(p.id_pregunta))
            if orden is None:
                faltan.append((n, p))
            elif orden not in {o.orden for o in p.opciones}:
                invalidas.append((n, p))
            else:
                pc = next(x for x in self.cuestionario_dao.preguntas_del_bloque(c, pendiente_nro) if x.id_pregunta == int(p.id_pregunta))
                nuevas.append(RespuestaCandidato(id_cuestionario=c.id_cuestionario, id_pregunta=pc.id_pregunta,
                                                 item_opcion_nombre=pc.pregunta.opcion_respuesta_nombre, item_opcion_orden=orden))
        if faltan or invalidas:
            raise DatosInvalidos([f"No respondió la pregunta {n}: {p.enunciado}" for n, p in faltan] +
                                 [f"Respuesta inválida en la pregunta {n}: {p.enunciado}" for n, p in invalidas],
                                 [p.id_pregunta for _, p in faltan + invalidas])
        self.cuestionario_dao.guardar_bloque_respuestas(c, nuevas)
        c.ultimo_ingreso = ahora
        self.db.commit()
        siguiente = self.obtener_bloque_pendiente(c)
        if siguiente is None:
            return self.calcular_resultados_cuestionario(c)
        return EstadoCuestionarioDTO(accion="BLOQUE", estado=c.estado, bloque=self._bloque(c, siguiente))

    def calcular_resultados_cuestionario(self, cuestionario: Cuestionario) -> EstadoCuestionarioDTO:
        """Paso 8 – observación (3): puntaje por factor y por competencia; el cuestionario pasa a Completo."""
        self.db.refresh(cuestionario)
        puntajes_factor, puntajes_competencia = cuestionario.calcular_puntaje()
        self.cuestionario_dao.guardar_resultados(cuestionario, puntajes_factor, puntajes_competencia)
        return self._finalizar(cuestionario, EstadoCuestionario.COMPLETO, MSG_COMPLETO, datetime.now())

    # ================================================================== CU007 / CU027 – candidatos evaluados
    def candidatos_evaluados(self, codigo_puesto: str, desde: date | None = None, hasta: date | None = None) -> list[CandidatoEvaluadoDTO]:
        puesto = self._puesto(codigo_puesto)
        vistos, res = set(), []
        for c in self.cuestionario_dao.buscar_completos_por_puesto(puesto, desde, hasta):
            if c.candidato_nro_candidato in vistos:  # el más reciente por candidato
                continue
            vistos.add(c.candidato_nro_candidato)
            k = c.candidato
            res.append(CandidatoEvaluadoDTO(nro_candidato=k.nro_candidato, apellido=k.apellido, nombre=k.nombre,
                                            tipo_documento=k.tipo_documento, nro_documento=k.nro_documento,
                                            fecha_finalizacion_cuestionario=c.fecha_fin))
        return res

    def _puesto(self, codigo: str):
        p = self.puesto_dao.obtener(codigo)
        if p is None:
            raise NoEncontrado("El puesto no existe.")
        return p

    # ================================================================== CU027 – Reporte comparativo
    def emitir_reporte_comparativo(self, nro_candidato: str, codigo_puesto: str) -> ReporteComparativoDTO:
        if not nro_candidato:
            raise ErrorNegocio("Debe seleccionar al menos un candidato.")
        puesto = self._puesto(codigo_puesto)
        candidato = CandidatoDAO(self.db).obtener(nro_candidato)
        cuestionario = next((c for c in self.cuestionario_dao.buscar_completos_por_puesto(puesto)
                             if c.candidato_nro_candidato == nro_candidato), None)
        if candidato is None or cuestionario is None:
            raise ErrorNegocio("El candidato no fue evaluado en la función seleccionada.")
        obtenidos = self.cuestionario_dao.obtener_puntajes_competencia(cuestionario)
        items = [ItemComparativoDTO(nombre_competencia=c.competencia.nombre, ponderacion_requerida=c.ponderacion_minima_requerida,
                                    puntaje_obtenido=obtenidos.get(c.competencia_codigo, 0.0))
                 for c in sorted(self.puesto_dao.obtener_caracteristicas(puesto), key=lambda c: c.competencia.nombre)]
        return ReporteComparativoDTO(
            nombre_puesto=puesto.nombre_puesto, empresa=puesto.empresa,
            candidato=f"{candidato.apellido}, {candidato.nombre} ({candidato.tipo_documento} {candidato.nro_documento})",
            fecha_finalizacion_cuestionario=cuestionario.fecha_fin, items=items,
        )

    # ================================================================== CU028 – Orden de mérito
    def listar_evaluaciones(self, codigo_puesto: str) -> list[EvaluacionDTO]:
        puesto = self._puesto(codigo_puesto)
        evaluaciones = self.evaluacion_dao.buscar_por_puesto(puesto)
        if not evaluaciones:
            raise ErrorNegocio(f"El puesto {puesto.nombre_puesto} no posee evaluaciones.")
        return [EvaluacionDTO(id_evaluacion=e.id_evaluacion, fecha_creacion=e.fecha_creacion, estado=e.estado,
                              cantidad_cuestionarios=len(e.cuestionarios),
                              cantidad_completos=sum(c.estado == EstadoCuestionario.COMPLETO for c in e.cuestionarios))
                for e in evaluaciones]

    @staticmethod
    def _item(c: Cuestionario, posicion: int, puntaje: float | None, supera: bool | None) -> ItemOrdenMeritoDTO:
        completo = c.estado == EstadoCuestionario.COMPLETO
        return ItemOrdenMeritoDTO(
            posicion=posicion, tipo_documento=c.candidato.tipo_documento, nro_documento=c.candidato.nro_documento,
            apellido=c.candidato.apellido, nombre=c.candidato.nombre, puntaje_total=puntaje if completo else None,
            estado_cuestionario=c.estado, fecha_inicio=c.fecha_inicio,
            fecha_fin_o_ultimo_ingreso=c.fecha_fin if completo else c.ultimo_ingreso,
            cantidad_accesos=c.cantidad_accesos or 0, supera_minimos=supera,
        )

    def generar_orden_merito(self, codigo_puesto: str, evaluacion_seleccionada: list[int] | None) -> OrdenDeMeritoDTO:
        puesto = self._puesto(codigo_puesto)
        todas = self.evaluacion_dao.buscar_por_puesto(puesto)
        if not todas:
            raise ErrorNegocio(f"El puesto {puesto.nombre_puesto} no posee evaluaciones.")
        if evaluacion_seleccionada:
            evaluaciones = [e for e in todas if e.id_evaluacion in set(evaluacion_seleccionada)]
            if not evaluaciones:
                raise ErrorNegocio("Las evaluaciones seleccionadas no pertenecen al puesto.")
        else:
            evaluaciones = todas  # TODAS

        minimos = {c.competencia_codigo: c.ponderacion_minima_requerida for c in self.puesto_dao.obtener_caracteristicas(puesto)}
        resultados = []  # (cuestionario, puntaje_total, supera)
        for c in self.cuestionario_dao.buscar_completos_por_evaluaciones(evaluaciones):
            obtenidos = self.cuestionario_dao.obtener_puntajes_competencia(c)
            total = round(sum(obtenidos.get(k, 0.0) for k in minimos) / len(minimos), 2) if minimos else 0.0
            supera = all(obtenidos.get(k, 0.0) >= m for k, m in minimos.items())
            resultados.append((c, total, supera))
        resultados.sort(key=lambda r: (-r[1], r[0].candidato.apellido, r[0].candidato.nombre))
        superan = [r for r in resultados if r[2]]
        no_superan = [r for r in resultados if not r[2]]

        orden = [self._item(c, i, t, s) for i, (c, t, s) in enumerate(superan, start=1)]
        no_alcanzan = [self._item(c, i, t, s) for i, (c, t, s) in enumerate(no_superan, start=len(superan) + 1)]
        otros: dict[str, list[ItemOrdenMeritoDTO]] = {}
        no_completos = sorted(self.cuestionario_dao.buscar_no_completos_por_evaluaciones(evaluaciones),
                              key=lambda c: (c.estado, c.candidato.apellido, c.candidato.nombre))
        for c in no_completos:
            otros.setdefault(c.estado, []).append(self._item(c, 0, None, None))

        # Persistencia del orden de mérito: uno por evaluación, con sus candidatos completos en orden de puntaje
        dao = OrdenDeMeritoDAO(self.db)
        hoy = date.today()
        for e in evaluaciones:
            de_eval = [r for r in superan + no_superan if r[0].evaluacion_id == e.id_evaluacion]
            if not de_eval:
                continue
            om = OrdenDeMerito(fecha_generacion=hoy, evaluacion_id=e.id_evaluacion)
            om.items = [ItemOrdenMerito(posicion=i, puntaje_total=t, supera_minimos_requeridos=s, candidato_nro_candidato=c.candidato_nro_candidato)
                        for i, (c, t, s) in enumerate(de_eval, start=1)]
            dao.insertar(om)
        self.db.commit()

        return OrdenDeMeritoDTO(nombre_puesto=puesto.nombre_puesto, codigo_puesto=puesto.codigo, empresa=puesto.empresa,
                                fecha_generacion=hoy, evaluaciones=[e.id_evaluacion for e in evaluaciones],
                                items=orden, no_alcanzan_minimos=no_alcanzan, otros_por_estado=otros)

    # ================================================================== CU007 – Exportar resultados
    def buscar_funciones_exportacion(self, criterios: ExportacionCriteriosDTO) -> list[PuestoDTO]:
        nombre, empresa = mayus(criterios.nombre_funcion), mayus(criterios.empresa)
        if not (nombre or empresa or criterios.fecha_desde or criterios.fecha_hasta):
            raise ErrorNegocio("Complete al menos uno de los filtros.", "nombre_funcion")
        if criterios.fecha_desde and criterios.fecha_hasta and criterios.fecha_desde > criterios.fecha_hasta:
            raise ErrorNegocio("La fecha desde no puede ser posterior a la fecha hasta.", "fecha_desde")
        return [PuestoDTO(codigo=p.codigo, nombre_puesto=p.nombre_puesto, descripcion=p.descripcion, empresa=p.empresa)
                for p in self.puesto_dao.buscar_con_completos(nombre, empresa, criterios.fecha_desde, criterios.fecha_hasta)]

    def exportar_resultados(self, criterios: ExportacionCriteriosDTO, codigo_puesto: str | None) -> list[ResultadoExportadoDTO]:
        if not codigo_puesto:
            raise ErrorNegocio("Debe seleccionar una función.")
        self._puesto(codigo_puesto)
        return self.cuestionario_dao.buscar_resultados(codigo_puesto, criterios.fecha_desde, criterios.fecha_hasta)

    def armar_csv_resultados(self, codigo_puesto: str, resultados: list[ResultadoExportadoDTO]) -> tuple[str, str]:
        """Devuelve (nombre del archivo aaaa-mm-dd-hh-mm-Empresa-NombreFunción.csv, contenido separado por ';')."""
        puesto = self._puesto(codigo_puesto)
        limpiar = lambda s: re.sub(r'[\\/:*?"<>|]+', "", s).strip()  # noqa: E731 (caracteres inválidos en nombres de archivo)
        nombre = f"{datetime.now():%Y-%m-%d-%H-%M}-{limpiar(puesto.empresa)}-{limpiar(puesto.nombre_puesto)}.csv"
        buf = io.StringIO()
        w = csv.writer(buf, delimiter=";", lineterminator="\r\n")
        w.writerow(["Nro candidato", "Apellido", "Nombre", "Tipo documento", "Nro documento", "Código Competencia",
                    "Resultado", "Nombre puesto", "Código puesto", "Fecha finalización cuestionario"])
        for r in resultados:
            w.writerow([r.nro_candidato, r.apellido, r.nombre, r.tipo_documento, r.nro_documento, r.codigo_competencia,
                        f"{r.resultado:.2f}", r.nombre_puesto, r.codigo_puesto,
                        f"{r.fecha_finalizacion_cuestionario:%Y-%m-%d %H:%M}" if r.fecha_finalizacion_cuestionario else ""])
        return nombre, buf.getvalue()
