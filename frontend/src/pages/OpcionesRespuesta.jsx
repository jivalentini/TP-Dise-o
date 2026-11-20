import { opcionesRespuesta as api } from "../api.js";
import Gestion from "../components/Gestion.jsx";
import { Campo, PanelErrores, Pantalla, upper } from "../components/ui.jsx";
import useFormulario from "../components/useFormulario.js";

// CU029 – Dar de alta / CU030 – Modificar Opción de Respuesta
function FormOpcion({ modo, id, onGuardado, onCancelar }) {
  const alta = modo === "alta";
  const f = useFormulario({
    modo, id, onGuardado,
    inicial: { nombre: "", descripcion: "", items: [{ orden: 1, descripcion: "" }, { orden: 2, descripcion: "" }] },
    obtener: api.obtener,
    guardar: (d) => (alta ? api.alta(d) : api.modificar(id, d)),
    campos: ["nombre", "descripcion", "items"],
  });
  if (f.cargando) return <Pantalla titulo="Cargando…" />;
  const items = f.datos.items;
  const setItem = (i, campo, valor) => f.setDatos((d) => ({ ...d, items: d.items.map((x, n) => (n === i ? { ...x, [campo]: valor } : x)) }));
  const mover = (i, delta) => {
    const j = i + delta;
    if (j < 0 || j >= items.length) return;
    f.setDatos((d) => {
      const nuevos = d.items.map((x) => ({ ...x }));
      [nuevos[i].orden, nuevos[j].orden] = [nuevos[j].orden, nuevos[i].orden];
      return { ...d, items: nuevos };
    });
  };
  const porOrden = items.map((x, i) => ({ ...x, i })).sort((a, b) => (a.orden ?? 99) - (b.orden ?? 99));

  return (
    <Pantalla titulo={alta ? "Alta de Opción de Respuesta" : "Modificar Opción de Respuesta"}>
      <PanelErrores error={f.error} />
      <form className="form-grid" onSubmit={f.submit} noValidate>
        <Campo label="Nombre" invalido={f.invalido("nombre")}>
          <input ref={f.refs.nombre} value={f.datos.nombre} onChange={f.set("nombre", upper)} disabled={!alta} maxLength={100} autoFocus={alta} />
        </Campo>
        <Campo label="Descripción" invalido={f.invalido("descripcion")} ancho={2}>
          <input ref={f.refs.descripcion} value={f.datos.descripcion || ""} onChange={f.set("descripcion", upper)} maxLength={300} autoFocus={!alta} />
        </Campo>

        <fieldset className={`subgrilla ${f.invalido("items") ? "subgrilla--error" : ""}`} style={{ gridColumn: "span 3" }}>
          <legend>Lista de opciones {!alta && <span className="hint">(no se pueden agregar ni quitar opciones)</span>}</legend>
          <table>
            <thead><tr><th style={{ width: 150 }}>Orden de visualización</th><th>Descripción</th><th style={{ width: 150 }} /></tr></thead>
            <tbody>
              {porOrden.map(({ i, orden, descripcion }, pos) => (
                <tr key={i}>
                  <td>
                    <input ref={pos === 0 ? f.refs.items : null} type="number" min={1} value={orden ?? ""}
                           onChange={(e) => setItem(i, "orden", e.target.value === "" ? null : Number(e.target.value))} />
                  </td>
                  <td><input value={descripcion} onChange={(e) => setItem(i, "descripcion", upper(e.target.value))} maxLength={300} /></td>
                  <td className="subgrilla__acciones">
                    <button type="button" className="btn-icono" title="Subir" onClick={() => mover(i, -1)} disabled={pos === 0}>▲</button>
                    <button type="button" className="btn-icono" title="Bajar" onClick={() => mover(i, 1)} disabled={pos === items.length - 1}>▼</button>
                    {alta && (
                      <button type="button" className="btn-icono" title="Quitar" disabled={items.length <= 2}
                              onClick={() => f.setDatos((d) => ({ ...d, items: d.items.filter((_, n) => n !== i) }))}>✕</button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {alta && (
            <button type="button" className="btn btn--secondary btn--sm"
                    onClick={() => f.setDatos((d) => ({ ...d, items: [...d.items, { orden: Math.max(0, ...d.items.map((x) => x.orden || 0)) + 1, descripcion: "" }] }))}>
              + Agregar opción
            </button>
          )}
        </fieldset>

        <div className="form-botones">
          <button type="submit" className="btn btn--primary" disabled={f.guardando}>Aceptar</button>
          <button type="button" className="btn btn--secondary" onClick={onCancelar}>Cancelar</button>
        </div>
      </form>
    </Pantalla>
  );
}

// CU024 – Gestionar Opciones de Respuestas
export default function OpcionesRespuesta({ onSalir }) {
  return (
    <Gestion
      titulo="Opciones de respuesta"
      api={api}
      buscarSinCriterio
      criterios={[{ name: "nombre", label: "Nombre de la opción de respuesta" }]}
      columnas={[
        { titulo: "Nombre", valor: (o) => o.nombre },
        { titulo: "Descripción", valor: (o) => o.descripcion },
        { titulo: "Opciones", valor: (o) => o.items.map((i) => i.descripcion).join(" · ") },
      ]}
      idDe={(o) => o.nombre}
      nombreDe={(o) => o.nombre}
      Formulario={FormOpcion}
      mensajeAlta={(o) => `La opción ${o.nombre} se ha creado correctamente ¿Desea cargar otra?`}
      onSalir={onSalir}
    />
  );
}
