"""CU008 – Gestionar Puestos, CU009 – Alta (con GenAI), CU010 – Modificar, CU011 – Baja; búsqueda para CU027/CU028."""
from ..dao import CandidatoDAO, CompetenciaDAO, CuestionarioDAO, PuestoDAO
from ..dto import (CaracteristicaPuestoDTO, GenerarPuestoIADTO, PuedeEliminarDTO, PuestoCriteriosDTO, PuestoDTO,
                   PuestoResumenDTO)
from ..entidades.models import CaracteristicaPuesto, Puesto
from ..infraestructura.ia_client import ErrorServicioIA, ServicioIA
from .base import BaseGestor, mensaje_duplicado
from .excepciones import EnUso, ErrorNegocio, NoEncontrado, ServicioNoDisponible, YaExiste
from .preguntas import MSG_IA
from .validacion import Validador, mayus


def a_dto(p: Puesto) -> PuestoDTO:
    return PuestoDTO(
        codigo=p.codigo, nombre_puesto=p.nombre_puesto, descripcion=p.descripcion, empresa=p.empresa,
        caracteristicas=[CaracteristicaPuestoDTO(codigo_competencia=c.competencia_codigo, nombre_competencia=c.competencia.nombre,
                                                 ponderacion_minima_requerida=c.ponderacion_minima_requerida)
                         for c in sorted(p.caracteristicas, key=lambda c: c.competencia.nombre)],
    )


