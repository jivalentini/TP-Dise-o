"""Pruebas de los CU007–CU033 contra una BD SQLite temporal.

    cd backend
    pip install pytest
    python -m pytest -q
"""
import os
import tempfile

_db = os.path.join(tempfile.mkdtemp(), "test.db")
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL", f"sqlite:///{_db}")  # BD vacía (p. ej. Postgres de prueba)
os.environ["BATCH_INTERVALO_MINUTOS"] = "0"
os.environ["IA_MODE"] = "mock"
os.environ["AUTH_MODE"] = "mock"

from datetime import datetime, timedelta  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import seed  # noqa: E402
from app.entidades import models as m  # noqa: E402
from app.infraestructura.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="module")
def client():
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed._base(db)
        seed._datos_basicos(db)
        seed._evaluacion_demo(db)
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def h(client):
    r = client.post("/api/auth/consultor", json={"username": "consultor", "password": "consultor123"})
    return {"Authorization": f"Bearer {r.json()['token']}"}


def auditorias(accion):
    with SessionLocal() as db:
        return db.query(m.RegistroAuditoria).filter_by(accion=accion).count()


# ------------------------------------------------------------------ seguridad
def test_requiere_consultor(client):
    assert client.get("/api/competencias").status_code == 401


# ------------------------------------------------------------------ CU012–015
def test_competencias(client, h):
    assert len(client.get("/api/competencias", headers=h).json()) == 3  # sin criterio: todas
    r = client.post("/api/competencias", headers=h, json={"codigo": "", "nombre": "", "descripcion": "", "tipo": ""})
    assert r.status_code == 400 and len(r.json()["errores"]) == 4  # TODAS las omisiones
    r = client.post("/api/competencias", headers=h, json={"codigo": "c9", "nombre": "liderazgo", "descripcion": "x", "tipo": "Actitudinal"})
    assert r.status_code == 201 and r.json()["nombre"] == "LIDERAZGO"  # mayúsculas
    r = client.post("/api/competencias", headers=h, json={"codigo": "C9", "nombre": "LIDERAZGO", "descripcion": "x", "tipo": "Actitudinal"})
    assert r.status_code == 409 and "código C9 y el nombre LIDERAZGO" in r.json()["detail"]
    r = client.put("/api/competencias/C9", headers=h, json={"codigo": "C9", "nombre": "LEALTAD", "descripcion": "x", "tipo": "Actitudinal"})
    assert r.status_code == 409 and r.json()["campo"] == "nombre"
    assert client.get("/api/competencias/COMP01/puede-eliminar", headers=h).json()["puede"] is False  # en uso
    assert client.delete("/api/competencias/COMP01", headers=h).status_code == 409
    assert client.get("/api/competencias/C9/puede-eliminar", headers=h).json()["puede"] is True
    assert "han sido eliminados" in client.delete("/api/competencias/C9", headers=h).json()["mensaje"]
    assert auditorias("BAJA_COMPETENCIA") == 1
    assert client.get("/api/competencias?nombre=lider", headers=h).json() == []


# ------------------------------------------------------------------ CU016–019
def test_factores(client, h):
    r = client.get("/api/factores?nombre_competencia=lealt", headers=h).json()
    assert [f["nombre"] for f in r] == ["COMPROMISO", "CREDIBILIDAD"]  # ordenado por nombre
    ocupados = client.get("/api/factores/ordenes/COMP02", headers=h).json()
    assert [o["nro_orden"] for o in ocupados] == [1, 2]
    base = {"codigo": "F99", "nombre": "RESPONSABILIDAD", "descripcion": "D", "codigo_competencia": "COMP02", "nro_orden": 2}
    r = client.post("/api/factores", headers=h, json=base)
    assert r.status_code == 409 and r.json()["campo"] == "nro_orden"
    assert client.post("/api/factores", headers=h, json={**base, "nro_orden": 3}).status_code == 201
    r = client.put("/api/factores/F99", headers=h, json={**base, "nombre": "COMPROMISO", "nro_orden": 3})
    assert r.status_code == 409
    # baja: elimina lógicamente sus preguntas y audita cada una
    client.post("/api/preguntas", headers=h, json={
        "nombre_pregunta": "P1", "enunciado": "E1", "codigo_competencia": "COMP02", "codigo_factor": "F99",
        "nombre_opcion_respuesta": "VERDADERO - FALSO", "ponderaciones": [{"orden": 1, "descripcion": "", "ponderacion": 10}, {"orden": 2, "descripcion": "", "ponderacion": 0}]})
    antes = auditorias("BAJA_PREGUNTA")
    assert "y sus preguntas" in client.get("/api/factores/F99/puede-eliminar", headers=h).json()["mensaje"]
    assert client.delete("/api/factores/F99", headers=h).status_code == 200
    assert auditorias("BAJA_PREGUNTA") == antes + 1 and auditorias("BAJA_FACTOR") == 1
    assert 3 not in [o["nro_orden"] for o in client.get("/api/factores/ordenes/COMP02", headers=h).json()]  # orden liberado


