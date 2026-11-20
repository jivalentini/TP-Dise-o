import { useState } from "react";
import { ordenMerito as api } from "../api.js";
import { Campo, Dialogo, Grilla, PanelErrores, Pantalla, fecha, upper } from "../components/ui.jsx";

const persona = [
  { titulo: "Tipo doc.", valor: (i) => i.tipo_documento },
  { titulo: "Documento", valor: (i) => i.nro_documento },
  { titulo: "Apellido", valor: (i) => i.apellido },
  { titulo: "Nombre", valor: (i) => i.nombre },
];
const COL_COMPLETOS = [
  { titulo: "#", valor: (i) => i.posicion, alinear: "right" },
  ...persona,
  { titulo: "Puntaje", valor: (i) => i.puntaje_total?.toFixed(2), alinear: "right" },
  { titulo: "Fecha inicio", valor: (i) => fecha(i.fecha_inicio) },
  { titulo: "Fecha fin", valor: (i) => fecha(i.fecha_fin_o_ultimo_ingreso) },
  { titulo: "Accesos", valor: (i) => i.cantidad_accesos, alinear: "right" },
];
const COL_OTROS = [
  ...persona,
  { titulo: "Fecha inicio", valor: (i) => fecha(i.fecha_inicio) },
  { titulo: "Último ingreso", valor: (i) => fecha(i.fecha_fin_o_ultimo_ingreso) },
  { titulo: "Accesos", valor: (i) => i.cantidad_accesos, alinear: "right" },
];
const idItem = (i) => `${i.tipo_documento}-${i.nro_documento}-${i.estado_cuestionario}-${i.fecha_inicio}`;

