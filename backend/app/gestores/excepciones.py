class CredencialesInvalidas(Exception):
    """Usuario/contraseña inválidos (consultor) o candidato/cuestionario/clave inválidos."""


class ErrorNegocio(Exception):
    """Error de negocio con mensaje para el usuario. `campo` indica dónde poner el foco."""

    status_code = 400

    def __init__(self, mensaje: str, campo: str | None = None):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.campo = campo


class DatosInvalidos(ErrorNegocio):
    """Omisiones / longitudes excedidas: se informan TODAS juntas (flujos 2.A / 2.B de los ABM)."""

    def __init__(self, errores: list[str], campos: list[str] | None = None):
        super().__init__("Corrija los siguientes datos:", campos[0] if campos else None)
        self.errores = errores
        self.campos = campos or []


class YaExiste(ErrorNegocio):
    status_code = 409


class EnUso(ErrorNegocio):
    status_code = 409


class NoEncontrado(ErrorNegocio):
    status_code = 404


class ServicioNoDisponible(ErrorNegocio):
    status_code = 503
