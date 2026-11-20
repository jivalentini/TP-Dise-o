"""CU012 – Gestionar Competencias, CU013 – Alta, CU014 – Modificar, CU015 – Baja."""
from ..dao import CompetenciaDAO
from ..dto import CompetenciaDTO, PuedeEliminarDTO
from ..entidades.estados import TipoCompetencia
from ..entidades.models import Competencia
from .base import BaseGestor, mensaje_duplicado
from .excepciones import NoEncontrado, YaExiste, EnUso
from .validacion import Validador, mayus

TIPOS = (TipoCompetencia.TECNICA, TipoCompetencia.ACTITUDINAL)


def a_dto(c: Competencia) -> CompetenciaDTO:
    return CompetenciaDTO(codigo=c.codigo, nombre=c.nombre, descripcion=c.descripcion, tipo=c.tipo)


class GestorCompetencias(BaseGestor):
    def __init__(self, db):
        super().__init__(db)
        self.dao = CompetenciaDAO(db)

    def buscar_competencia(self, nombre: str | None) -> list[CompetenciaDTO]:
        return [a_dto(c) for c in self.dao.buscar(mayus(nombre))]

    def obtener(self, codigo: str) -> Competencia:
        c = self.dao.obtener(codigo)
        if c is None:
            raise NoEncontrado("La competencia no existe.")
        return c

    def _normalizar(self, datos: CompetenciaDTO) -> CompetenciaDTO:
        tipo = next((t for t in TIPOS if datos.tipo and t.upper() == datos.tipo.strip().upper()), datos.tipo)
        return CompetenciaDTO(codigo=mayus(datos.codigo) or "", nombre=mayus(datos.nombre) or "",
                              descripcion=mayus(datos.descripcion), tipo=tipo or "")

    def _validar(self, d: CompetenciaDTO, alta: bool):
        v = Validador()
        if alta:
            v.requerido("codigo", "Código", d.codigo).longitud("codigo", "Código", d.codigo, 50)
        (v.requerido("nombre", "Nombre", d.nombre).longitud("nombre", "Nombre", d.nombre, 100)
          .requerido("descripcion", "Descripción", d.descripcion).longitud("descripcion", "Descripción", d.descripcion, 300)
          .requerido("tipo", "Tipo", d.tipo))
        if d.tipo:
            v.regla(d.tipo in TIPOS, "tipo", "El tipo debe ser Técnica o Actitudinal")
        v.verificar()

    def dar_alta_competencia(self, datos: CompetenciaDTO) -> CompetenciaDTO:
        d = self._normalizar(datos)
        self._validar(d, alta=True)
        existente = self.dao.existe_codigo_o_nombre(d.codigo, d.nombre)
        if existente:
            raise YaExiste(*mensaje_duplicado(existente, d.codigo, d.nombre, "competencia", articulo="una"))
        c = Competencia(codigo=d.codigo, nombre=d.nombre, descripcion=d.descripcion, tipo=d.tipo)
        self.dao.insertar(c)
        self.db.commit()
        return a_dto(c)

    def modificar_competencia(self, codigo: str, nuevos_datos: CompetenciaDTO) -> CompetenciaDTO:
        c = self.obtener(codigo)
        d = self._normalizar(nuevos_datos)
        self._validar(d, alta=False)
        if self.dao.existe_codigo_o_nombre(None, d.nombre, excluir_codigo=c.codigo):
            raise YaExiste(f"Ya existe una competencia con el nombre {d.nombre}.", "nombre")
        c.nombre, c.descripcion, c.tipo = d.nombre, d.descripcion, d.tipo
        self.dao.actualizar(c)
        self.db.commit()
        return a_dto(c)

    def puede_eliminar(self, codigo: str) -> PuedeEliminarDTO:
        c = self.obtener(codigo)
        if self.dao.esta_en_uso(c):
            return PuedeEliminarDTO(puede=False, mensaje=f"La competencia {c.nombre} está siendo usada en la base de datos y no puede eliminarse.")
        return PuedeEliminarDTO(puede=True, mensaje=f"Los datos de la competencia {c.nombre} serán eliminados del sistema.")

    def dar_baja_competencia(self, codigo: str, legajo: str) -> str:
        c = self.obtener(codigo)
        if self.dao.esta_en_uso(c):
            raise EnUso(f"La competencia {c.nombre} está siendo usada en la base de datos y no puede eliminarse.")
        self.dao.eliminar(c)
        self.auditar("BAJA_COMPETENCIA", "Competencia", c.codigo, legajo)
        self.db.commit()
        return f"Los datos de la competencia {c.nombre} han sido eliminados del sistema."
