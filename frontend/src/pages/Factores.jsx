import { useEffect, useState } from "react";
import { competencias, factores as api } from "../api.js";
import Gestion from "../components/Gestion.jsx";
import { Campo, PanelErrores, Pantalla, upper } from "../components/ui.jsx";
import useFormulario from "../components/useFormulario.js";

// CU017 – Dar de alta / CU018 – Modificar Factor
function FormFactor({ modo, id, onGuardado, onCancelar }) {
  const alta = modo === "alta";
  const [listaComp, setListaComp] = useState([]);
  const [ocupados, setOcupados] = useState([]);
  const f = useFormulario({
    modo, id, onGuardado,
    inicial: { codigo: "", nombre: "", descripcion: "", codigo_competencia: "", nro_orden: null },
    obtener: api.obtener,
    guardar: (d) => (alta ? api.alta(d) : api.modificar(id, d)),
    campos: ["codigo", "nombre", "descripcion", "codigo_competencia", "nro_orden"],
  });
  const comp = f.datos.codigo_competencia;

  useEffect(() => { competencias.buscar({}).then(setListaComp).catch(f.setError); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Mecanismo para gestionar el orden: muestra qué factor ocupa cada número y propone el siguiente libre
  useEffect(() => {
    if (!comp) return setOcupados([]);
    api.ordenes(comp).then((o) => {
      setOcupados(o);
      if (alta && f.datos.nro_orden == null) {
        const usados = new Set(o.map((x) => x.nro_orden));
        let n = 1;
        while (usados.has(n)) n++;
        f.setDatos((d) => ({ ...d, nro_orden: n }));
      }
    }).catch(f.setError);
  }, [comp]); // eslint-disable-line react-hooks/exhaustive-deps

  if (f.cargando) return <Pantalla titulo="Cargando…" />;
  const ocupante = Object.fromEntries(ocupados.map((o) => [o.nro_orden, o]));
  const max = Math.max(0, ...ocupados.map((o) => o.nro_orden)) + 1;
  const opcionesOrden = Array.from({ length: max }, (_, i) => i + 1);

  return (
    <Pantalla titulo={alta ? "Alta de Factor" : "Modificar Factor"}>
      <PanelErrores error={f.error} />
      <form className="form-grid" onSubmit={f.submit} noValidate>
        <Campo label="Código" invalido={f.invalido("codigo")}>
          <input ref={f.refs.codigo} value={f.datos.codigo} onChange={f.set("codigo", upper)} disabled={!alta} maxLength={50} autoFocus={alta} />
        </Campo>
        <Campo label="Nombre" invalido={f.invalido("nombre")}>
          <input ref={f.refs.nombre} value={f.datos.nombre} onChange={f.set("nombre", upper)} maxLength={100} autoFocus={!alta} />
        </Campo>
        <Campo label="Competencia" invalido={f.invalido("codigo_competencia")}>
          <select ref={f.refs.codigo_competencia} value={comp}
                  onChange={(e) => f.setDatos((d) => ({ ...d, codigo_competencia: e.target.value, nro_orden: alta ? null : d.nro_orden }))}>
            <option value="">Seleccionar…</option>
            {listaComp.map((c) => <option key={c.codigo} value={c.codigo}>{c.nombre}</option>)}
          </select>
        </Campo>
        <Campo label="Nro de orden" invalido={f.invalido("nro_orden")}>
          <select ref={f.refs.nro_orden} value={f.datos.nro_orden ?? ""} disabled={!comp}
                  onChange={(e) => f.setDatos((d) => ({ ...d, nro_orden: e.target.value ? Number(e.target.value) : null }))}>
            <option value="">Seleccionar…</option>
            {opcionesOrden.map((n) => {
              const o = ocupante[n];
              const propio = o && o.codigo_factor === id;
              return (
                <option key={n} value={n} disabled={!!o && !propio}>
                  {n}{o ? ` — ${propio ? "actual" : `ocupado por ${o.nombre_factor}`}` : " — libre"}
                </option>
              );
            })}
          </select>
        </Campo>
        <Campo label="Descripción" invalido={f.invalido("descripcion")} ancho={2}>
          <textarea ref={f.refs.descripcion} value={f.datos.descripcion || ""} onChange={f.set("descripcion", upper)} maxLength={300} rows={3} />
        </Campo>
        {ocupados.length > 0 && (
          <div className="orden-factores" style={{ gridColumn: "span 3" }}>
            <span className="hint">Orden actual de los factores en la competencia:</span>
            <ol>{ocupados.map((o) => <li key={o.nro_orden} value={o.nro_orden}>{o.nombre_factor}</li>)}</ol>
          </div>
        )}
        <div className="form-botones">
          <button type="submit" className="btn btn--primary" disabled={f.guardando}>Aceptar</button>
          <button type="button" className="btn btn--secondary" onClick={onCancelar}>Cancelar</button>
        </div>
      </form>
    </Pantalla>
  );
}

// CU016 – Gestión de Factores
export default function Factores({ onSalir }) {
  return (
    <Gestion
      titulo="Factores"
      api={api}
      buscarSinCriterio
      criterios={[{ name: "nombre_competencia", label: "Nombre de competencia" }, { name: "nombre_factor", label: "Nombre de factor" }]}
      columnas={[
        { titulo: "Código", valor: (x) => x.codigo },
        { titulo: "Factor", valor: (x) => x.nombre },
        { titulo: "Competencia", valor: (x) => x.nombre_competencia },
        { titulo: "Orden", valor: (x) => x.nro_orden, alinear: "right" },
      ]}
      idDe={(x) => x.codigo}
      nombreDe={(x) => x.nombre}
      Formulario={FormFactor}
      mensajeAlta={(x) => `El factor ${x.nombre} se ha creado correctamente ¿Desea cargar otro?`}
      onSalir={onSalir}
    />
  );
}
