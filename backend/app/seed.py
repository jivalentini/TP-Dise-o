"""Datos de prueba: python -m app.seed   (se puede correr más de una vez: solo agrega lo que falta)"""
import random
from datetime import date, datetime, timedelta

from sqlalchemy import select

from .dto import BloqueRespuestasDTO, RespuestaDTO
from .entidades import models as m
from .entidades.estados import EstadoCuestionario, EstadoEvaluacion, TipoCompetencia
from .gestores.evaluaciones import GestorEvaluaciones
from .infraestructura.database import Base, SessionLocal, engine

OPCIONES = {
    "VERDADERO - FALSO": ("Respuesta dicotómica", ["VERDADERO", "FALSO"]),
    "ESCALA DE CALIDAD": ("De malo a excelente", ["MALO", "REGULAR", "BUENO", "MUY BUENO", "EXCELENTE"]),
    "GRADO DE ACUERDO": ("Escala de acuerdo de 4 niveles", ["EN DESACUERDO", "PARCIALMENTE EN DESACUERDO",
                                                          "PARCIALMENTE DE ACUERDO", "DE ACUERDO"]),
}
PONDERACIONES = {"VERDADERO - FALSO": [10, 0], "ESCALA DE CALIDAD": [0, 0, 1, 2, 7], "GRADO DE ACUERDO": [0, 0, 2, 8]}

COMPETENCIAS = [
    ("COMP01", "GESTION DE PROYECTOS", "PLANIFICACION Y CONTROL DE PROYECTOS DE SOFTWARE", TipoCompetencia.TECNICA, [
        ("F01", "GESTION DEL ALCANCE", "DEFINICION Y CONTROL DEL ALCANCE", [
            ("WBS Y ALCANCE", "¿LA DESCOMPOSICION DE ESTRUCTURA DE TRABAJO (WBS) FORMA PARTE DE LA DEFINICION DEL ALCANCE?", "VERDADERO - FALSO"),
            ("LINEA BASE DE REQUERIMIENTOS", "¿CUANDO SE DEFINE UN ALCANCE, DEBE DEFINIRSE UNA LINEA BASE DE LOS REQUERIMIENTOS?", "VERDADERO - FALSO"),
            ("CONTROL DE CAMBIOS", "¿COMO EVALUA SU MANEJO DE SOLICITUDES DE CAMBIO DE ALCANCE?", "ESCALA DE CALIDAD"),
        ]),
        ("F02", "GESTION DEL TIEMPO", "PLANIFICACION DEL CRONOGRAMA", [
            ("DEPENDENCIA FIN A COMIENZO", "EN UN CRONOGRAMA, UNA ACTIVIDAD 'FIN A COMIENZO' NO PUEDE INICIAR HASTA QUE TERMINE SU PREDECESORA", "VERDADERO - FALSO"),
            ("VALOR GANADO", "¿LA METODOLOGIA DE VALOR GANADO PERMITE PREDECIR EL COSTO FINAL DE UN PROYECTO?", "VERDADERO - FALSO"),
            ("ESTIMACIONES", "¿COMO CALIFICARIA SUS ESTIMACIONES DE ESFUERZO EN PROYECTOS ANTERIORES?", "ESCALA DE CALIDAD"),
        ]),
    ]),
    ("COMP02", "LEALTAD", "COMPROMISO CON LA ORGANIZACION", TipoCompetencia.ACTITUDINAL, [
        ("F03", "CREDIBILIDAD", "CONFIANZA QUE GENERA EN EL EQUIPO", [
            ("HECHOS PROFESIONALES", "SOY DIGNO DE CONFIANZA PORQUE LO DEMUESTRO CON MIS HECHOS PROFESIONALES", "GRADO DE ACUERDO"),
            ("CONFIANZA DEL EQUIPO", "MIS COMPAÑEROS DE TRABAJO CONFIAN EN MI GRACIAS A MI DESEMPEÑO COTIDIANO", "GRADO DE ACUERDO"),
            ("RESGUARDO DE INFORMACION", "RESGUARDO LA INFORMACION DE MI PUESTO PARA EL MEJOR USO DE LA EMPRESA", "GRADO DE ACUERDO"),
        ]),
        ("F04", "COMPROMISO", "ASUNCION DE RESPONSABILIDADES", [
            ("PROYECTOS ESTRATEGICOS", "CUANDO ME ASIGNAN PROYECTOS ESTRATEGICOS ME HAGO CARGO DE ELLOS TOTALMENTE", "GRADO DE ACUERDO"),
            ("OBJETIVOS COLECTIVOS", "PARA MI EL LOGRO DE OBJETIVOS COLECTIVOS ES IMPORTANTE", "GRADO DE ACUERDO"),
            ("COMPROMISOS ASUMIDOS", "EN MIS ACTIVIDADES PROFESIONALES ASUMO TODOS LOS COMPROMISOS QUE CONTRAIGO", "GRADO DE ACUERDO"),
        ]),
    ]),
    ("COMP03", "PROGRAMACION PYTHON", "DESARROLLO DE SOFTWARE EN PYTHON", TipoCompetencia.TECNICA, [
        ("F05", "FUNDAMENTOS DEL LENGUAJE", "SINTAXIS Y TIPOS", [
            ("LISTAS MUTABLES", "EN PYTHON LAS LISTAS SON MUTABLES Y LAS TUPLAS INMUTABLES", "VERDADERO - FALSO"),
            ("DICCIONARIOS", "EN PYTHON 3.7+ LOS DICCIONARIOS CONSERVAN EL ORDEN DE INSERCION", "VERDADERO - FALSO"),
            ("GIL", "EL GIL IMPIDE QUE DOS HILOS EJECUTEN BYTECODE PYTHON EN PARALELO EN CPYTHON", "VERDADERO - FALSO"),
        ]),
        ("F06", "BUENAS PRACTICAS", "CALIDAD DEL CODIGO", [
            ("TESTING", "¿COMO CALIFICARIA SU PRACTICA DE ESCRIBIR TESTS AUTOMATIZADOS?", "ESCALA DE CALIDAD"),
            ("REVISION DE CODIGO", "¿COMO CALIFICARIA SU PARTICIPACION EN REVISIONES DE CODIGO?", "ESCALA DE CALIDAD"),
        ]),
    ]),
]

