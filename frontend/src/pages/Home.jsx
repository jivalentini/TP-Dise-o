import { useState } from "react";
import Banner from "../components/Banner.jsx";
import Competencias from "./Competencias.jsx";
import Cuestionario from "./Cuestionario.jsx";
import ExportarResultados from "./ExportarResultados.jsx";
import Factores from "./Factores.jsx";
import OpcionesRespuesta from "./OpcionesRespuesta.jsx";
import OrdenMerito from "./OrdenMerito.jsx";
import Preguntas from "./Preguntas.jsx";
import Puestos from "./Puestos.jsx";
import ReporteComparativo from "./ReporteComparativo.jsx";

// Opciones del perfil Consultor. `pantalla: null` = CU todavía no integrado en esta rama.
const SECCIONES = [
  { titulo: "Datos básicos", opciones: [
    { label: "Puestos", cu: "CU008", pantalla: Puestos },
    { label: "Competencias", cu: "CU012", pantalla: Competencias },
    { label: "Factores", cu: "CU016", pantalla: Factores },
    { label: "Preguntas", cu: "CU020", pantalla: Preguntas },
    { label: "Opciones de respuesta", cu: "CU024", pantalla: OpcionesRespuesta },
  ] },
  { titulo: "Evaluación", opciones: [
    { label: "Importar candidatos", cu: "CU006", pantalla: null },
    { label: "Evaluar candidatos", cu: "CU025", pantalla: null },
    { label: "Exportar resultados", cu: "CU007", pantalla: ExportarResultados },
  ] },
  { titulo: "Reportes", opciones: [
    { label: "Reporte comparativo", cu: "CU027", pantalla: ReporteComparativo },
    { label: "Orden de mérito", cu: "CU028", pantalla: OrdenMerito },
  ] },
];

export default function Home({ session, onLogout, onIngresoRegistrado }) {
  const [actual, setActual] = useState(null);
  const esConsultor = session.perfil === "CONSULTOR";

  if (!esConsultor) {
    return (
      <div className="page">
        <Banner title="Cuestionario" />
        <main className="main">
          <Cuestionario session={session} onIngresoRegistrado={onIngresoRegistrado} onSalir={onLogout} />
        </main>
      </div>
    );
  }

  const Pantalla = actual?.pantalla;
  return (
    <div className="page">
      <Banner title={actual ? actual.label : "Menú principal"} />
      <main className="main main--top">
        {Pantalla ? (
          <Pantalla onSalir={() => setActual(null)} />
        ) : (
          <section className="panel panel--wide">
            <h2>Bienvenido, {session.nombre}</h2>
            <p className="hint">Opciones disponibles para el perfil Consultor.</p>
            {SECCIONES.map((s) => (
              <div key={s.titulo} className="menu-seccion">
                <h3>{s.titulo}</h3>
                <div className="menu">
                  {s.opciones.map((o) => (
                    <button key={o.label} type="button" className="menu__opcion" disabled={!o.pantalla}
                            title={o.pantalla ? undefined : `${o.cu}: pendiente de integrar en esta rama`} onClick={() => setActual(o)}>
                      <strong>{o.label}</strong>
                      <span>{o.cu}</span>
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </section>
        )}
      </main>
      {!actual && (
        <footer className="footer no-print">
          <button type="button" className="btn btn--secondary" onClick={onLogout}>Salir</button>
        </footer>
      )}
    </div>
  );
}
