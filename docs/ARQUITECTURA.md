# Arquitectura y mapa de las entregas

## Capas (diagrama de despliegue → paquetes `backend/app`)
| Despliegue | Código |
|---|---|
| Capa de Interfaz (páginas / controladores web) | `interfaz/` (routers FastAPI) + `frontend/` (React) |
| Capa de Negocio (Gestores) | `gestores/` |
| Entidades (DER / diagrama de clases) | `entidades/models.py`, `entidades/estados.py` |
| Capa de Datos (DAOs) | `dao/` (la sesión se inyecta; el commit lo hace el Gestor) |
| DTO | `dto/` |
| Servidor LDAP (389/636) | `infraestructura/ldap_client.py` (`LDAP_SERVER=ldaps://…:636`) |
| Servicio de IA (HTTPS/REST) | `infraestructura/ia_client.py` (CU021/033 y CU009) – `IA_MODE=mock/api/anthropic` |
| Sistema de Candidatos y CV (HTTPS/REST) | `infraestructura/sistema_candidatos_client.py` (CU006) |
| Impresora (IPP) | `infraestructura/impresora.py` (CU028, vía `lp`/CUPS; sin cola configurada imprime el navegador) |
| Proceso batch (CU032) | `gestores/proceso_batch.py` – tarea periódica en `main.py` y `python -m app.batch` |
| BD (JDBC en el diseño) | PostgreSQL vía psycopg (`infraestructura/database.py`) |

HTTPS: en producción se termina TLS en un proxy inverso (nginx/Caddy) delante de FastAPI y del frontend.

## Estado
- **Implementado:** CU001 y CU007 a CU033 excepto CU025 (gestores, DAOs, routers en `interfaz/` y pantallas en `frontend/src/pages`).
- **Pendientes (`pendiente("CUxxx")`):** CU006 (`GestorCandidatos.importar_candidatos`, `CandidatoDAO.insertar/actualizar`) y
  CU025 (`GestorEvaluaciones.crear_evaluacion / exportar_claves / validar_competencias_evaluables / generar_clave_aleatoria`,
  `EvaluacionDAO.insertar`, `CuestionarioDAO.insertar`, `CandidatoDAO.buscar`, `GestorCandidatos.buscar_candidato / tiene_cuestionario_activo`).
- **Pruebas:** `backend/tests/test_casos_de_uso.py` (un test por CU, flujos principales y alternativos).

## Mapa CU → código
| CU | Gestor | Router (`/api/...`) | Pantalla |
|---|---|---|---|
| 007 Exportar resultados | `GestorEvaluaciones.buscar_funciones_exportacion / exportar_resultados / armar_csv_resultados` | `exportacion/*` | `ExportarResultados.jsx` |
| 008–011 Puestos (+ GenAI) | `GestorPuestos` | `puestos` | `Puestos.jsx` |
| 012–015 Competencias | `GestorCompetencias` | `competencias` | `Competencias.jsx` |
| 016–019 Factores | `GestorFactores` | `factores` | `Factores.jsx` |
| 020–023 Preguntas, 033 IA | `GestorPreguntas` | `preguntas`, `preguntas/generar-ia` | `Preguntas.jsx` |
| 024, 029–031 Opciones de respuesta | `GestorOpcionesRespuesta` | `opciones-respuesta` | `OpcionesRespuesta.jsx` |
| 026 Completar cuestionario | `GestorEvaluaciones.obtener_cuestionario_para_completar / armar_cuestionario / registrar_respuesta_bloque / calcular_resultados_cuestionario` + `Cuestionario.calcular_puntaje()` | `cuestionario/*` | `Cuestionario.jsx` |
| 027 Reporte comparativo | `GestorEvaluaciones.candidatos_evaluados / emitir_reporte_comparativo` | `reporte-comparativo*` | `ReporteComparativo.jsx` |
| 028 Orden de mérito | `GestorPuestos.buscar_puesto_con_resumen`, `GestorEvaluaciones.listar_evaluaciones / generar_orden_merito` | `orden-merito/*` | `OrdenMerito.jsx` |
| 032 Finalizar cuestionarios | `ProcesoBatchFinalizacionCuestionarios.ejecutar` | `proceso-batch/finalizar-cuestionarios` | — (actor Sistema) |