# ------------------------------------------------------------------ CU024, CU029–031
def test_opciones_respuesta(client, h):
    assert len(client.get("/api/opciones-respuesta", headers=h).json()) == 3
    r = client.post("/api/opciones-respuesta", headers=h, json={"nombre": "SI NO", "descripcion": "D",
                                                              "items": [{"orden": 1, "descripcion": "SI"}, {"orden": 3, "descripcion": "NO"}]})
    assert r.status_code == 400 and "consecutivo" in r.json()["detail"]
    r = client.post("/api/opciones-respuesta", headers=h, json={"nombre": "SI NO", "descripcion": "D",
                                                              "items": [{"orden": 1, "descripcion": "SI"}, {"orden": 2, "descripcion": "si"}]})
    assert "más de una vez" in r.json()["detail"]
    ok = {"nombre": "si no", "descripcion": "d", "items": [{"orden": 1, "descripcion": "si"}, {"orden": 2, "descripcion": "no"}]}
    assert client.post("/api/opciones-respuesta", headers=h, json=ok).status_code == 201
    assert client.post("/api/opciones-respuesta", headers=h, json=ok).status_code == 409
    r = client.put("/api/opciones-respuesta/SI NO", headers=h, json={**ok, "items": [{"orden": 2, "descripcion": "si"}, {"orden": 1, "descripcion": "no"}]})
    assert r.status_code == 200 and [i["descripcion"] for i in r.json()["items"]] == ["NO", "SI"]
    r = client.put("/api/opciones-respuesta/SI NO", headers=h, json={**ok, "items": ok["items"][:1]})
    assert r.status_code == 400  # no se pueden quitar opciones
    assert client.get("/api/opciones-respuesta/ESCALA DE CALIDAD/puede-eliminar", headers=h).json()["puede"] is False
    assert client.delete("/api/opciones-respuesta/SI NO", headers=h).status_code == 200
    assert auditorias("BAJA_OPCION_RESPUESTA") == 1


# ------------------------------------------------------------------ CU020–023, CU033
def test_preguntas(client, h):
    assert client.get("/api/preguntas", headers=h).status_code == 400  # al menos un criterio
    r = client.get("/api/preguntas?nombre_factor=alcance", headers=h).json()
    assert len(r) == 3 and r[0]["ponderaciones"][0]["descripcion"]
    pond = lambda *v: [{"orden": i, "descripcion": "", "ponderacion": x} for i, x in enumerate(v, start=1)]  # noqa: E731
    base = {"nombre_pregunta": "nueva", "enunciado": "enunciado nuevo", "codigo_competencia": "COMP01", "codigo_factor": "F01",
            "nombre_opcion_respuesta": "ESCALA DE CALIDAD", "ponderaciones": pond(0, 1, 2, 3, 4)}
    r = client.post("/api/preguntas", headers=h, json={**base, "nombre_pregunta": "", "enunciado": ""})
    assert len(r.json()["errores"]) == 2
    r = client.post("/api/preguntas", headers=h, json={**base, "enunciado": "x" * 301})
    assert "longitud máxima" in r.json()["errores"][0]
    assert "sumar 10" in client.post("/api/preguntas", headers=h, json={**base, "ponderaciones": pond(1, 1, 1, 1, 1)}).json()["detail"]
    assert "positivas" in client.post("/api/preguntas", headers=h, json={**base, "ponderaciones": pond(-1, 1, 2, 3, 5)}).json()["detail"]
    assert "no pertenece" in client.post("/api/preguntas", headers=h, json={**base, "codigo_factor": "F03"}).json()["detail"]
    r = client.post("/api/preguntas", headers=h, json=base)
    assert r.status_code == 201
    pid = r.json()["id_pregunta"]
    r = client.post("/api/preguntas", headers=h, json={**base, "nombre_pregunta": "otra"})
    assert r.status_code == 409 and "ENUNCIADO" in r.json()["detail"]
    r = client.put(f"/api/preguntas/{pid}", headers=h, json={**base, "codigo_factor": "F03", "nombre_opcion_respuesta": "VERDADERO - FALSO",
                                                            "ponderaciones": pond(7, 3)})
    assert r.status_code == 200 and r.json()["codigo_factor"] == "F01" and len(r.json()["ponderaciones"]) == 2  # factor de solo lectura
    assert client.delete(f"/api/preguntas/{pid}", headers=h).status_code == 200
    assert client.get(f"/api/preguntas/{pid}", headers=h).status_code == 404
    # CU033
    assert len(client.post("/api/preguntas/generar-ia", headers=h, json={}).json()["errores"]) == 2
    r = client.post("/api/preguntas/generar-ia", headers=h, json={"codigo_competencia": "COMP01", "codigo_factor": "F02"}).json()
    assert r["enunciado"] and abs(sum(p["ponderacion"] for p in r["ponderaciones"]) - 10) < 0.01
    assert client.post("/api/preguntas", headers=h, json=r).status_code == 201  # lo generado se puede guardar (vuelve al CU021)


