"""Servicio de IA (GenAI) – HTTPS / REST (JSON). Usado por CU033 (preguntas, desde CU021) y CU009 (puestos).

IA_MODE:
  mock      -> genera contenido de ejemplo localmente (para desarrollo / demo sin credenciales)
  api       -> REST propio: POST {IA_BASE_URL}/preguntas  y  POST {IA_BASE_URL}/puestos  (JSON)
  anthropic -> API de Claude (Messages API) con IA_API_KEY e IA_MODEL
"""
import json
import random
import re

import httpx

from ..config import settings


class ErrorServicioIA(Exception):
    pass


def _ponderaciones_crecientes(n: int) -> list[float]:
    """n valores >= 0, crecientes, que suman 10 (2 decimales)."""
    total = n * (n - 1) / 2 or 1
    valores = [round(10 * i / total, 2) for i in range(n)]
    valores[-1] = round(10 - sum(valores[:-1]), 2)
    return valores


class ServicioIA:
    TIMEOUT = 30

    # ------------------------------------------------------------------ CU033
    def generar_pregunta(self, competencia: dict, factor: dict, opciones: list[dict]) -> dict:
        """Devuelve {nombre_pregunta, enunciado, descripcion, nombre_opcion_respuesta, ponderaciones: [{orden, ponderacion}]}."""
        if not opciones:
            raise ErrorServicioIA("No hay opciones de respuesta cargadas")
        payload = {"competencia": competencia, "factor": factor, "opciones_respuesta": opciones}
        if settings.ia_mode == "mock":
            return self._mock_pregunta(competencia, factor, opciones)
        if settings.ia_mode == "api":
            return self._post("/preguntas", payload)
        prompt = (
            "Sos un especialista en selección de personal de una consultora de RRHH de TIC. Generá UNA pregunta "
            "cerrada de opción única para evaluar el factor indicado de la competencia indicada.\n"
            f"Datos: {json.dumps(payload, ensure_ascii=False)}\n"
            "Elegí la opción de respuesta más adecuada de la lista (por su nombre) y asigná una ponderación a CADA "
            "una de sus opciones: valores >= 0 que sumen exactamente 10 (la mejor respuesta recibe más puntos).\n"
            "Respondé SOLO un JSON con las claves: nombre_pregunta (título corto, máx 100), enunciado (máx 300), "
            "descripcion (máx 300), nombre_opcion_respuesta, ponderaciones (lista de {orden, ponderacion})."
        )
        return self._anthropic(prompt)

    # ------------------------------------------------------------------ CU009 (creación con GenAI)
    def generar_puesto(self, descripcion: str, empresa: str | None, competencias: list[dict]) -> dict:
        """Devuelve {nombre_puesto, descripcion, caracteristicas: [{codigo_competencia, ponderacion_minima_requerida}]}."""
        if settings.ia_mode == "mock":
            return self._mock_puesto(descripcion, competencias)
        payload = {"descripcion": descripcion, "empresa": empresa, "competencias_disponibles": competencias}
        if settings.ia_mode == "api":
            return self._post("/puestos", payload)
        prompt = (
            "Sos un especialista en selección de personal de TIC. A partir de la descripción de un puesto, proponé "
            "el nombre del puesto, una descripción formal (máx 300 caracteres) y las competencias requeridas, "
            "eligiendo SOLO entre las competencias disponibles, con una ponderación mínima requerida entre 0 y 10.\n"
            f"Datos: {json.dumps(payload, ensure_ascii=False)}\n"
            "Respondé SOLO un JSON con: nombre_puesto (máx 100), descripcion, caracteristicas "
            "(lista de {codigo_competencia, ponderacion_minima_requerida})."
        )
        return self._anthropic(prompt)

    # ------------------------------------------------------------------ transporte
    def _post(self, ruta: str, payload: dict) -> dict:
        if not settings.ia_base_url:
            raise ErrorServicioIA("IA_BASE_URL no configurada")
        try:
            r = httpx.post(settings.ia_base_url.rstrip("/") + ruta, json=payload, timeout=self.TIMEOUT,
                           headers={"Authorization": f"Bearer {settings.ia_api_key}"} if settings.ia_api_key else None)
            r.raise_for_status()
            return r.json()
        except (httpx.HTTPError, ValueError) as e:
            raise ErrorServicioIA(str(e)) from e

    def _anthropic(self, prompt: str) -> dict:
        if not settings.ia_api_key:
            raise ErrorServicioIA("IA_API_KEY no configurada")
        try:
            r = httpx.post(
                (settings.ia_base_url or "https://api.anthropic.com").rstrip("/") + "/v1/messages",
                headers={"x-api-key": settings.ia_api_key, "anthropic-version": "2023-06-01"},
                json={"model": settings.ia_model, "max_tokens": 1024, "messages": [{"role": "user", "content": prompt}]},
                timeout=self.TIMEOUT,
            )
            r.raise_for_status()
            texto = "".join(b.get("text", "") for b in r.json().get("content", []))
            m = re.search(r"\{.*\}", texto, re.S)
            return json.loads(m.group(0) if m else texto)
        except (httpx.HTTPError, ValueError, AttributeError) as e:
            raise ErrorServicioIA(str(e)) from e

    # ------------------------------------------------------------------ modo mock
    @staticmethod
    def _mock_pregunta(competencia: dict, factor: dict, opciones: list[dict]) -> dict:
        opcion = max(opciones, key=lambda o: len(o["items"]))
        n = random.randint(100, 999)
        valores = _ponderaciones_crecientes(len(opcion["items"]))
        return {
            "nombre_pregunta": f"{factor['nombre']} - SITUACION {n}",
            "enunciado": f"¿En qué medida aplica prácticas de {factor['nombre'].lower()} en su trabajo diario? (caso {n})",
            "descripcion": f"Pregunta generada para evaluar el factor {factor['nombre']} de la competencia {competencia['nombre']}.",
            "nombre_opcion_respuesta": opcion["nombre"],
            "ponderaciones": [{"orden": i["orden"], "ponderacion": v} for i, v in zip(opcion["items"], valores)],
        }

    @staticmethod
    def _mock_puesto(descripcion: str, competencias: list[dict]) -> dict:
        palabras = [p for p in re.findall(r"[A-Za-zÁÉÍÓÚÑáéíóúñ]+", descripcion) if len(p) > 3][:3]
        elegidas = competencias[: min(3, len(competencias))]
        return {
            "nombre_puesto": " ".join(palabras).upper() or "PUESTO GENERADO",
            "descripcion": descripcion[:300],
            "caracteristicas": [{"codigo_competencia": c["codigo"], "ponderacion_minima_requerida": 6} for c in elegidas],
        }