class GestorPuestos(BaseGestor):
    def __init__(self, db, ia: ServicioIA | None = None):
        super().__init__(db)
        self.dao = PuestoDAO(db)
        self.competencia_dao = CompetenciaDAO(db)
        self.ia = ia or ServicioIA()

    @staticmethod
    def _criterios(c: PuestoCriteriosDTO, requerido: bool) -> PuestoCriteriosDTO:
        c = PuestoCriteriosDTO(codigo=mayus(c.codigo), nombre_puesto=mayus(c.nombre_puesto), empresa=mayus(c.empresa))
        if requerido and not (c.codigo or c.nombre_puesto or c.empresa):
            raise ErrorNegocio("Ingrese al menos un criterio de búsqueda.", "codigo")
        return c

    def buscar_puesto(self, criterios: PuestoCriteriosDTO, requerido: bool = True) -> list[PuestoDTO]:
        return [PuestoDTO(codigo=p.codigo, nombre_puesto=p.nombre_puesto, descripcion=p.descripcion, empresa=p.empresa)
                for p in self.dao.buscar(self._criterios(criterios, requerido))]

    def buscar_puesto_con_resumen(self, criterios: PuestoCriteriosDTO) -> list[PuestoResumenDTO]:
        """CU028 paso 4: incluye cantidad de candidatos y de evaluaciones (cuestionarios) completas."""
        candidato_dao, cuestionario_dao = CandidatoDAO(self.db), CuestionarioDAO(self.db)
        return [
            PuestoResumenDTO(codigo=p.codigo, nombre_puesto=p.nombre_puesto, empresa=p.empresa,
                             cantidad_candidatos=candidato_dao.contar_por_puesto(p),
                             cantidad_evaluaciones_completas=cuestionario_dao.contar_completos_por_puesto(p))
            for p in self.dao.buscar(self._criterios(criterios, True))
        ]

    def obtener(self, codigo: str) -> Puesto:
        p = self.dao.obtener(codigo)
        if p is None:
            raise NoEncontrado("El puesto no existe.")
        return p

    def obtener_dto(self, codigo: str) -> PuestoDTO:
        return a_dto(self.obtener(codigo))

    # ---- validaciones comunes a CU009 y CU010
    @staticmethod
    def _normalizar(d: PuestoDTO) -> PuestoDTO:
        return PuestoDTO(
            codigo=mayus(d.codigo) or "", nombre_puesto=mayus(d.nombre_puesto) or "", descripcion=mayus(d.descripcion),
            empresa=mayus(d.empresa) or "",
            caracteristicas=[CaracteristicaPuestoDTO(codigo_competencia=(c.codigo_competencia or "").strip(),
                                                     ponderacion_minima_requerida=c.ponderacion_minima_requerida)
                             for c in d.caracteristicas],
        )

    def _validar(self, d: PuestoDTO, alta: bool):
        v = Validador()
        if alta:
            v.requerido("codigo", "Código", d.codigo).longitud("codigo", "Código", d.codigo, 50)
        (v.requerido("nombre_puesto", "Nombre del Puesto", d.nombre_puesto).longitud("nombre_puesto", "Nombre del Puesto", d.nombre_puesto, 100)
          .requerido("descripcion", "Descripción", d.descripcion).longitud("descripcion", "Descripción", d.descripcion, 300)
          .requerido("empresa", "Empresa", d.empresa).longitud("empresa", "Empresa", d.empresa, 100)
          .requerido("caracteristicas", "Características del Puesto (al menos una competencia)", d.caracteristicas))
        vistas = set()
        for n, c in enumerate(d.caracteristicas, start=1):
            if not c.codigo_competencia:
                v.requerido("caracteristicas", f"competencia de la fila {n} de Características del Puesto", None)
                continue
            comp = self.competencia_dao.obtener(c.codigo_competencia)
            nombre = comp.nombre if comp else c.codigo_competencia
            v.regla(comp is not None, "caracteristicas", f"La competencia {nombre} no existe")
            v.regla(c.codigo_competencia not in vistas, "caracteristicas", f"La competencia {nombre} está más de una vez (cada competencia puede existir una sola vez para cada puesto)")
            vistas.add(c.codigo_competencia)
            if c.ponderacion_minima_requerida is None:
                v.requerido("caracteristicas", f"ponderación de la competencia {nombre}", None)
            else:
                v.regla(0 <= c.ponderacion_minima_requerida <= 10, "caracteristicas", f"La ponderación de {nombre} debe estar entre 0 y 10")
        v.verificar()

    def dar_alta_puesto(self, datos: PuestoDTO) -> PuestoDTO:
        d = self._normalizar(datos)
        self._validar(d, alta=True)
        existente = self.dao.existe_codigo_o_nombre(d.codigo, d.nombre_puesto)
        if existente:
            raise YaExiste(*mensaje_duplicado(existente, d.codigo, d.nombre_puesto, "puesto", campo_nombre="nombre_puesto"))
        p = Puesto(codigo=d.codigo, nombre_puesto=d.nombre_puesto, descripcion=d.descripcion, empresa=d.empresa)
        p.caracteristicas = [CaracteristicaPuesto(competencia_codigo=c.codigo_competencia,
                                                  ponderacion_minima_requerida=c.ponderacion_minima_requerida)
                             for c in d.caracteristicas]
        self.dao.insertar(p)
        self.db.commit()
        self.db.refresh(p)
        return a_dto(p)

    def modificar_puesto(self, codigo: str, nuevos_datos: PuestoDTO) -> PuestoDTO:
        p = self.obtener(codigo)
        d = self._normalizar(nuevos_datos.model_copy(update={"codigo": p.codigo}))
        self._validar(d, alta=False)
        if self.dao.existe_codigo_o_nombre(None, d.nombre_puesto, excluir_codigo=p.codigo):
            raise YaExiste(f"Ya existe un puesto con el nombre {d.nombre_puesto}.", "nombre_puesto")
        actuales = {c.competencia_codigo: c for c in p.caracteristicas}
        nuevas = {c.codigo_competencia: c.ponderacion_minima_requerida for c in d.caracteristicas}
        if set(actuales) != set(nuevas) and self.dao.tiene_cuestionarios(p):
            raise ErrorNegocio("No se pueden agregar ni quitar competencias al puesto porque ya existen cuestionarios generados para el mismo.", "caracteristicas")
        p.nombre_puesto, p.descripcion, p.empresa = d.nombre_puesto, d.descripcion, d.empresa
        for cod, c in list(actuales.items()):
            if cod not in nuevas:
                p.caracteristicas.remove(c)
            else:
                c.ponderacion_minima_requerida = nuevas[cod]
        for cod, pond in nuevas.items():
            if cod not in actuales:
                p.caracteristicas.append(CaracteristicaPuesto(competencia_codigo=cod, ponderacion_minima_requerida=pond))
        self.dao.actualizar(p)
        self.db.commit()
        self.db.refresh(p)
        return a_dto(p)

    def puede_eliminar(self, codigo: str) -> PuedeEliminarDTO:
        p = self.obtener(codigo)
        if self.dao.existe_en_uso(p):
            return PuedeEliminarDTO(puede=False, mensaje=f"El puesto {p.nombre_puesto} está siendo usado en la base de datos y no puede eliminarse.")
        return PuedeEliminarDTO(puede=True, mensaje=f"Los datos del puesto {p.nombre_puesto} serán eliminados del sistema.")

    def dar_baja_puesto(self, codigo: str, legajo: str) -> str:
        p = self.obtener(codigo)
        if self.dao.existe_en_uso(p):
            raise EnUso(f"El puesto {p.nombre_puesto} está siendo usado en la base de datos y no puede eliminarse.")
        self.dao.eliminar(p)
        self.auditar("BAJA_PUESTO", "Puesto", p.codigo, legajo)
        self.db.commit()
        return f"Los datos del puesto {p.nombre_puesto} han sido eliminados del sistema."

    # ---- Creación con GenAI (alcance: "Gestión de puestos o funciones. Creación con GenAI")
    def generar_puesto_ia(self, datos: GenerarPuestoIADTO) -> PuestoDTO:
        v = Validador()
        v.requerido("descripcion", "Descripción", datos.descripcion).verificar()
        competencias = {c.codigo: c for c in self.competencia_dao.buscar(None)}
        try:
            r = self.ia.generar_puesto(
                datos.descripcion, datos.empresa,
                [{"codigo": c.codigo, "nombre": c.nombre, "descripcion": c.descripcion, "tipo": c.tipo} for c in competencias.values()],
            )
            caracteristicas = [
                CaracteristicaPuestoDTO(codigo_competencia=x["codigo_competencia"], nombre_competencia=competencias[x["codigo_competencia"]].nombre,
                                        ponderacion_minima_requerida=max(0.0, min(10.0, float(x["ponderacion_minima_requerida"]))))
                for x in r.get("caracteristicas", []) if x.get("codigo_competencia") in competencias
            ]
        except (ErrorServicioIA, KeyError, TypeError, ValueError) as e:
            raise ServicioNoDisponible(MSG_IA) from e
        return PuestoDTO(codigo="", nombre_puesto=(mayus(r.get("nombre_puesto")) or "")[:100],
                         descripcion=(mayus(r.get("descripcion")) or "")[:300], empresa=mayus(datos.empresa) or "",
                         caracteristicas=caracteristicas)
