"""CU032 – Finalizar cuestionarios (actor: Sistema, ejecución periódica)."""
from datetime import datetime

from ..dao import CuestionarioDAO, RepositorioConfiguracionDAO
from ..entidades.estados import EstadoCuestionario
from ..infraestructura.database import SessionLocal
from .base import BaseGestor


class ProcesoBatchFinalizacionCuestionarios:
    """Pasa a Incompleto / Sin Contestar los cuestionarios vencidos y registra inicio y fin de la ejecución."""

    def __init__(self, session_factory=SessionLocal):
        self.session_factory = session_factory

    def ejecutar(self) -> dict:
        with self.session_factory() as db:
            gestor, dao = BaseGestor(db), CuestionarioDAO(db)
            gestor.auditar("INICIO_EJECUCION", "ProcesoBatchFinalizacionCuestionarios", "CU032", None)
            db.commit()

            ahora = datetime.now()
            cfg = RepositorioConfiguracionDAO(db).obtener_parametros()
            incompletos = dao.buscar_vencidos(cfg.tiempo_maximo_cuestionario, ahora)  # paso 2
            for c in incompletos:
                dao.actualizar_estado(c, EstadoCuestionario.INCOMPLETO, ahora)
            sin_contestar = dao.buscar_activos_vencidos(cfg.tiempo_maximo_activo, ahora)  # paso 3
            for c in sin_contestar:
                dao.actualizar_estado(c, EstadoCuestionario.SIN_CONTESTAR, ahora)

            gestor.auditar("FIN_EJECUCION", "ProcesoBatchFinalizacionCuestionarios", "CU032", None)
            db.commit()
            return {"incompletos": len(incompletos), "sin_contestar": len(sin_contestar)}
