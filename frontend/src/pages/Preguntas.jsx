import { useEffect, useState } from "react";
import { competencias, factores, opcionesRespuesta, preguntas as api } from "../api.js";
import Gestion from "../components/Gestion.jsx";
import { Campo, Dialogo, PanelErrores, Pantalla, upper } from "../components/ui.jsx";
import useFormulario from "../components/useFormulario.js";

function useFactores(codigoCompetencia, onError) {
  const [lista, setLista] = useState([]);
  useEffect(() => {
    if (!codigoCompetencia) return setLista([]);
    factores.buscar({ codigo_competencia: codigoCompetencia }).then(setLista).catch(onError);
  }, [codigoCompetencia]); // eslint-disable-line react-hooks/exhaustive-deps
  return lista;
}

// CU033 – Generar pregunta con Inteligencia Artificial (ventana emergente)
function GenerarConIA({ listaComp, inicial, onGenerada, onCerrar }) {
  const [sel, setSel] = useState(inicial);
  const [error, setError] = useState(null);
  const [aviso, setAviso] = useState(null);
  const [generando, setGenerando] = useState(false);
  const lista = useFactores(sel.codigo_competencia, setError);

  async function generar() {
    if (generando) return;
    setGenerando(true);
    try {
      onGenerada(await api.generarIA(sel));
    } catch (e) {
      if (e.status === 503) setAviso(e.message); // 4.A: no se puede conectar con el servicio
      else setError(e);
    } finally {
      setGenerando(false);
    }
  }

  if (aviso) {
    return <Dialogo key="aviso" titulo="Servicio de IA" tipo="error" mensaje={aviso} botones={[{ label: "Aceptar", primario: true, onClick: () => setAviso(null) }]} />;
  }
  return (
    <Dialogo key="form" titulo="Generar pregunta con IA" botones={[
      { label: generando ? "Generando…" : "Generar pregunta", primario: true, onClick: generar },
      { label: "Cancelar", onClick: onCerrar },
    ]}>
      <PanelErrores error={error} />
      <div className="form-col">
        <Campo label="Competencia" invalido={error?.campos?.includes("codigo_competencia")}>
          <select value={sel.codigo_competencia} onChange={(e) => setSel({ codigo_competencia: e.target.value, codigo_factor: "" })}>
            <option value="">Seleccionar…</option>
            {listaComp.map((c) => <option key={c.codigo} value={c.codigo}>{c.nombre}</option>)}
          </select>
        </Campo>
        <Campo label="Factor" invalido={error?.campos?.includes("codigo_factor")}>
          <select value={sel.codigo_factor} disabled={!sel.codigo_competencia} onChange={(e) => setSel({ ...sel, codigo_factor: e.target.value })}>
            <option value="">Seleccionar…</option>
            {lista.map((f) => <option key={f.codigo} value={f.codigo}>{f.nombre}</option>)}
          </select>
        </Campo>
      </div>
    </Dialogo>
  );
}

