"""Impresora – spool de impresión (IPP vía CUPS). Usada por CU028 (listado de orden de mérito).

Si IMPRESORA_URI está vacío, la interfaz imprime desde el navegador (diálogo de impresión del SO).
"""
import shutil
import subprocess

from ..config import settings


class ImpresoraNoDisponible(Exception):
    pass


class Impresora:
    def disponible(self) -> bool:
        return bool(settings.impresora_uri) and shutil.which("lp") is not None

    def imprimir(self, documento: bytes, titulo: str = "Listado") -> None:
        if not self.disponible():
            raise ImpresoraNoDisponible()
        try:
            subprocess.run(["lp", "-d", settings.impresora_uri, "-t", titulo], input=documento, check=True,
                           capture_output=True, timeout=30)
        except (subprocess.SubprocessError, OSError) as e:
            raise ImpresoraNoDisponible() from e
