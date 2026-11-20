"""CU016 – Gestión de Factores, CU017 – Alta, CU018 – Modificar, CU019 – Baja."""
from sqlalchemy import func, select

from ..dao import CompetenciaDAO, FactorDAO, PreguntaDAO
from ..dto import FactorCriteriosDTO, FactorDTO
from ..entidades.models import Factor
from .base import BaseGestor, mensaje_duplicado
from .excepciones import NoEncontrado, YaExiste
from .validacion import Validador, mayus


def a_dto(f: Factor) -> FactorDTO:
    return FactorDTO(codigo=f.codigo, nombre=f.nombre, descripcion=f.descripcion, nro_orden=f.nro_orden,
                     codigo_competencia=f.competencia_codigo, nombre_competencia=f.competencia.nombre)


class GestorFactores(BaseGestor):
    def __init__(self, db):
        super().__init__(db)
        self.dao = FactorDAO(db)
        self.competencia_dao = CompetenciaDAO(db)

    def buscar_factor(self, criterios: FactorCriteriosDTO, codigo_competencia: str | None = None) -> list[FactorDTO]:
        criterios = FactorCriteriosDTO(nombre_competencia=mayus(criterios.nombre_competencia),
                                       nombre_factor=mayus(criterios.nombre_factor))
        return [a_dto(f) for f in self.dao.buscar(criterios, codigo_competencia)]

    def obtener(self, codigo: str) -> Factor:
        f = self.dao.obtener(codigo)
        if f is None:
            raise NoEncontrado("El factor no existe.")
        return f

    def ordenes_de_competencia(self, codigo_competencia: str) -> list[dict]:
        """Mecanismo para gestionar el orden (CU017): números ocupados por factores activos + el siguiente libre."""
        ocupados = [f for f in self.dao.ordenes_usados(codigo_competencia) if not f.eliminado and f.nro_orden > 0]
        return [{"nro_orden": f.nro_orden, "codigo_factor": f.codigo, "nombre_factor": f.nombre} for f in ocupados]

    def _normalizar(self, d: FactorDTO) -> FactorDTO:
        return FactorDTO(codigo=mayus(d.codigo) or "", nombre=mayus(d.nombre) or "", descripcion=mayus(d.descripcion),
                         nro_orden=d.nro_orden, codigo_competencia=(d.codigo_competencia or "").strip())

    def _validar(self, d: FactorDTO, alta: bool):
        v = Validador()
        if alta:
            v.requerido("codigo", "Código", d.codigo).longitud("codigo", "Código", d.codigo, 50)
        (v.requerido("nombre", "Nombre", d.nombre).longitud("nombre", "Nombre", d.nombre, 100)
          .requerido("descripcion", "Descripción", d.descripcion).longitud("descripcion", "Descripción", d.descripcion, 300)
          .requerido("codigo_competencia", "Competencia", d.codigo_competencia)
          .requerido("nro_orden", "Nro de orden", d.nro_orden))
        if d.nro_orden is not None:
            v.regla(d.nro_orden >= 1, "nro_orden", "El nro de orden debe ser mayor o igual a 1")
        if d.codigo_competencia:
            v.regla(self.competencia_dao.obtener(d.codigo_competencia) is not None, "codigo_competencia", "La competencia seleccionada no existe")
        v.verificar()

    def _validar_orden(self, d: FactorDTO, excluir_codigo: str | None = None):
        otro = self.dao.obtener_por_orden(d.codigo_competencia, d.nro_orden)
        if otro and otro.codigo != excluir_codigo:
            raise YaExiste(f"El nro de orden {d.nro_orden} ya existe para la competencia seleccionada (factor {otro.nombre}).", "nro_orden")

    def dar_alta_factor(self, datos: FactorDTO) -> FactorDTO:
        d = self._normalizar(datos)
        self._validar(d, alta=True)
        existente = self.dao.existe_codigo_o_nombre(d.codigo, d.nombre)
        if existente:
            raise YaExiste(*mensaje_duplicado(existente, d.codigo, d.nombre, "factor"))
        self._validar_orden(d)
        f = Factor(codigo=d.codigo, nombre=d.nombre, descripcion=d.descripcion, nro_orden=d.nro_orden,
                   competencia_codigo=d.codigo_competencia)
        self.dao.insertar(f)
        self.db.commit()
        self.db.refresh(f)
        return a_dto(f)

    def modificar_factor(self, codigo: str, nuevos_datos: FactorDTO) -> FactorDTO:
        f = self.obtener(codigo)
        d = self._normalizar(nuevos_datos)
        self._validar(d, alta=False)
        if self.dao.existe_codigo_o_nombre(None, d.nombre, excluir_codigo=f.codigo):
            raise YaExiste(f"Ya existe un factor con el nombre {d.nombre}.", "nombre")
        self._validar_orden(d, excluir_codigo=f.codigo)
        f.nombre, f.descripcion, f.nro_orden, f.competencia_codigo = d.nombre, d.descripcion, d.nro_orden, d.codigo_competencia
        self.dao.actualizar(f)
        self.db.commit()
        self.db.refresh(f)
        return a_dto(f)

    def dar_baja_factor(self, codigo: str, legajo: str) -> str:
        """Baja lógica del factor y de todas sus preguntas, con un registro de auditoría por cada una."""
        f = self.obtener(codigo)
        pregunta_dao = PreguntaDAO(self.db)
        for p in pregunta_dao.buscar_por_factor(f.codigo):
            pregunta_dao.eliminar(p)
            self.auditar("BAJA_PREGUNTA", "Pregunta", p.id_pregunta, legajo)
        # Libera el nro de orden (único por competencia en la BD) para que pueda reutilizarse
        minimo = self.db.scalar(select(func.min(Factor.nro_orden)).where(Factor.competencia_codigo == f.competencia_codigo)) or 0
        f.nro_orden = min(minimo, 0) - 1
        self.dao.eliminar(f)
        self.auditar("BAJA_FACTOR", "Factor", f.codigo, legajo)
        self.db.commit()
        return f"Los datos del factor {f.nombre} han sido eliminados del sistema."

    def mensaje_baja(self, codigo: str) -> str:
        f = self.obtener(codigo)
        return f"Los datos del factor {f.nombre} y sus preguntas serán eliminados del sistema."