// CU021 – Dar de alta / CU022 – Modificar Pregunta
function FormPregunta({ modo, id, onGuardado, onCancelar }) {
  const alta = modo === "alta";
  const [listaComp, setListaComp] = useState([]);
  const [listaOpc, setListaOpc] = useState([]);
  const [ia, setIa] = useState(false);
  const f = useFormulario({
    modo, id, onGuardado,
    inicial: { codigo_competencia: "", codigo_factor: "", nombre_pregunta: "", enunciado: "", descripcion: "", nombre_opcion_respuesta: "", ponderaciones: [] },
    obtener: api.obtener,
    guardar: (d) => (alta ? api.alta(d) : api.modificar(id, d)),
    campos: ["codigo_competencia", "codigo_factor", "nombre_pregunta", "enunciado", "descripcion", "nombre_opcion_respuesta", "ponderaciones"],
  });
  const listaFac = useFactores(alta ? f.datos.codigo_competencia : null, f.setError);

  useEffect(() => {
    competencias.buscar({}).then(setListaComp).catch(f.setError);
    opcionesRespuesta.buscar({}).then(setListaOpc).catch(f.setError);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  if (f.cargando) return <Pantalla titulo="Cargando…" />;

  const elegirOpcion = (nombre) => {
    const o = listaOpc.find((x) => x.nombre === nombre);
    f.setDatos((d) => ({ ...d, nombre_opcion_respuesta: nombre, ponderaciones: (o?.items || []).map((i) => ({ ...i, ponderacion: null })) }));
  };
  const setPond = (orden, v) => f.setDatos((d) => ({ ...d, ponderaciones: d.ponderaciones.map((p) => (p.orden === orden ? { ...p, ponderacion: v } : p)) }));
  const suma = f.datos.ponderaciones.reduce((s, p) => s + (Number(p.ponderacion) || 0), 0);

  return (
    <Pantalla titulo={alta ? "Alta de Pregunta" : "Modificar Pregunta"}>
      <PanelErrores error={f.error} />
      <form className="form-grid" onSubmit={f.submit} noValidate>
        {alta ? (
          <>
            <Campo label="Competencia" invalido={f.invalido("codigo_competencia")}>
              <select ref={f.refs.codigo_competencia} value={f.datos.codigo_competencia} autoFocus
                      onChange={(e) => f.setDatos((d) => ({ ...d, codigo_competencia: e.target.value, codigo_factor: "" }))}>
                <option value="">Seleccionar…</option>
                {listaComp.map((c) => <option key={c.codigo} value={c.codigo}>{c.nombre}</option>)}
              </select>
            </Campo>
            <Campo label="Factor" invalido={f.invalido("codigo_factor")}>
              <select ref={f.refs.codigo_factor} value={f.datos.codigo_factor} onChange={f.set("codigo_factor")} disabled={!f.datos.codigo_competencia}>
                <option value="">Seleccionar…</option>
                {listaFac.map((x) => <option key={x.codigo} value={x.codigo}>{x.nombre}</option>)}
              </select>
            </Campo>
          </>
        ) : (
          <>
            <Campo label="Competencia"><input value={f.datos.nombre_competencia || ""} readOnly disabled /></Campo>
            <Campo label="Factor"><input value={f.datos.nombre_factor || ""} readOnly disabled /></Campo>
          </>
        )}
        <Campo label="Nombre de Pregunta" invalido={f.invalido("nombre_pregunta")}>
          <input ref={f.refs.nombre_pregunta} value={f.datos.nombre_pregunta} onChange={f.set("nombre_pregunta", upper)} maxLength={300} autoFocus={!alta} />
        </Campo>
        <Campo label="Pregunta" invalido={f.invalido("enunciado")} ancho={3}>
          <textarea ref={f.refs.enunciado} value={f.datos.enunciado} onChange={f.set("enunciado", upper)} maxLength={300} rows={2} />
        </Campo>
        <Campo label="Descripción (opcional)" invalido={f.invalido("descripcion")} ancho={2}>
          <input ref={f.refs.descripcion} value={f.datos.descripcion || ""} onChange={f.set("descripcion", upper)} maxLength={300} />
        </Campo>
        <Campo label="Opción de Respuesta" invalido={f.invalido("nombre_opcion_respuesta")}>
          <select ref={f.refs.nombre_opcion_respuesta} value={f.datos.nombre_opcion_respuesta} onChange={(e) => elegirOpcion(e.target.value)}>
            <option value="">Seleccionar…</option>
            {listaOpc.map((o) => <option key={o.nombre} value={o.nombre}>{o.nombre}</option>)}
          </select>
        </Campo>

        {f.datos.ponderaciones.length > 0 && (
          <fieldset className={`subgrilla ${f.invalido("ponderaciones") ? "subgrilla--error" : ""}`} style={{ gridColumn: "span 3" }}>
            <legend>Opciones <span className="hint">(las ponderaciones deben sumar 10 y ser 0 o positivas)</span></legend>
            <table>
              <thead><tr><th style={{ width: 80 }}>Orden</th><th>Descripción</th><th style={{ width: 160 }}>Ponderación</th></tr></thead>
              <tbody>
                {[...f.datos.ponderaciones].sort((a, b) => a.orden - b.orden).map((p, i) => (
                  <tr key={p.orden}>
                    <td>{p.orden}</td>
                    <td>{p.descripcion}</td>
                    <td>
                      <input ref={i === 0 ? f.refs.ponderaciones : null} type="number" min={0} max={10} step="0.25" value={p.ponderacion ?? ""}
                             onChange={(e) => setPond(p.orden, e.target.value === "" ? null : Number(e.target.value))} />
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr><td colSpan={2} style={{ textAlign: "right" }}><strong>Total</strong></td>
                  <td className={Math.abs(suma - 10) < 0.001 ? "ok" : "mal"}><strong>{+suma.toFixed(2)} / 10</strong></td></tr>
              </tfoot>
            </table>
          </fieldset>
        )}

        <div className="form-botones">
          {alta && <button type="button" className="btn btn--ia" onClick={() => setIa(true)}>✦ Generar con IA</button>}
          <button type="submit" className="btn btn--primary" disabled={f.guardando}>Aceptar</button>
          <button type="button" className="btn btn--secondary" onClick={onCancelar}>Cancelar</button>
        </div>
      </form>
      {ia && (
        <GenerarConIA
          listaComp={listaComp}
          inicial={{ codigo_competencia: f.datos.codigo_competencia, codigo_factor: f.datos.codigo_factor }}
          onCerrar={() => setIa(false)}
          onGenerada={(p) => {
            f.setDatos((d) => ({ ...d, ...p, descripcion: p.descripcion || "" }));
            f.setError(null);
            setIa(false);
          }}
        />
      )}
    </Pantalla>
  );
}

// CU020 – Gestionar Preguntas
export default function Preguntas({ onSalir }) {
  return (
    <Gestion
      titulo="Preguntas"
      api={api}
      criterios={[
        { name: "nombre_competencia", label: "Competencia" },
        { name: "nombre_factor", label: "Factor" },
        { name: "nombre_pregunta", label: "Nombre de Pregunta" },
      ]}
      columnas={[
        { titulo: "Competencia", valor: (p) => p.nombre_competencia },
        { titulo: "Factor", valor: (p) => p.nombre_factor },
        { titulo: "Pregunta", valor: (p) => <><strong>{p.nombre_pregunta}</strong><div className="sub">{p.enunciado}</div></> },
      ]}
      idDe={(p) => p.id_pregunta}
      nombreDe={(p) => p.nombre_pregunta}
      Formulario={FormPregunta}
      mensajeAlta={(p) => `La Pregunta ${p.nombre_pregunta} se ha creado correctamente ¿Desea cargar otra?`}
      onSalir={onSalir}
    />
  );
}