## Diferencias entre las entregas (para resolver en el próximo ajuste)
1. **Baja lógica**: el DER no tiene `eliminado` en Puesto, Competencia, Factor, Pregunta ni OpcionRespuesta, pero los CU011/015/019/023/031 la exigen → agregado.
2. **`Cuestionario.fechaCreacion`**: el diagrama de secuencia del CU026 lo usa (tiempo máximo en estado Activo) y no está en el DER → agregado.
3. **CU026** usa `BloqueCuestionario` y `RepositorioConfiguracionDAO`, que no están en el diagrama de clases (el DER maneja los bloques con `PREGUNTA_CUESTIONARIO.numeroBloque`).
4. **`GestorAutenticacion`** (CU001) no figura en el diagrama de clases.
5. **`claveIngreso`** se guarda en texto plano porque `exportarClaves` (CU025) la lee de la BD para el Excel.
6. Longitudes: CU008 define código de 10 y nombre de 300; CU009 define 50 y 100. Se usó CU009.
7. **Repositorio de configuraciones** (CU026): tabla `parametro_configuracion` (clave/valor, fuera del DER). Si un parámetro
   no está cargado se usan los valores por defecto de `RepositorioConfiguracionDAO` (tiempos en minutos, 4 preguntas por bloque, 5 accesos).
8. **Fecha de cambio de estado**: al pasar a Completo / Incompleto / Sin Contestar se guarda en `Cuestionario.fechaFin`
   (el DER no tiene otro atributo para "fecha y hora en que fue puesto en ese estado").
9. **Accesos (CU026)**: se cuentan una vez por autenticación del candidato (`POST /api/cuestionario/ingresar`).
10. **Orden de las preguntas** dentro de cada bloque: aleatorio con semilla fija por cuestionario y bloque, así al volver a
    ingresar se presenta idéntico sin agregar columnas al DER (los bloques ya están en `PREGUNTA_CUESTIONARIO.numeroBloque`).
11. **Baja de factor (CU019)**: además de la baja lógica, su `nroOrden` pasa a negativo para liberar el número dentro de la
    competencia (el par competencia + nroOrden es único en el DER).
12. **CU030**: el orden de visualización de una opción de respuesta solo puede cambiarse si todavía no está asociada a preguntas
    (el orden es parte de la PK de `ITEM_OPCION` y lo referencian las ponderaciones y respuestas).
13. **Puntaje del orden de mérito (CU028)**: promedio de los puntajes obtenidos en las competencias del puesto; "supera los
    mínimos" = obtuvo ≥ ponderación mínima en TODAS las competencias. Se persiste un `OrdenDeMerito` por evaluación.
14. **CU007** genera el archivo CSV (no usa el `SistemaCandidatosClient`, que queda para el CU006).
15. **DTOs agregados** (no están en el diagrama de clases): `PreguntaCuestionarioDTO`, `EstadoCuestionarioDTO`,
    `CandidatoEvaluadoDTO`, `EvaluacionDTO`, `OrdenMeritoSolicitudDTO`, `GenerarPreguntaIADTO`, `GenerarPuestoIADTO`,
    `MensajeDTO`, `PuedeEliminarDTO`.

## Secuencias para implementar (resumen)
- **CU020**: `GestorPreguntas.buscarPregunta(PreguntaCriteriosDTO)` → `PreguntaDAO.buscar` → `List<PreguntaDTO>`; Nuevo/Modificar/Eliminar navegan a CU021/022/023 y luego actualizan la grilla.
- **CU021**: al elegir Competencia → `GestorFactores.buscarFactor`; Aceptar → `GestorPreguntas.darAltaPregunta(PreguntaDTO)` → `PreguntaDAO.existePregunta(nombre, enunciado, competencia, factor)`; si no existe → `insertar`.
- **CU023**: confirmación → `darBajaPregunta` → `PreguntaDAO.eliminar` (baja lógica) → `RegistroAuditoriaDAO.insertar(fecha, hora, usuario, "BAJA_PREGUNTA", "Pregunta", id)`.
- **CU025**: `buscarCandidato` → por candidato `tieneCuestionarioActivo` → `buscarPuesto` → `validarCompetenciasEvaluables` (factor con ≥ 2 preguntas) → `crearEvaluacion` (Evaluacion "Activa" + un Cuestionario "Activo" con `generarClaveAleatoria()` por candidato) → opcional `exportarClaves` (.xls).
- **CU026**: `obtenerCuestionarioParaCompletar` (+ `obtenerParametros`); Activo → valida `tiempoMaximoActivo` ("Sin Contestar"); En Proceso → valida `tiempoMaximoCuestionario` ("Incompleto"); Aceptar → `armarCuestionario` (2 preguntas al azar por factor, mezcla, bloques) → "En Proceso"; por bloque `registrarRespuestaBloque`; último bloque → `calcularResultadosCuestionario` → "Completo".
- **CU028**: `buscarPuestoConResumen` (candidatos y evaluaciones completas) → `EvaluacionDAO.buscarPorPuesto` → elegir evaluaciones o TODAS → `generarOrdenMerito`: completos y no completos, `obtenerCaracteristicas`, puntajes por competencia vs. mínimo, promedio, orden descendente, resto agrupado por estado → `OrdenDeMeritoDTO` → Imprimir (IPP).
