import { useEffect, useRef } from "react";

export const upper = (v) => (v ?? "").toUpperCase();

export function fecha(v, conHora = true) {
  if (!v) return "—";
  const soloFecha = /^\d{4}-\d{2}-\d{2}$/.test(v); // "aaaa-mm-dd" se interpreta en hora local, no UTC
  const d = soloFecha ? new Date(`${v}T00:00:00`) : new Date(v);
  const f = d.toLocaleDateString("es-AR", { day: "2-digit", month: "2-digit", year: "numeric" });
  return conHora ? `${f} ${d.toLocaleTimeString("es-AR", { hour: "2-digit", minute: "2-digit" })}` : f;
}

/** Diálogo modal con botones configurables. El primer botón recibe el foco; Escape = último botón. */
export function Dialogo({ titulo, mensaje, tipo = "info", botones, children }) {
  const primero = useRef(null);
  const caja = useRef(null);
  const ultimos = useRef(botones);
  ultimos.current = botones;

  useEffect(() => {
    // Si el diálogo tiene campos, foco en el primero; si no, en el primer botón
    const campo = caja.current?.querySelector("input, select, textarea");
    (campo || primero.current)?.focus();
    const onKey = (e) => {
      if (e.key !== "Escape") return;
      const b = ultimos.current;
      b[b.length - 1]?.onClick();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  return (
    <div className="overlay no-print">
      <div ref={caja} className={`dialog dialog--${tipo}`} role="alertdialog" aria-modal="true" aria-labelledby="dlg-titulo">
        <h2 id="dlg-titulo">{titulo}</h2>
        {mensaje && <p className="dialog__msg">{mensaje}</p>}
        {children}
        <div className="dialog__acciones">
          {botones.map((b, i) => (
            <button
              key={b.label}
              ref={i === 0 ? primero : null}
              type="button"
              className={`btn ${b.primario ? "btn--primary" : b.peligro ? "btn--danger" : "btn--secondary"}`}
              onClick={b.onClick}
            >
              {b.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

/** Mensajes de error sin tapar campos ni botones (flujos 2.A / 2.B). */
export function PanelErrores({ error }) {
  if (!error) return null;
  return (
    <div className="errores" role="alert">
      <strong>{error.message}</strong>
      {error.errores?.length > 0 && (
        <ul>
          {error.errores.map((e) => (
            <li key={e}>{e}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

/** Grilla con selección de una fila (o varias con `multiple`). */
export function Grilla({ columnas, filas, idDe, seleccion, onSeleccion, multiple = false, vacio = "Sin resultados.", acciones }) {
  const sel = multiple ? seleccion || [] : seleccion;
  const estaSel = (id) => (multiple ? sel.includes(id) : sel === id);
  const toggle = (id) => {
    if (!onSeleccion) return;
    if (multiple) onSeleccion(estaSel(id) ? sel.filter((x) => x !== id) : [...sel, id]);
    else onSeleccion(id);
  };
  return (
    <div className="grilla">
      <table>
        <thead>
          <tr>
            {columnas.map((c) => (
              <th key={c.titulo} style={{ textAlign: c.alinear || "left" }}>
                {c.titulo}
              </th>
            ))}
            {acciones && <th className="no-print" />}
          </tr>
        </thead>
        <tbody>
          {filas.length === 0 && (
            <tr>
              <td colSpan={columnas.length + (acciones ? 1 : 0)} className="grilla__vacio">
                {vacio}
              </td>
            </tr>
          )}
          {filas.map((f) => {
            const id = idDe(f);
            return (
              <tr
                key={id}
                className={estaSel(id) ? "sel" : ""}
                onClick={() => toggle(id)}
                tabIndex={onSeleccion ? 0 : undefined}
                onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && onSeleccion && (e.preventDefault(), toggle(id))}
                aria-selected={onSeleccion ? estaSel(id) : undefined}
              >
                {columnas.map((c) => (
                  <td key={c.titulo} style={{ textAlign: c.alinear || "left" }}>
                    {c.valor(f)}
                  </td>
                ))}
                {acciones && <td className="no-print grilla__acciones">{acciones(f)}</td>}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

/** Campo con etiqueta. `invalido` lo resalta cuando el backend informa ese campo con error. */
export function Campo({ label, invalido, children, ancho }) {
  return (
    <label className={`field ${invalido ? "field--error" : ""}`} style={ancho ? { gridColumn: `span ${ancho}` } : undefined}>
      <span>{label}</span>
      {children}
    </label>
  );
}

export function Pantalla({ titulo, children, pie }) {
  return (
    <section className="pantalla">
      <h2 className="pantalla__titulo">{titulo}</h2>
      {children}
      {pie && <div className="pantalla__pie no-print">{pie}</div>}
    </section>
  );
}

/** Enfoca el campo que informó el backend (p. ej. 2.B "con foco en el campo Nombre"). */
export function useFoco(error, refs) {
  useEffect(() => {
    const campo = error?.campo || error?.campos?.[0];
    if (campo && refs[campo]?.current) refs[campo].current.focus();
  }, [error]); // eslint-disable-line react-hooks/exhaustive-deps
}
