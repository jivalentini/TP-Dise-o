from ..dto import ConfiguracionDTO
from ..entidades.models import ParametroConfiguracion
from .base import BaseDAO

INSTRUCCIONES = (
    "Bienvenido/a al cuestionario de evaluación de competencias.\n\n"
    "• Cada pregunta tiene una única respuesta correcta para usted: elija la opción con la que más se identifique.\n"
    "• Las preguntas se presentan en bloques. Debe responder TODAS las preguntas del bloque para avanzar.\n"
    "• Una vez que avanza al siguiente bloque NO podrá volver a ver ni modificar las respuestas anteriores.\n"
    "• Puede salir y volver a ingresar más tarde: continuará desde el bloque que aún no respondió.\n"
    "• Tenga en cuenta el tiempo máximo y la cantidad máxima de ingresos permitidos."
)

# Valores por defecto si el parámetro no está cargado en el repositorio
DEFAULTS = {
    "tiempo_maximo_activo": "10080",  # minutos (7 días) desde que se generó el cuestionario
    "tiempo_maximo_cuestionario": "120",  # minutos desde el primer ingreso a completarlo
    "cantidad_maxima_accesos": "5",
    "cantidad_preguntas_por_bloque": "4",
    "instrucciones": INSTRUCCIONES,
}


class RepositorioConfiguracionDAO(BaseDAO):
    """Aparece en el diagrama de secuencia del CU026 (no en el diagrama de clases)."""

    def obtener_parametros(self) -> ConfiguracionDTO:
        valores = dict(DEFAULTS)
        for p in self.db.query(ParametroConfiguracion).all():
            valores[p.clave] = p.valor
        return ConfiguracionDTO(
            tiempo_maximo_activo=int(valores["tiempo_maximo_activo"]),
            tiempo_maximo_cuestionario=int(valores["tiempo_maximo_cuestionario"]),
            cantidad_maxima_accesos=int(valores["cantidad_maxima_accesos"]),
            cantidad_preguntas_por_bloque=max(1, int(valores["cantidad_preguntas_por_bloque"])),
            instrucciones=valores["instrucciones"],
        )
