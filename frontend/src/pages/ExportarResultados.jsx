import { useState } from "react";
import { exportacion as api } from "../api.js";
import { Campo, Dialogo, Grilla, PanelErrores, Pantalla, fecha, upper } from "../components/ui.jsx";

/** Pasos 7 a 9: el usuario elige carpeta y nombre (si el navegador lo permite) y se guarda el archivo. */
async function guardarArchivo(blob, nombre) {
  if (window.showSaveFilePicker) {
    try {
      const handle = await window.showSaveFilePicker({ suggestedName: nombre, types: [{ description: "Archivo CSV", accept: { "text/csv": [".csv"] } }] });
      const w = await handle.createWritable();
      await w.write(blob);
      await w.close();
      return true;
    } catch (e) {
      if (e.name === "AbortError") return false; // canceló el diálogo de guardado
    }
  }
  const url = URL.createObjectURL(blob);
  const a = Object.assign(document.createElement("a"), { href: url, download: nombre });
  a.click();
  URL.revokeObjectURL(url);
  return true;
}

// CU007 – Exportar Resultados
export default function ExportarResultados({ onSalir }) {
  const [filtros, setFiltros] = useState({ nombre_funcion: "", empresa: "", fecha_desde: "", fecha_hasta: "" });
  const [funciones, setFunciones] = useState(null);
  const [funcion, setFuncion] = useState(null);
  const [candidatos, setCandidatos] = useState([]);
  const [error, setError] = useState(null);
  const [dialogo, setDialogo] = useState(null);
  const fechas = { fecha_desde: filtros.fecha_desde, fecha_hasta: filtros.fecha_hasta };

  async function buscar(e) {
    e.preventDefault();
    try {
      setFunciones(await api.buscarFunciones(filtros));
      setFuncion(null);
      setCandidatos([]);
      setError(null);
    } catch (err) {
      setError(err);
    }
  }

  async function elegir(codigo) {
    setFuncion(codigo);
    try {
      setCandidatos(await api.candidatosEvaluados(codigo, fechas));
    } catch (err) {
      setError(err);
    }
  }

  async function exportar() {
    if (!funcion) {
      setDialogo({ titulo: "Exportar", mensaje: "Debe seleccionar una función.", tipo: "error", botones: [{ label: "Aceptar", primario: true, onClick: () => setDialogo(null) }] });
      return;
    }
    try {
      const { nombre, blob } = await api.csv(funcion, fechas);
      if (await guardarArchivo(blob, nombre)) {
        setDialogo({ titulo: "Exportación finalizada", mensaje: `Se generó el archivo ${nombre}.`, botones: [{ label: "Aceptar", primario: true, onClick: onSalir }] });
      }
    } catch (err) {
      setError(err);
    }
  }

  const set = (campo, t = (v) => v) => (e) => setFiltros({ ...filtros, [campo]: t(e.target.value) });
  return (
    <Pantalla titulo="Exportar resultados" pie={<button type="button" className="btn btn--secondary" onClick={onSalir}>Cancelar</button>}>
      <form className="criterios" onSubmit={buscar}>
        <Campo label="Nombre de Función o puesto"><input value={filtros.nombre_funcion} onChange={set("nombre_funcion", upper)} /></Campo>
        <Campo label="Empresa"><input value={filtros.empresa} onChange={set("empresa", upper)} /></Campo>
        <Campo label="Fin del cuestionario desde"><input type="date" value={filtros.fecha_desde} onChange={set("fecha_desde")} /></Campo>
        <Campo label="Fin del cuestionario hasta"><input type="date" value={filtros.fecha_hasta} onChange={set("fecha_hasta")} /></Campo>
        <div className="criterios__botones"><button type="submit" className="btn btn--primary">Buscar</button></div>
      </form>
      <PanelErrores error={error} />
      {funciones && (
        <>
          <h3 className="subtitulo">Funciones con candidatos evaluados</h3>
          <Grilla columnas={[{ titulo: "Código", valor: (p) => p.codigo }, { titulo: "Función", valor: (p) => p.nombre_puesto }, { titulo: "Empresa", valor: (p) => p.empresa }]}
                  filas={funciones} idDe={(p) => p.codigo} seleccion={funcion} onSeleccion={elegir} />
        </>
      )}
      {funcion && (
        <>
          <h3 className="subtitulo">Candidatos evaluados</h3>
          <Grilla
            columnas={[
              { titulo: "Apellido", valor: (c) => c.apellido }, { titulo: "Nombre", valor: (c) => c.nombre },
              { titulo: "Tipo doc.", valor: (c) => c.tipo_documento }, { titulo: "Documento", valor: (c) => c.nro_documento },
              { titulo: "Nro candidato", valor: (c) => c.nro_candidato }, { titulo: "Fin del cuestionario", valor: (c) => fecha(c.fecha_finalizacion_cuestionario) },
            ]}
            filas={candidatos} idDe={(c) => c.nro_candidato}
          />
        </>
      )}
      {funciones && (
        <div className="acciones-grilla">
          <button type="button" className="btn btn--primary" onClick={exportar}>Exportar</button>
        </div>
      )}
      {dialogo && <Dialogo key={dialogo.mensaje} {...dialogo} />}
    </Pantalla>
  );
}
