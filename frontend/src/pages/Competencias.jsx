import { competencias as api } from "../api.js";
import Gestion from "../components/Gestion.jsx";
import { Campo, PanelErrores, Pantalla, upper } from "../components/ui.jsx";
import useFormulario from "../components/useFormulario.js";

const TIPOS = ["Técnica", "Actitudinal"];

// CU013 – Dar de alta / CU014 – Modificar Competencia
function FormCompetencia({ modo, id, onGuardado, onCancelar }) {
  const alta = modo === "alta";
  const f = useFormulario({
    modo, id, onGuardado,
    inicial: { codigo: "", nombre: "", descripcion: "", tipo: "" },
    obtener: api.obtener,
    guardar: (d) => (alta ? api.alta(d) : api.modificar(id, d)),
    campos: ["codigo", "nombre", "descripcion", "tipo"],
  });
  if (f.cargando) return <Pantalla titulo="Cargando…" />;
  return (
    <Pantalla titulo={alta ? "Alta de Competencia" : "Modificar Competencia"}>
      <PanelErrores error={f.error} />
      <form className="form-grid" onSubmit={f.submit} noValidate>
        <Campo label="Código" invalido={f.invalido("codigo")}>
          <input ref={f.refs.codigo} value={f.datos.codigo} onChange={f.set("codigo", upper)} disabled={!alta} maxLength={50} autoFocus={alta} />
        </Campo>
        <Campo label="Nombre" invalido={f.invalido("nombre")}>
          <input ref={f.refs.nombre} value={f.datos.nombre} onChange={f.set("nombre", upper)} maxLength={100} autoFocus={!alta} />
        </Campo>
        <Campo label="Tipo" invalido={f.invalido("tipo")}>
          <select ref={f.refs.tipo} value={f.datos.tipo} onChange={f.set("tipo")}>
            <option value="">Seleccionar…</option>
            {TIPOS.map((t) => <option key={t}>{t}</option>)}
          </select>
        </Campo>
        <Campo label="Descripción" invalido={f.invalido("descripcion")} ancho={3}>
          <textarea ref={f.refs.descripcion} value={f.datos.descripcion || ""} onChange={f.set("descripcion", upper)} maxLength={300} rows={3} />
        </Campo>
        <div className="form-botones">
          <button type="submit" className="btn btn--primary" disabled={f.guardando}>Aceptar</button>
          <button type="button" className="btn btn--secondary" onClick={onCancelar}>Cancelar</button>
        </div>
      </form>
    </Pantalla>
  );
}

// CU012 – Gestionar Competencias
export default function Competencias({ onSalir }) {
  return (
    <Gestion
      titulo="Competencias"
      api={api}
      buscarSinCriterio
      criterios={[{ name: "nombre", label: "Nombre de competencia" }]}
      columnas={[
        { titulo: "Código", valor: (c) => c.codigo },
        { titulo: "Nombre", valor: (c) => c.nombre },
        { titulo: "Tipo", valor: (c) => c.tipo },
      ]}
      idDe={(c) => c.codigo}
      nombreDe={(c) => c.nombre}
      Formulario={FormCompetencia}
      mensajeAlta={(c) => `La competencia ${c.nombre} se ha creado correctamente ¿Desea cargar otra?`}
      onSalir={onSalir}
    />
  );
}
