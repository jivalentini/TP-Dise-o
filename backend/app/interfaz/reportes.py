"""CU027 – Reporte comparativo, CU028 – Orden de mérito, CU007 – Exportar resultados, CU032 – ejecución manual."""
from datetime import date
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from ..dto import (CandidatoEvaluadoDTO, EvaluacionDTO, ExportacionCriteriosDTO, MensajeDTO, OrdenDeMeritoDTO,
                   OrdenMeritoSolicitudDTO, PuestoCriteriosDTO, PuestoDTO, PuestoResumenDTO, ReporteComparativoDTO)
from ..gestores.evaluaciones import GestorEvaluaciones
from ..gestores.proceso_batch import ProcesoBatchFinalizacionCuestionarios
from ..gestores.puestos import GestorPuestos
from ..infraestructura.database import get_db
from ..infraestructura.impresora import Impresora, ImpresoraNoDisponible
from .deps import consultor

router = APIRouter(prefix="/api", dependencies=[Depends(consultor)])


# ---------------------------------------------------------------- CU027
@router.get("/reporte-comparativo/funciones", response_model=list[PuestoDTO], tags=["CU027 Reporte comparativo"])
def buscar_funciones(nombre_funcion: str | None = None, empresa: str | None = None, db: Session = Depends(get_db)):
    return GestorPuestos(db).buscar_puesto(PuestoCriteriosDTO(nombre_puesto=nombre_funcion, empresa=empresa), requerido=False)


@router.get("/funciones/{codigo}/candidatos-evaluados", response_model=list[CandidatoEvaluadoDTO], tags=["CU027 Reporte comparativo", "CU007 Exportar resultados"])
def candidatos_evaluados(codigo: str, fecha_desde: date | None = None, fecha_hasta: date | None = None, db: Session = Depends(get_db)):
    return GestorEvaluaciones(db).candidatos_evaluados(codigo, fecha_desde, fecha_hasta)


@router.get("/reporte-comparativo", response_model=ReporteComparativoDTO, tags=["CU027 Reporte comparativo"])
def reporte_comparativo(codigo_puesto: str, nro_candidato: str | None = None, db: Session = Depends(get_db)):
    return GestorEvaluaciones(db).emitir_reporte_comparativo(nro_candidato or "", codigo_puesto)


# ---------------------------------------------------------------- CU028
@router.get("/orden-merito/puestos", response_model=list[PuestoResumenDTO], tags=["CU028 Orden de mérito"])
def buscar_puestos_con_resumen(codigo: str | None = None, nombre_puesto: str | None = None, empresa: str | None = None,
                               db: Session = Depends(get_db)):
    return GestorPuestos(db).buscar_puesto_con_resumen(PuestoCriteriosDTO(codigo=codigo, nombre_puesto=nombre_puesto, empresa=empresa))


@router.get("/orden-merito/puestos/{codigo}/evaluaciones", response_model=list[EvaluacionDTO], tags=["CU028 Orden de mérito"])
def evaluaciones(codigo: str, db: Session = Depends(get_db)):
    return GestorEvaluaciones(db).listar_evaluaciones(codigo)


@router.post("/orden-merito", response_model=OrdenDeMeritoDTO, tags=["CU028 Orden de mérito"])
def emitir_orden_merito(solicitud: OrdenMeritoSolicitudDTO, db: Session = Depends(get_db)):
    return GestorEvaluaciones(db).generar_orden_merito(solicitud.codigo_puesto, solicitud.evaluaciones)


@router.get("/impresora", tags=["CU028 Orden de mérito"])
def impresora_disponible():
    return {"disponible": Impresora().disponible()}


@router.post("/orden-merito/imprimir", response_model=MensajeDTO, tags=["CU028 Orden de mérito"])
def imprimir_orden_merito(solicitud: OrdenMeritoSolicitudDTO, db: Session = Depends(get_db)):
    om = GestorEvaluaciones(db).generar_orden_merito(solicitud.codigo_puesto, solicitud.evaluaciones)
    lineas = [f"ORDEN DE MERITO - {om.nombre_puesto} ({om.empresa}) - {om.fecha_generacion:%d/%m/%Y}", ""]
    for i in om.items + om.no_alcanzan_minimos:
        lineas.append(f"{i.posicion:>3}  {i.tipo_documento} {i.nro_documento:<12} {i.apellido}, {i.nombre}  "
                      f"{i.puntaje_total:.2f}{'' if i.supera_minimos else '  (no alcanza minimos)'}")
    for estado, items in om.otros_por_estado.items():
        lineas += ["", estado.upper()] + [f"     {i.tipo_documento} {i.nro_documento:<12} {i.apellido}, {i.nombre}" for i in items]
    try:
        Impresora().imprimir("\n".join(lineas).encode(), f"Orden de merito {om.nombre_puesto}")
    except ImpresoraNoDisponible:
        raise HTTPException(status_code=503, detail="La impresora no está disponible.")
    return MensajeDTO(mensaje="El listado fue enviado a la impresora.")


# ---------------------------------------------------------------- CU007
@router.get("/exportacion/funciones", response_model=list[PuestoDTO], tags=["CU007 Exportar resultados"])
def buscar_funciones_exportacion(nombre_funcion: str | None = None, empresa: str | None = None, fecha_desde: date | None = None,
                                 fecha_hasta: date | None = None, db: Session = Depends(get_db)):
    criterios = ExportacionCriteriosDTO(nombre_funcion=nombre_funcion, empresa=empresa, fecha_desde=fecha_desde, fecha_hasta=fecha_hasta)
    return GestorEvaluaciones(db).buscar_funciones_exportacion(criterios)


@router.get("/exportacion/csv", tags=["CU007 Exportar resultados"])
def exportar_csv(codigo_puesto: str | None = None, fecha_desde: date | None = None, fecha_hasta: date | None = None,
                 db: Session = Depends(get_db)):
    gestor = GestorEvaluaciones(db)
    resultados = gestor.exportar_resultados(ExportacionCriteriosDTO(fecha_desde=fecha_desde, fecha_hasta=fecha_hasta), codigo_puesto)
    nombre, contenido = gestor.armar_csv_resultados(codigo_puesto, resultados)
    return Response(content="﻿" + contenido, media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(nombre)}", "X-Nombre-Archivo": quote(nombre),
                             "Access-Control-Expose-Headers": "X-Nombre-Archivo"})


# ---------------------------------------------------------------- CU032 (ejecución manual)
@router.post("/proceso-batch/finalizar-cuestionarios", tags=["CU032 Finalizar cuestionarios"])
def ejecutar_batch():
    return ProcesoBatchFinalizacionCuestionarios().ejecutar()
