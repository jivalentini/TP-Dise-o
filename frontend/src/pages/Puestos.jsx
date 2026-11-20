import { useEffect, useState } from "react";
import { competencias, puestos as api } from "../api.js";
import Gestion from "../components/Gestion.jsx";
import { Campo, Dialogo, PanelErrores, Pantalla, upper } from "../components/ui.jsx";
import useFormulario from "../components/useFormulario.js";

// Ventana "Generar con IA" (alcance: creación de puestos con GenAI)
function GenerarPuestoIA({ empresa, onGenerado, onCerrar }) {
  const [descripcion, setDescripcion] = useState("");
  const [error, setError] = useState(null);
  const [generando, setGenerando] = useState(false);
  async function generar() {
    setGenerando(true);
    try {
      onGenerado(await api.generarIA({ descripcion, empresa }));
    } catch (e) {
      setError(e);
    } finally {
      setGenerando(false);
    }
  }
  return (
    <Dialogo titulo="Generar puesto con IA" botones={[
      { label: generando ? "Generando…" : "Generar puesto", primario: true, onClick: generar },
      { label: "Cancelar", onClick: onCerrar },
    ]}>
      <PanelErrores error={error} />
      <Campo label="Describa el puesto buscado">
        <textarea rows={4} value={descripcion} onChange={(e) => setDescripcion(e.target.value)} placeholder="Ej.: desarrollador Python senior para APIs de pagos, con liderazgo técnico…" />
      </Campo>
    </Dialogo>
  );
}

