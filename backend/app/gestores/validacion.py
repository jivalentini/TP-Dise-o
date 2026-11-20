"""Ayuda para los flujos alternativos 2.A (omisiones) y 2.B (longitud máxima) de los ABM."""
from .excepciones import DatosInvalidos


def mayus(valor: str | None) -> str | None:
    """Los datos literales se ingresan SIEMPRE en mayúsculas."""
    if valor is None:
        return None
    valor = valor.strip().upper()
    return valor or None


class Validador:
    def __init__(self):
        self.errores: list[str] = []
        self.campos: list[str] = []

    def _error(self, campo: str, mensaje: str):
        self.errores.append(mensaje)
        if campo not in self.campos:
            self.campos.append(campo)

    def requerido(self, campo: str, etiqueta: str, valor) -> "Validador":
        if valor is None or (isinstance(valor, str) and not valor.strip()) or (isinstance(valor, list) and not valor):
            self._error(campo, f"Falta ingresar: {etiqueta}")
        return self

    def longitud(self, campo: str, etiqueta: str, valor: str | None, maximo: int) -> "Validador":
        if valor and len(valor) > maximo:
            self._error(campo, f"{etiqueta} excede la longitud máxima ({len(valor)}/{maximo} caracteres)")
        return self

    def regla(self, condicion: bool, campo: str, mensaje: str) -> "Validador":
        if not condicion:
            self._error(campo, mensaje)
        return self

    def verificar(self):
        if self.errores:
            raise DatosInvalidos(self.errores, self.campos)
