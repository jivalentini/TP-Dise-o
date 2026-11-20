import { useState } from "react";
import { Campo, Dialogo, Grilla, PanelErrores, Pantalla, upper } from "./ui.jsx";

/**
 * Flujo común de los CU "Gestionar ..." (CU008, 012, 016, 020, 024):
 * criterios de búsqueda → Buscar → grilla → Nuevo / Modificar / Eliminar (extensiones) → actualiza la grilla.
 */
export default function Gestion({
  titulo, api, criterios, columnas, idDe, nombreDe, Formulario,
  mensajeAlta, mensajeEliminado, onSalir, buscarSinCriterio = false,
}) {
  const vacio = Object.fromEntries(criterios.map((c) => [c.name, ""]));
  const [filtros, setFiltros] = useState(vacio);
  const [ultima, setUltima] = useState(null); // última búsqueda realizada (para "actualiza la grilla")
  const [filas, setFilas] = useState([]);
  const [sel, setSel] = useState(null);
  const [error, setError] = useState(null);
  const [vista, setVista] = useState({ modo: "buscar" });
  const [dialogo, setDialogo] = useState(null);
  const [cargando, setCargando] = useState(false);

  async function buscar(params = filtros, silencioso = false) {
    if (!buscarSinCriterio && !Object.values(params).some((v) => v.trim())) {
      setError(new Error("Ingrese al menos un criterio de búsqueda."));
      return;
    }
    setCargando(true);
    try {
      const r = await api.buscar(params);
      setFilas(r);
      setUltima(params);
      setError(null);
      if (!silencioso) setSel(null);
      else if (!r.some((f) => idDe(f) === sel)) setSel(null);
    } catch (e) {
      setError(e);
    } finally {
      setCargando(false);
    }
  }

  const refrescar = () => ultima && buscar(ultima, true);
  const volver = () => {
    setVista({ modo: "buscar" });
    refrescar();
  };

  async function eliminar() {
    const fila = filas.find((f) => idDe(f) === sel);
    try {
      const r = await api.puedeEliminar(sel);
      if (!r.puede) {
        setDialogo({ titulo: "No se puede eliminar", mensaje: r.mensaje, tipo: "error", botones: [{ label: "Aceptar", primario: true, onClick: () => setDialogo(null) }] });
        return;
      }
      setDialogo({
        titulo: "Confirmar eliminación",
        mensaje: r.mensaje,
        tipo: "confirm",
        botones: [
          {
            label: "ELIMINAR",
            peligro: true,
            onClick: async () => {
              try {
                const res = await api.eliminar(sel);
                setDialogo({ titulo: "Eliminado", mensaje: res.mensaje || mensajeEliminado?.(fila), botones: [{ label: "Aceptar", primario: true, onClick: () => { setDialogo(null); setSel(null); refrescar(); } }] });
              } catch (e) {
                setDialogo({ titulo: "Error", mensaje: e.message, tipo: "error", botones: [{ label: "Aceptar", primario: true, onClick: () => setDialogo(null) }] });
              }
            },
          },
          { label: "CANCELAR", onClick: () => setDialogo(null) },
        ],
      });
    } catch (e) {
      setError(e);
    }
  }

  if (vista.modo !== "buscar") {
    return (
      <>
        <Formulario
          key={vista.key}
          modo={vista.modo}
          id={vista.id}
          onCancelar={volver}
          onGuardado={(dto) =>
            vista.modo === "alta"
              ? setDialogo({
                  titulo: "Alta exitosa",
                  mensaje: mensajeAlta(dto),
                  botones: [
                    { label: "SI", primario: true, onClick: () => { setDialogo(null); setVista({ modo: "alta", key: Date.now() }); } },
                    { label: "NO", onClick: () => { setDialogo(null); volver(); } },
                  ],
                })
              : setDialogo({
                  titulo: "Modificación exitosa",
                  mensaje: "La operación ha culminado con éxito",
                  botones: [{ label: "Aceptar", primario: true, onClick: () => { setDialogo(null); volver(); } }],
                })
          }
        />
        {dialogo && <Dialogo key={`${dialogo.titulo}|${dialogo.mensaje}`} {...dialogo} />}
      </>
    );
  }

  return (
    <Pantalla
      titulo={titulo}
      pie={<button type="button" className="btn btn--secondary" onClick={onSalir}>Salir</button>}
    >
      <form className="criterios" onSubmit={(e) => { e.preventDefault(); buscar(); }}>
        {criterios.map((c) => (
          <Campo key={c.name} label={c.label}>
            <input value={filtros[c.name]} onChange={(e) => setFiltros({ ...filtros, [c.name]: upper(e.target.value) })} placeholder="Contiene…" />
          </Campo>
        ))}
        <div className="criterios__botones">
          <button type="submit" className="btn btn--primary" disabled={cargando}>Buscar</button>
          <button type="button" className="btn btn--secondary" onClick={() => setVista({ modo: "alta", key: Date.now() })}>Nuevo</button>
        </div>
      </form>

      <PanelErrores error={error} />

      <Grilla columnas={columnas} filas={filas} idDe={idDe} seleccion={sel} onSeleccion={setSel}
              vacio={ultima ? "No hay resultados para los criterios ingresados." : "Ingrese criterios y presione Buscar."} />

      <div className="acciones-grilla">
        <span className="hint">{sel ? `Seleccionado: ${nombreDe(filas.find((f) => idDe(f) === sel) || {})}` : "Seleccione un elemento de la lista."}</span>
        <button type="button" className="btn btn--secondary" disabled={!sel} onClick={() => setVista({ modo: "modificar", id: sel, key: Date.now() })}>Modificar</button>
        <button type="button" className="btn btn--danger" disabled={!sel} onClick={eliminar}>Eliminar</button>
      </div>

      {dialogo && <Dialogo key={`${dialogo.titulo}|${dialogo.mensaje}`} {...dialogo} />}
    </Pantalla>
  );
}