// CU028 – Emitir Orden de mérito
export default function OrdenMerito({ onSalir }) {
  const [filtros, setFiltros] = useState({ codigo: "", nombre_puesto: "", empresa: "" });
  const [puestos, setPuestos] = useState(null);
  const [error, setError] = useState(null);
  const [eleccion, setEleccion] = useState(null); // { puesto, evaluaciones, seleccion }
  const [dialogo, setDialogo] = useState(null);
  const [orden, setOrden] = useState(null);

  async function buscar(e) {
    e.preventDefault();
    if (!Object.values(filtros).some((v) => v.trim())) return setError(new Error("Ingrese al menos un criterio de búsqueda."));
    try {
      setPuestos(await api.buscarPuestos(filtros));
      setError(null);
    } catch (err) {
      setError(err);
    }
  }

  async function emitirPara(puesto) {
    try {
      const evaluaciones = await api.evaluaciones(puesto.codigo);
      setEleccion({ puesto, evaluaciones, seleccion: "TODAS" });
    } catch (err) {
      // 6.A: el puesto no posee evaluaciones
      setDialogo({ titulo: "Orden de mérito", mensaje: err.message, tipo: "error", botones: [{ label: "Aceptar", primario: true, onClick: () => setDialogo(null) }] });
    }
  }

  async function emitir() {
    const ids = eleccion.seleccion === "TODAS" ? null : eleccion.seleccion;
    if (ids && ids.length === 0) return;
    try {
      setOrden({ ...(await api.emitir(eleccion.puesto.codigo, ids)), ids });
      setEleccion(null);
    } catch (err) {
      setError(err);
      setEleccion(null);
    }
  }

  async function imprimir() {
    try {
      const { disponible } = await api.impresora();
      if (!disponible) return window.print(); // sin cola IPP configurada: diálogo de impresión del navegador
      const r = await api.imprimir(orden.codigo_puesto, orden.ids);
      setDialogo({ titulo: "Imprimir", mensaje: r.mensaje, botones: [{ label: "Aceptar", primario: true, onClick: () => setDialogo(null) }] });
    } catch {
      window.print();
    }
  }

  if (orden) {
    const otros = Object.entries(orden.otros_por_estado);
    return (
      <Pantalla
        titulo="Orden de mérito"
        pie={<>
          <button type="button" className="btn btn--primary" onClick={imprimir}>Imprimir</button>
          <button type="button" className="btn btn--secondary" onClick={() => setOrden(null)}>Volver</button>
        </>}
      >
        <div className="reporte-cabecera">
          <div><span>Puesto</span><strong>{orden.codigo_puesto} – {orden.nombre_puesto}</strong></div>
          <div><span>Empresa</span><strong>{orden.empresa}</strong></div>
          <div><span>Evaluaciones</span><strong>{orden.ids ? orden.evaluaciones.map((e) => `#${e}`).join(", ") : "TODAS"}</strong></div>
          <div><span>Emitido</span><strong>{fecha(orden.fecha_generacion, false)}</strong></div>
        </div>

        <h3 className="subtitulo">Orden de mérito <span className="hint">— cuestionarios completos que alcanzan las ponderaciones mínimas</span></h3>
        <Grilla columnas={COL_COMPLETOS} filas={orden.items} idDe={idItem} vacio="Ningún candidato alcanzó las ponderaciones mínimas." />

        <h3 className="subtitulo">No alcanzan las ponderaciones mínimas</h3>
        <Grilla columnas={COL_COMPLETOS} filas={orden.no_alcanzan_minimos} idDe={idItem} vacio="—" />

        {otros.map(([estado, items]) => (
          <div key={estado}>
            <h3 className="subtitulo">Cuestionarios en estado {estado}</h3>
            <Grilla columnas={COL_OTROS} filas={items} idDe={idItem} />
          </div>
        ))}
        {dialogo && <Dialogo key={dialogo.mensaje} {...dialogo} />}
      </Pantalla>
    );
  }

  const set = (c) => (e) => setFiltros({ ...filtros, [c]: upper(e.target.value) });
  return (
    <Pantalla titulo="Orden de mérito">
      <form className="criterios" onSubmit={buscar}>
        <Campo label="Código"><input value={filtros.codigo} onChange={set("codigo")} autoFocus /></Campo>
        <Campo label="Nombre del Puesto"><input value={filtros.nombre_puesto} onChange={set("nombre_puesto")} /></Campo>
        <Campo label="Empresa"><input value={filtros.empresa} onChange={set("empresa")} /></Campo>
        <div className="criterios__botones">
          <button type="submit" className="btn btn--primary">Buscar</button>
          <button type="button" className="btn btn--secondary" onClick={onSalir}>Cancelar</button>
        </div>
      </form>
      <PanelErrores error={error} />
      {puestos && (
        <Grilla
          columnas={[
            { titulo: "Código", valor: (p) => p.codigo }, { titulo: "Nombre del puesto", valor: (p) => p.nombre_puesto },
            { titulo: "Empresa", valor: (p) => p.empresa }, { titulo: "Candidatos", valor: (p) => p.cantidad_candidatos, alinear: "right" },
            { titulo: "Evaluaciones completas", valor: (p) => p.cantidad_evaluaciones_completas, alinear: "right" },
          ]}
          filas={puestos}
          idDe={(p) => p.codigo}
          acciones={(p) => <button type="button" className="btn btn--primary btn--sm" onClick={() => emitirPara(p)}>Emitir el orden de mérito</button>}
        />
      )}

      {eleccion && (
        <Dialogo key="eleccion" titulo={`Evaluaciones de ${eleccion.puesto.nombre_puesto}`} botones={[
          { label: "Emitir", primario: true, onClick: emitir },
          { label: "Cancelar", onClick: () => setEleccion(null) },
        ]}>
          <p className="dialog__msg">Seleccione para qué evaluación/es emitir el orden de mérito:</p>
          <div className="checks">
            <label><input type="radio" checked={eleccion.seleccion === "TODAS"} onChange={() => setEleccion({ ...eleccion, seleccion: "TODAS" })} /> <strong>TODAS</strong></label>
            {eleccion.evaluaciones.map((e) => {
              const sel = Array.isArray(eleccion.seleccion) && eleccion.seleccion.includes(e.id_evaluacion);
              return (
                <label key={e.id_evaluacion}>
                  <input type="checkbox" checked={sel} onChange={() => {
                    const actual = Array.isArray(eleccion.seleccion) ? eleccion.seleccion : [];
                    setEleccion({ ...eleccion, seleccion: sel ? actual.filter((x) => x !== e.id_evaluacion) : [...actual, e.id_evaluacion] });
                  }} />
                  Evaluación #{e.id_evaluacion} — {fecha(e.fecha_creacion, false)} · {e.cantidad_completos}/{e.cantidad_cuestionarios} completos
                </label>
              );
            })}
          </div>
        </Dialogo>
      )}
      {dialogo && <Dialogo key={dialogo.mensaje} {...dialogo} />}
    </Pantalla>
  );
}