CANDIDATOS = [
    ("C0002", "20111222", "GOMEZ", "MARIA"), ("C0003", "30222333", "FERNANDEZ", "LUCAS"),
    ("C0004", "35444555", "LOPEZ", "SOFIA"), ("C0005", "28999000", "MARTINEZ", "DIEGO"),
    ("C0006", "33123456", "SANCHEZ", "VALENTINA"), ("C0007", "40111000", "ROMERO", "TOMAS"),
]


def _base(db):
    if db.scalar(select(m.Consultor).where(m.Consultor.username == "CONSULTOR")):
        return
    db.add(m.Consultor(legajo="L0001", username="CONSULTOR"))
    db.add(m.Competencia(codigo="COMP01", nombre="GESTION DE PROYECTOS", descripcion="Competencia técnica", tipo=TipoCompetencia.TECNICA))
    db.add(m.Puesto(codigo="P001", nombre_puesto="DESARROLLADOR BACKEND", descripcion="Servicios y APIs", empresa="MERCADOLIBRE"))
    db.add(m.CaracteristicaPuesto(puesto_codigo="P001", competencia_codigo="COMP01", ponderacion_minima_requerida=6))
    db.add(m.Candidato(nro_candidato="C0001", tipo_documento="DNI", nro_documento="12345678", apellido="PEREZ", nombre="JUAN"))
    evaluacion = m.Evaluacion(fecha_creacion=date.today(), estado=EstadoEvaluacion.ACTIVA, puesto_codigo="P001")
    evaluacion.cuestionarios.append(
        m.Cuestionario(estado=EstadoCuestionario.ACTIVO, clave_ingreso="AB12CD34", candidato_nro_candidato="C0001")
    )
    db.add(evaluacion)
    db.commit()


