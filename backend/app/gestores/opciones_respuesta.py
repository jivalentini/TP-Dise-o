"""CU024 – Gestionar Opciones de Respuesta, CU029 – Alta, CU030 – Modificar, CU031 – Baja."""
from ..dao import OpcionRespuestaDAO
from ..dto import ItemOpcionDTO, OpcionRespuestaDTO, PuedeEliminarDTO
from ..entidades.models import ItemOpcion, OpcionRespuesta
from .base import BaseGestor
from .excepciones import EnUso, ErrorNegocio, NoEncontrado, YaExiste
from .validacion import Validador, mayus


def a_dto(o: OpcionRespuesta) -> OpcionRespuestaDTO:
    return OpcionRespuestaDTO(nombre=o.nombre, descripcion=o.descripcion,
                              items=[ItemOpcionDTO(orden=i.orden, descripcion=i.descripcion) for i in o.items])


class GestorOpcionesRespuesta(BaseGestor):
    def __init__(self, db):
        super().__init__(db)
        self.dao = OpcionRespuestaDAO(db)

    def buscar_opcion(self, nombre: str | None) -> list[OpcionRespuestaDTO]:
        return [a_dto(o) for o in self.dao.buscar(mayus(nombre))]

    def obtener(self, nombre: str) -> OpcionRespuesta:
        o = self.dao.obtener(nombre)
        if o is None:
            raise NoEncontrado("La opción de respuesta no existe.")
        return o

    @staticmethod
    def _normalizar(d: OpcionRespuestaDTO) -> OpcionRespuestaDTO:
        items = [ItemOpcionDTO(orden=i.orden, descripcion=mayus(i.descripcion) or "") for i in d.items]
        return OpcionRespuestaDTO(nombre=mayus(d.nombre) or "", descripcion=mayus(d.descripcion), items=items)

    @staticmethod
    def _validar_datos(d: OpcionRespuestaDTO):
        v = Validador()
        (v.requerido("nombre", "Nombre", d.nombre).longitud("nombre", "Nombre", d.nombre, 100)
          .requerido("descripcion", "Descripción", d.descripcion).longitud("descripcion", "Descripción", d.descripcion, 300))
        v.regla(len(d.items) >= 2, "items", "La lista de opciones debe tener al menos 2 opciones")
        for n, i in enumerate(d.items, start=1):
            if i.orden is None:
                v.requerido("items", f"orden de visualización de la opción {n}", None)
            if not i.descripcion:
                v.requerido("items", f"descripción de la opción {n}", None)
            v.longitud("items", f"Descripción de la opción {n}", i.descripcion, 300)
        v.verificar()

    @staticmethod
    def _validar_reglas(d: OpcionRespuestaDTO):
        ordenes = sorted(i.orden for i in d.items)
        if ordenes != list(range(1, len(ordenes) + 1)):
            raise ErrorNegocio("El orden de visualización no es consecutivo: debe ir de 1 a "
                               f"{len(ordenes)} sin repetirse ni saltear números.", "items")
        vistos, repetidas = set(), set()
        for i in d.items:
            (repetidas if i.descripcion in vistos else vistos).add(i.descripcion)
        if repetidas:
            raise ErrorNegocio(f"La descripción de opción está más de una vez en la opción de respuesta: {', '.join(sorted(repetidas))}.", "items")

    def dar_alta_opcion(self, datos: OpcionRespuestaDTO) -> OpcionRespuestaDTO:
        d = self._normalizar(datos)
        self._validar_datos(d)
        if self.dao.existe(d.nombre):
            raise YaExiste(f"Ya existe una opción de respuesta con el nombre {d.nombre}.", "nombre")
        self._validar_reglas(d)
        o = OpcionRespuesta(nombre=d.nombre, descripcion=d.descripcion)
        o.items = [ItemOpcion(orden=i.orden, descripcion=i.descripcion) for i in sorted(d.items, key=lambda x: x.orden)]
        self.dao.insertar(o)
        self.db.commit()
        return a_dto(o)

    def modificar_opcion(self, nombre: str, nuevos_datos: OpcionRespuestaDTO) -> OpcionRespuestaDTO:
        """El nombre es de solo lectura y no se pueden agregar ni quitar opciones."""
        o = self.obtener(nombre)
        d = self._normalizar(OpcionRespuestaDTO(nombre=o.nombre, descripcion=nuevos_datos.descripcion, items=nuevos_datos.items))
        self._validar_datos(d)
        if len(d.items) != len(o.items):
            raise ErrorNegocio("No se pueden agregar o quitar opciones.", "items")
        self._validar_reglas(d)
        o.descripcion = d.descripcion
        # Las opciones se identifican por su posición original: el orden es parte de la PK y lo referencian las ponderaciones
        actuales = list(o.items)
        reordenado = any(nuevos_datos.items[n].orden != item.orden for n, item in enumerate(actuales))
        if reordenado and self.dao.esta_en_uso(o):
            raise ErrorNegocio("No se puede cambiar el orden de visualización porque la opción de respuesta ya está "
                               "asociada a preguntas (solo pueden modificarse las descripciones).", "items")
        if reordenado:
            o.items.clear()
            self.db.flush()
            o.items = [ItemOpcion(orden=i.orden, descripcion=i.descripcion) for i in sorted(d.items, key=lambda x: x.orden)]
        else:
            for n, item in enumerate(actuales):
                item.descripcion = d.items[n].descripcion
        self.dao.actualizar(o)
        self.db.commit()
        self.db.expire(o)
        return a_dto(o)

    def puede_eliminar(self, nombre: str) -> PuedeEliminarDTO:
        o = self.obtener(nombre)
        if self.dao.esta_en_uso(o):
            return PuedeEliminarDTO(puede=False, mensaje=f"La opción de respuesta {o.nombre} está siendo usada en la base de datos y no puede eliminarse.")
        return PuedeEliminarDTO(puede=True, mensaje=f"Los datos de la opción de respuesta {o.nombre} serán eliminados del sistema.")

    def dar_baja_opcion(self, nombre: str, legajo: str) -> str:
        o = self.obtener(nombre)
        if self.dao.esta_en_uso(o):
            raise EnUso(f"La opción de respuesta {o.nombre} está siendo usada en la base de datos y no puede eliminarse.")
        self.dao.eliminar(o)
        self.auditar("BAJA_OPCION_RESPUESTA", "OpcionRespuesta", o.nombre, legajo)
        self.db.commit()
        return f"Los datos de la opción de respuesta {o.nombre} han sido eliminados del sistema."