// CU009 – Dar de alta / CU010 – Modificar Puesto o función
function FormPuesto({ modo, id, onGuardado, onCancelar }) {
  const alta = modo === "alta";
  const [listaComp, setListaComp] = useState([]);
  const [ia, setIa] = useState(false);
  const f = useFormulario({
    modo, id, onGuardado,
    inicial: { codigo: "", nombre_puesto: "", descripcion: "", empresa: "", caracteristicas: [] },
    obtener: api.obtener,
    guardar: (d) => (alta ? api.alta(d) : api.modificar(id, d)),
    campos: ["codigo", "nombre_puesto", "descripcion", "empresa", "caracteristicas"],
  });
  useEffect(() => { competencias.buscar({}).then(setListaComp).catch(f.setError); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  if (f.cargando) return <Pantalla titulo="Cargando…" />;
  const car = f.datos.caracteristicas;
  const setCar = (i, campo, valor) => f.setDatos((d) => ({ ...d, caracteristicas: d.caracteristicas.map((x, n) => (n === i ? { ...x, [campo]: valor } : x)) }));
  const usadas = new Set(car.map((c) => c.codigo_competencia));

  return (
    <Pantalla titulo={alta ? "Alta de Puesto o función" : "Modificar Puesto o función"}>
      <PanelErrores error={f.error} />
      <form className="form-grid" onSubmit={f.submit} noValidate>
        <Campo label="Código" invalido={f.invalido("codigo")}>
          <input ref={f.refs.codigo} value={f.datos.codigo} onChange={f.set("codigo", upper)} disabled={!alta} maxLength={50} autoFocus={alta} />
        </Campo>
        <Campo label="Nombre del Puesto" invalido={f.invalido("nombre_puesto")}>
          <input ref={f.refs.nombre_puesto} value={f.datos.nombre_puesto} onChange={f.set("nombre_puesto", upper)} maxLength={100} autoFocus={!alta} />
        </Campo>
        <Campo label="Empresa" invalido={f.invalido("empresa")}>
          <input ref={f.refs.empresa} value={f.datos.empresa} onChange={f.set("empresa", upper)} maxLength={100} />
        </Campo>
        <Campo label="Descripción" invalido={f.invalido("descripcion")} ancho={3}>
          <textarea ref={f.refs.descripcion} value={f.datos.descripcion || ""} onChange={f.set("descripcion", upper)} maxLength={300} rows={2} />
        </Campo>

        <fieldset className={`subgrilla ${f.invalido("caracteristicas") ? "subgrilla--error" : ""}`} style={{ gridColumn: "span 3" }}>
          <legend>Características del Puesto <span className="hint">(competencia y ponderación mínima requerida, de 0 a 10)</span></legend>
          <table>
            <thead><tr><th>Competencia</th><th style={{ width: 160 }}>Ponderación</th><th style={{ width: 50 }} /></tr></thead>
            <tbody>
              {car.length === 0 && <tr><td colSpan={3} className="grilla__vacio">Agregue al menos una competencia.</td></tr>}
              {car.map((c, i) => (
                <tr key={i}>
                  <td>
                    <select ref={i === 0 ? f.refs.caracteristicas : null} value={c.codigo_competencia} onChange={(e) => setCar(i, "codigo_competencia", e.target.value)}>
                      <option value="">Seleccionar…</option>
                      {listaComp.map((x) => (
                        <option key={x.codigo} value={x.codigo} disabled={usadas.has(x.codigo) && x.codigo !== c.codigo_competencia}>{x.nombre} ({x.tipo})</option>
                      ))}
                    </select>
                  </td>
                  <td>
                    <input type="number" min={0} max={10} step="0.5" value={c.ponderacion_minima_requerida ?? ""}
                           onChange={(e) => setCar(i, "ponderacion_minima_requerida", e.target.value === "" ? null : Number(e.target.value))} />
                  </td>
                  <td><button type="button" className="btn-icono" title="Quitar" onClick={() => f.setDatos((d) => ({ ...d, caracteristicas: d.caracteristicas.filter((_, n) => n !== i) }))}>✕</button></td>
                </tr>
              ))}
            </tbody>
          </table>
          <button type="button" className="btn btn--secondary btn--sm" disabled={usadas.size >= listaComp.length && car.length > 0}
                  onClick={() => f.setDatos((d) => ({ ...d, caracteristicas: [...d.caracteristicas, { codigo_competencia: "", ponderacion_minima_requerida: null }] }))}>
            + Agregar competencia
          </button>
        </fieldset>

        <div className="form-botones">
          {alta && <button type="button" className="btn btn--ia" onClick={() => setIa(true)}>✦ Generar con IA</button>}
          <button type="submit" className="btn btn--primary" disabled={f.guardando}>Aceptar</button>
          <button type="button" className="btn btn--secondary" onClick={onCancelar}>Cancelar</button>
        </div>
      </form>
      {ia && (
        <GenerarPuestoIA
          empresa={f.datos.empresa}
          onCerrar={() => setIa(false)}
          onGenerado={(p) => {
            f.setDatos((d) => ({ ...d, nombre_puesto: p.nombre_puesto || d.nombre_puesto, descripcion: p.descripcion || d.descripcion,
                                 caracteristicas: p.caracteristicas.length ? p.caracteristicas : d.caracteristicas }));
            f.setError(null);
            setIa(false);
          }}
        />
      )}
    </Pantalla>
  );
}

// CU008 – Gestionar Puestos o funciones
export default function Puestos({ onSalir }) {
  return (
    <Gestion
      titulo="Puestos o funciones"
      api={api}
      criterios={[{ name: "codigo", label: "Código" }, { name: "nombre_puesto", label: "Nombre del Puesto" }, { name: "empresa", label: "Empresa" }]}
      columnas={[
        { titulo: "Código", valor: (p) => p.codigo },
        { titulo: "Nombre del puesto", valor: (p) => p.nombre_puesto },
        { titulo: "Empresa", valor: (p) => p.empresa },
      ]}
      idDe={(p) => p.codigo}
      nombreDe={(p) => p.nombre_puesto}
      Formulario={FormPuesto}
      mensajeAlta={(p) => `El puesto ${p.nombre_puesto} se ha creado correctamente ¿Desea cargar otro?`}
      onSalir={onSalir}
    />
  );
}