def _datos_basicos(db):
    if db.scalar(select(m.Factor).limit(1)):
        return False
    for nombre, (desc, items) in OPCIONES.items():
        if not db.get(m.OpcionRespuesta, nombre):
            o = m.OpcionRespuesta(nombre=nombre, descripcion=desc.upper())
            o.items = [m.ItemOpcion(orden=i, descripcion=d) for i, d in enumerate(items, start=1)]
            db.add(o)
    for cod, nombre, desc, tipo, factores in COMPETENCIAS:
        if not db.get(m.Competencia, cod):
            db.add(m.Competencia(codigo=cod, nombre=nombre, descripcion=desc, tipo=tipo))
        db.flush()
        for orden, (fcod, fnombre, fdesc, preguntas) in enumerate(factores, start=1):
            db.add(m.Factor(codigo=fcod, nombre=fnombre, descripcion=fdesc, nro_orden=orden, competencia_codigo=cod))
            db.flush()
            for pnombre, enunciado, opcion in preguntas:
                p = m.Pregunta(nombre_pregunta=pnombre, enunciado=enunciado, factor_codigo=fcod, opcion_respuesta_nombre=opcion)
                p.ponderaciones = [m.PonderacionItemPregunta(nombre_opcion_respuesta=opcion, orden=i, ponderacion=v)
                                   for i, v in enumerate(PONDERACIONES[opcion], start=1)]
                db.add(p)
    # Características del puesto P001 y un segundo puesto sin evaluaciones
    p001 = db.get(m.Puesto, "P001")
    actuales = {c.competencia_codigo for c in p001.caracteristicas}
    for cod, minimo in (("COMP01", 6), ("COMP02", 5), ("COMP03", 7)):
        if cod not in actuales:
            p001.caracteristicas.append(m.CaracteristicaPuesto(competencia_codigo=cod, ponderacion_minima_requerida=minimo))
    if not db.get(m.Puesto, "P002"):
        p002 = m.Puesto(codigo="P002", nombre_puesto="ANALISTA FUNCIONAL", descripcion="RELEVAMIENTO Y ANALISIS", empresa="TOYOTA")
        p002.caracteristicas = [m.CaracteristicaPuesto(competencia_codigo="COMP01", ponderacion_minima_requerida=5),
                                m.CaracteristicaPuesto(competencia_codigo="COMP02", ponderacion_minima_requerida=6)]
        db.add(p002)
    db.commit()
    return True


def _evaluacion_demo(db):
    """Evaluación ya rendida para probar CU007 / CU027 / CU028 (respuestas simuladas con el flujo real del CU026)."""
    if db.get(m.Candidato, "C0002"):
        return
    for nro, doc, ape, nom in CANDIDATOS:
        db.add(m.Candidato(nro_candidato=nro, tipo_documento="DNI", nro_documento=doc, apellido=ape, nombre=nom,
                           fecha_nacimiento=date(1995, 1, 1), genero="M", nacionalidad="ARGENTINA", email=f"{nom.lower()}@mail.com"))
    ev = m.Evaluacion(fecha_creacion=date.today() - timedelta(days=3), estado=EstadoEvaluacion.ACTIVA, puesto_codigo="P001")
    db.add(ev)
    db.flush()
    cuestionarios = {}
    for i, (nro, *_rest) in enumerate(CANDIDATOS, start=1):
        c = m.Cuestionario(estado=EstadoCuestionario.ACTIVO, clave_ingreso=f"CLAVE00{i}", candidato_nro_candidato=nro,
                           evaluacion_id=ev.id_evaluacion, fecha_creacion=datetime.now() - timedelta(days=3))
        db.add(c)
        cuestionarios[nro] = c
    db.commit()

    gestor = GestorEvaluaciones(db)
    rnd = random.Random(2026)
    # nivel = probabilidad de elegir la mejor opción (define quién supera los mínimos)
    for nro, nivel, completar in (("C0002", 0.95, True), ("C0003", 0.8, True), ("C0004", 0.5, True), ("C0005", 0.2, True),
                                  ("C0006", 0.7, False)):
        c = cuestionarios[nro]
        gestor.obtener_cuestionario_para_completar(c.id_cuestionario, registrar_acceso=True)
        estado = gestor.armar_cuestionario(c.id_cuestionario)
        while estado.accion == "BLOQUE":
            respuestas = []
            for p in estado.bloque.preguntas:
                mejor = max(p.opciones, key=lambda o: o.orden if len(p.opciones) > 2 else -o.orden)
                elegida = mejor if rnd.random() < nivel else rnd.choice(p.opciones)
                respuestas.append(RespuestaDTO(id_pregunta=p.id_pregunta, orden_opcion_seleccionada=elegida.orden))
            estado = gestor.registrar_respuesta_bloque(
                c.id_cuestionario, BloqueRespuestasDTO(id_cuestionario=str(c.id_cuestionario), nro_bloque=estado.bloque.nro_bloque, respuestas=respuestas))
            if not completar:  # deja un bloque respondido y lo marca Incompleto (como haría el CU032)
                db.refresh(c)
                c.estado, c.fecha_fin = EstadoCuestionario.INCOMPLETO, datetime.now()
                db.commit()
                break
    c = cuestionarios["C0007"]
    c.estado, c.fecha_fin = EstadoCuestionario.SIN_CONTESTAR, datetime.now()
    db.commit()


if __name__ == "__main__":
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        _base(db)
        _datos_basicos(db)
        _evaluacion_demo(db)
    print("Listo.\n  Consultor: CONSULTOR / consultor123 (AUTH_MODE=mock)\n"
          "  Candidato: DNI 12345678 / clave AB12CD34 (cuestionario Activo para probar el CU026)")