# ------------------------------------------------------------------ CU008–011
def test_puestos(client, h):
    assert client.get("/api/puestos", headers=h).status_code == 400
    base = {"codigo": "p3", "nombre_puesto": "qa tester", "descripcion": "pruebas", "empresa": "globant",
            "caracteristicas": [{"codigo_competencia": "COMP01", "ponderacion_minima_requerida": 5}]}
    r = client.post("/api/puestos", headers=h, json={**base, "caracteristicas": [
        {"codigo_competencia": "COMP01", "ponderacion_minima_requerida": 11}, {"codigo_competencia": "COMP01", "ponderacion_minima_requerida": 2}]})
    assert len(r.json()["errores"]) == 2
    assert client.post("/api/puestos", headers=h, json=base).status_code == 201
    assert client.get("/api/puestos?empresa=glob", headers=h).json()[0]["codigo"] == "P3"
    r = client.put("/api/puestos/P001", headers=h, json={**base, "nombre_puesto": "DESARROLLADOR BACKEND"})
    assert r.status_code == 400 and "cuestionarios" in r.json()["detail"]  # 2.C
    assert client.get("/api/puestos/P001/puede-eliminar", headers=h).json()["puede"] is False
    assert client.delete("/api/puestos/P3", headers=h).status_code == 200
    r = client.post("/api/puestos/generar-ia", headers=h, json={"descripcion": "desarrollador python senior", "empresa": "acme"}).json()
    assert r["nombre_puesto"] and r["caracteristicas"]


# ------------------------------------------------------------------ CU026
def test_completar_cuestionario(client):
    r = client.post("/api/auth/candidato", json={"tipo_documento": "DNI", "nro_documento": "12345678", "clave": "AB12CD34"})
    hc = {"Authorization": f"Bearer {r.json()['token']}"}
    e = client.post("/api/cuestionario/ingresar", headers=hc).json()
    assert e["accion"] == "INSTRUCCIONES" and e["instrucciones"]
    e = client.post("/api/cuestionario/comenzar", headers=hc).json()
    assert e["accion"] == "BLOQUE" and e["estado"] == "En Proceso" and e["bloque"]["nro_bloque"] == 1
    total = e["bloque"]["total_bloques"]
    # 6.A: no respondió todas
    r = client.post("/api/cuestionario/bloque", headers=hc, json={"id_cuestionario": "1", "nro_bloque": 1, "respuestas": []})
    assert r.status_code == 400 and len(r.json()["errores"]) == len(e["bloque"]["preguntas"])
    primero = e["bloque"]
    resp = lambda b: [{"id_pregunta": p["id_pregunta"], "orden_opcion_seleccionada": 1} for p in b["preguntas"]]  # noqa: E731
    e = client.post("/api/cuestionario/bloque", headers=hc, json={"id_cuestionario": "1", "nro_bloque": 1, "respuestas": resp(primero)}).json()
    # 1.C: reingresa y continúa en el bloque pendiente, idéntico
    e2 = client.post("/api/cuestionario/ingresar", headers=hc).json()
    assert e2["bloque"] == e["bloque"]
    # no puede volver al bloque ya respondido
    assert client.post("/api/cuestionario/bloque", headers=hc, json={"id_cuestionario": "1", "nro_bloque": 1, "respuestas": resp(primero)}).status_code == 400
    while e["accion"] == "BLOQUE":
        e = client.post("/api/cuestionario/bloque", headers=hc, json={"id_cuestionario": "1", "nro_bloque": e["bloque"]["nro_bloque"], "respuestas": resp(e["bloque"])}).json()
    assert e["estado"] == "Completo" and total >= 2
    with SessionLocal() as db:
        c = db.get(m.Cuestionario, 1)
        assert c.fecha_fin and len(c.puntajes_competencia) == 3 and len(c.puntajes_factor) == 6


def test_maximo_accesos(client):
    with SessionLocal() as db:
        c = db.query(m.Cuestionario).filter_by(candidato_nro_candidato="C0007").one()
        c.estado, c.fecha_fin, c.cantidad_accesos = "Activo", None, 5
        db.commit()
    r = client.post("/api/auth/candidato", json={"tipo_documento": "DNI", "nro_documento": "40111000", "clave": "CLAVE006"})
    hc = {"Authorization": f"Bearer {r.json()['token']}"}
    e = client.post("/api/cuestionario/ingresar", headers=hc).json()
    assert e["accion"] == "FINALIZADO" and e["estado"] == "Incompleto"


