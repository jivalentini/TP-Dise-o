import { useState } from "react";
import { reporteComparativo as api } from "../api.js";
import { Campo, Grilla, PanelErrores, Pantalla, fecha, upper } from "../components/ui.jsx";

const COL_CANDIDATOS = [
  { titulo: "Apellido", valor: (c) => c.apellido },
  { titulo: "Nombre", valor: (c) => c.nombre },
  { titulo: "Tipo doc.", valor: (c) => c.tipo_documento },
  { titulo: "Documento", valor: (c) => c.nro_documento },
  { titulo: "Nro candidato", valor: (c) => c.nro_candidato },
  { titulo: "Fin del cuestionario", valor: (c) => fecha(c.fecha_finalizacion_cuestionario) },
];

/** Gráfico de barras: requerido vs obtenido por competencia (escala 0 a 10). */
function Grafico({ items }) {
  const fila = 54, izq = 210, ancho = 420, top = 28;
  const alto = top + items.length * fila + 30;
  const x = (v) => izq + (v / 10) * ancho;
  return (
    <svg className="grafico" viewBox={`0 0 ${izq + ancho + 60} ${alto}`} role="img" aria-label="Gráfico comparativo requerido vs obtenido">
      <g className="grafico__leyenda">
        <rect x={izq} y={4} width={12} height={12} className="barra--req" /><text x={izq + 18} y={14}>Requerido</text>
        <rect x={izq + 110} y={4} width={12} height={12} className="barra--ok" /><text x={izq + 128} y={14}>Obtenido</text>
        <rect x={izq + 215} y={4} width={12} height={12} className="barra--mal" /><text x={izq + 233} y={14}>Obtenido (bajo el mínimo)</text>
      </g>
      {[0, 2, 4, 6, 8, 10].map((v) => (
        <g key={v}>
          <line x1={x(v)} x2={x(v)} y1={top} y2={alto - 24} className="grafico__guia" />
          <text x={x(v)} y={alto - 8} textAnchor="middle" className="grafico__eje">{v}</text>
        </g>
      ))}
      {items.map((it, i) => {
        const y = top + i * fila + 6;
        const ok = it.puntaje_obtenido >= it.ponderacion_requerida;
        return (
          <g key={it.nombre_competencia}>
            <text x={izq - 10} y={y + 22} textAnchor="end" className="grafico__label">{it.nombre_competencia}</text>
            <rect x={izq} y={y} width={Math.max(1, x(it.ponderacion_requerida) - izq)} height={18} rx={3} className="barra--req" />
            <text x={x(it.ponderacion_requerida) + 6} y={y + 13} className="grafico__valor">{it.ponderacion_requerida}</text>
            <rect x={izq} y={y + 21} width={Math.max(1, x(it.puntaje_obtenido) - izq)} height={18} rx={3} className={ok ? "barra--ok" : "barra--mal"} />
            <text x={x(it.puntaje_obtenido) + 6} y={y + 34} className="grafico__valor">{it.puntaje_obtenido}</text>
          </g>
        );
      })}
    </svg>
  );
}

// CU027 – Emitir Reporte Comparativo
export default function ReporteComparativo({ onSalir }) {
  const [filtros, setFiltros] = useState({ nombre_funcion: "", empresa: "" });
  const [funciones, setFunciones] = useState(null);
  const [funcion, setFuncion] = useState(null);
  const [candidatos, setCandidatos] = useState([]);
  const [candidato, setCandidato] = useState(null);
  const [reporte, setReporte] = useState(null);
  const [error, setError] = useState(null);

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

  async function elegirFuncion(codigo) {
    setFuncion(codigo);
    setCandidato(null);
    try {
      setCandidatos(await api.candidatosEvaluados(codigo));
      setError(null);
    } catch (err) {
      setError(err);
    }
  }

  async function comparar() {
    if (!candidato) return setError(new Error("Debe seleccionar al menos un candidato de la lista."));
    try {
      setReporte(await api.emitir(funcion, candidato));
      setError(null);
    } catch (err) {
      setError(err);
    }
  }

  if (reporte) {
    return (
      <Pantalla
        titulo="Reporte comparativo"
        pie={<>
          <button type="button" className="btn btn--primary" onClick={() => window.print()}>Imprimir</button>
          <button type="button" className="btn btn--secondary" onClick={() => setReporte(null)}>Cancelar</button>
        </>}
      >
        <div className="reporte-cabecera">
          <div><span>Función</span><strong>{reporte.nombre_puesto}</strong></div>
          <div><span>Empresa</span><strong>{reporte.empresa}</strong></div>
          <div><span>Candidato</span><strong>{reporte.candidato}</strong></div>
          <div><span>Cuestionario finalizado</span><strong>{fecha(reporte.fecha_finalizacion_cuestionario)}</strong></div>
        </div>
        <Grilla
          columnas={[
            { titulo: "Competencia", valor: (i) => i.nombre_competencia },
            { titulo: "Requerido", valor: (i) => i.ponderacion_requerida.toFixed(2), alinear: "right" },
            { titulo: "Obtenido", valor: (i) => i.puntaje_obtenido.toFixed(2), alinear: "right" },
            { titulo: "Diferencia", alinear: "right", valor: (i) => {
              const d = i.puntaje_obtenido - i.ponderacion_requerida;
              return <span className={d >= 0 ? "ok" : "mal"}>{d >= 0 ? "+" : ""}{d.toFixed(2)}</span>;
            } },
          ]}
          filas={reporte.items}
          idDe={(i) => i.nombre_competencia}
        />
        <Grafico items={reporte.items} />
      </Pantalla>
    );
  }

  return (
    <Pantalla titulo="Reporte comparativo" pie={<button type="button" className="btn btn--secondary" onClick={onSalir}>Salir</button>}>
      <form className="criterios" onSubmit={buscar}>
        <Campo label="Nombre de Función"><input value={filtros.nombre_funcion} onChange={(e) => setFiltros({ ...filtros, nombre_funcion: upper(e.target.value) })} /></Campo>
        <Campo label="Empresa"><input value={filtros.empresa} onChange={(e) => setFiltros({ ...filtros, empresa: upper(e.target.value) })} /></Campo>
        <div className="criterios__botones"><button type="submit" className="btn btn--primary">Buscar</button></div>
      </form>
      <PanelErrores error={error} />
      {funciones && (
        <>
          <h3 className="subtitulo">Funciones</h3>
          <Grilla columnas={[{ titulo: "Código", valor: (p) => p.codigo }, { titulo: "Función", valor: (p) => p.nombre_puesto }, { titulo: "Empresa", valor: (p) => p.empresa }]}
                  filas={funciones} idDe={(p) => p.codigo} seleccion={funcion} onSeleccion={elegirFuncion} />
        </>
      )}
      {funcion && (
        <>
          <h3 className="subtitulo">Candidatos evaluados en la función</h3>
          <Grilla columnas={COL_CANDIDATOS} filas={candidatos} idDe={(c) => c.nro_candidato} seleccion={candidato} onSeleccion={setCandidato}
                  vacio="No hay candidatos con el cuestionario completo en esta función." />
          <div className="acciones-grilla">
            <button type="button" className="btn btn--primary" onClick={comparar}>Comparar</button>
            <button type="button" className="btn btn--secondary" onClick={onSalir}>Cancelar</button>
          </div>
        </>
      )}
    </Pantalla>
  );
}