# ------------------------------------------------------------------ CU027 / CU028 / CU007
def test_reporte_comparativo(client, h):
    funciones = client.get("/api/reporte-comparativo/funciones?nombre_funcion=backend", headers=h).json()
    candidatos = client.get(f"/api/funciones/{funciones[0]['codigo']}/candidatos-evaluados", headers=h).json()
    assert {c["nro_candidato"] for c in candidatos} >= {"C0002", "C0003", "C0004", "C0005"}
    assert client.get("/api/reporte-comparativo?codigo_puesto=P001", headers=h).status_code == 400  # 6.A
    r = client.get("/api/reporte-comparativo?codigo_puesto=P001&nro_candidato=C0002", headers=h).json()
    assert [i["nombre_competencia"] for i in r["items"]] == ["GESTION DE PROYECTOS", "LEALTAD", "PROGRAMACION PYTHON"]


def test_orden_merito(client, h):
    r = client.get("/api/orden-merito/puestos?nombre_puesto=a", headers=h).json()
    p001 = next(p for p in r if p["codigo"] == "P001")
    assert p001["cantidad_candidatos"] == 7 and p001["cantidad_evaluaciones_completas"] >= 4
    assert client.get("/api/orden-merito/puestos/P002/evaluaciones", headers=h).status_code == 400  # 6.A
    om = client.post("/api/orden-merito", headers=h, json={"codigo_puesto": "P001"}).json()  # TODAS
    puntajes = [i["puntaje_total"] for i in om["items"]]
    assert puntajes == sorted(puntajes, reverse=True) and all(i["supera_minimos"] for i in om["items"])
    assert all(not i["supera_minimos"] for i in om["no_alcanzan_minimos"])
    assert "Incompleto" in om["otros_por_estado"] and om["otros_por_estado"]["Incompleto"][0]["puntaje_total"] is None
    evs = client.get("/api/orden-merito/puestos/P001/evaluaciones", headers=h).json()
    om1 = client.post("/api/orden-merito", headers=h, json={"codigo_puesto": "P001", "evaluaciones": [evs[-1]["id_evaluacion"]]}).json()
    assert om1["evaluaciones"] == [evs[-1]["id_evaluacion"]]


def test_exportar_resultados(client, h):
    assert client.get("/api/exportacion/funciones", headers=h).status_code == 400  # al menos un filtro
    hoy = datetime.now().date()
    f = client.get(f"/api/exportacion/funciones?fecha_desde={hoy - timedelta(days=1)}", headers=h).json()
    assert [x["codigo"] for x in f] == ["P001"]
    assert client.get(f"/api/exportacion/funciones?fecha_hasta={hoy - timedelta(days=5)}", headers=h).json() == []
    assert client.get("/api/exportacion/csv", headers=h).status_code == 400  # 6.A
    r = client.get("/api/exportacion/csv?codigo_puesto=P001", headers=h)
    lineas = r.content.decode("utf-8-sig").strip().split("\r\n")
    assert lineas[0].startswith("Nro candidato;Apellido;Nombre;Tipo documento;Nro documento;Código Competencia;Resultado")
    assert len(lineas) - 1 == 3 * 5  # 5 completos x 3 competencias
    assert r.headers["x-nombre-archivo"].endswith("-MERCADOLIBRE-DESARROLLADOR%20BACKEND.csv")


# ------------------------------------------------------------------ CU032
def test_proceso_batch(client, h):
    with SessionLocal() as db:
        ev = db.query(m.Evaluacion).first()
        db.add(m.Candidato(nro_candidato="C0100", tipo_documento="DNI", nro_documento="1", apellido="A", nombre="B"))
        db.add(m.Candidato(nro_candidato="C0101", tipo_documento="DNI", nro_documento="2", apellido="A", nombre="B"))
        db.add(m.Cuestionario(estado="Activo", clave_ingreso="X", candidato_nro_candidato="C0100", evaluacion_id=ev.id_evaluacion,
                              fecha_creacion=datetime.now() - timedelta(days=30)))
        db.add(m.Cuestionario(estado="En Proceso", clave_ingreso="Y", candidato_nro_candidato="C0101", evaluacion_id=ev.id_evaluacion,
                              fecha_inicio=datetime.now() - timedelta(days=1)))
        db.commit()
    r = client.post("/api/proceso-batch/finalizar-cuestionarios", headers=h).json()
    assert r == {"incompletos": 1, "sin_contestar": 1}
    assert auditorias("INICIO_EJECUCION") == 1 and auditorias("FIN_EJECUCION") == 1
