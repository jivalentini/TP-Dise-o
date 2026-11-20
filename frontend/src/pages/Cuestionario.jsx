import { useEffect, useRef, useState } from "react";
import { cuestionario as api } from "../api.js";
import { Dialogo, PanelErrores } from "../components/ui.jsx";

const ingreso = { token: null, promesa: null }; // evita contar dos accesos si el efecto se ejecuta dos veces (StrictMode)

// CU026 – Completar Cuestionario
export default function Cuestionario({ session, onIngresoRegistrado, onSalir }) {
  const [estado, setEstado] = useState(null);
  const [respuestas, setRespuestas] = useState({});
  const [error, setError] = useState(null);
  const [enviando, setEnviando] = useState(false);
  const [confirmarSalida, setConfirmarSalida] = useState(false);
  const arriba = useRef(null);

  useEffect(() => {
    let p;
    if (session.ingresoPendiente) {
      if (ingreso.token !== session.token) {
        ingreso.token = session.token;
        ingreso.promesa = api.ingresar().finally(() => onIngresoRegistrado());
      }
      p = ingreso.promesa;
    } else {
      p = api.estado();
    }
    p.then(setEstado).catch(setError);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    setRespuestas({});
    arriba.current?.scrollIntoView({ behavior: "smooth" });
  }, [estado?.bloque?.nro_bloque]);

  async function ejecutar(fn) {
    setEnviando(true);
    try {
      setEstado(await fn());
      setError(null);
    } catch (e) {
      setError(e); // 6.A: mantiene el bloque y las respuestas ya marcadas
    } finally {
      setEnviando(false);
    }
  }

  const enviarBloque = (e) => {
    e.preventDefault();
    const b = estado.bloque;
    ejecutar(() =>
      api.responderBloque({
        id_cuestionario: String(session.cuestionario_id),
        nro_bloque: b.nro_bloque,
        respuestas: Object.entries(respuestas).map(([id_pregunta, orden]) => ({ id_pregunta, orden_opcion_seleccionada: orden })),
      })
    );
  };

  if (!estado) {
    return <section className="panel panel--wide"><PanelErrores error={error} />{!error && <p className="hint">Cargando cuestionario…</p>}</section>;
  }

  if (estado.accion === "FINALIZADO") {
    const ok = estado.estado === "Completo";
    return (
      <section className={`panel panel--wide fin ${ok ? "fin--ok" : "fin--mal"}`}>
        <div className="fin__icono" aria-hidden="true">{ok ? "✓" : "!"}</div>
        <h2>{ok ? "¡Cuestionario completado!" : "No es posible continuar"}</h2>
        <p>{estado.mensaje}</p>
        <button type="button" className="btn btn--primary" onClick={onSalir} autoFocus>Salir</button>
      </section>
    );
  }

  if (estado.accion === "INSTRUCCIONES") {
    return (
      <section className="panel panel--wide">
        <h2>Cuestionario – Instrucciones</h2>
        <div className="instrucciones">{estado.instrucciones}</div>
        <PanelErrores error={error} />
        <div className="form-botones">
          <button type="button" className="btn btn--primary" disabled={enviando} onClick={() => ejecutar(api.comenzar)} autoFocus>Aceptar</button>
          <button type="button" className="btn btn--secondary" onClick={onSalir}>Cancelar</button>
        </div>
      </section>
    );
  }

  const b = estado.bloque;
  const ultimo = b.nro_bloque === b.total_bloques;
  const sinResponder = new Set(error?.campos || []);
  return (
    <section className="panel panel--cuestionario" ref={arriba}>
      <div className="wizard">
        <div className="wizard__paso">Bloque {b.nro_bloque} de {b.total_bloques}</div>
        <div className="wizard__barra"><div style={{ width: `${((b.nro_bloque - 1) / b.total_bloques) * 100}%` }} /></div>
      </div>
      <PanelErrores error={error} />
      <form onSubmit={enviarBloque}>
        {b.preguntas.map((p, n) => (
          <fieldset key={p.id_pregunta} className={`pregunta ${sinResponder.has(p.id_pregunta) && !respuestas[p.id_pregunta] ? "pregunta--falta" : ""}`}>
            <legend><span className="pregunta__nro">{n + 1}</span>{p.enunciado}</legend>
            <div className="pregunta__opciones">
              {p.opciones.map((o) => (
                <label key={o.orden} className={respuestas[p.id_pregunta] === o.orden ? "elegida" : ""}>
                  <input type="radio" name={`p${p.id_pregunta}`} checked={respuestas[p.id_pregunta] === o.orden}
                         onChange={() => setRespuestas({ ...respuestas, [p.id_pregunta]: o.orden })} />
                  {o.descripcion}
                </label>
              ))}
            </div>
          </fieldset>
        ))}
        <p className="hint">Una vez que avance no podrá volver a este bloque.</p>
        <div className="form-botones">
          <button type="submit" className="btn btn--primary" disabled={enviando}>{ultimo ? "Finalizar" : "Siguiente"}</button>
          <button type="button" className="btn btn--secondary" onClick={() => setConfirmarSalida(true)}>Salir y continuar más tarde</button>
        </div>
      </form>
      {confirmarSalida && (
        <Dialogo titulo="Salir del cuestionario" mensaje="Las respuestas de este bloque que aún no envió no se guardarán. Podrá continuar desde este bloque al volver a ingresar (se contará un nuevo acceso)."
                 botones={[{ label: "Salir", primario: true, onClick: onSalir }, { label: "Seguir respondiendo", onClick: () => setConfirmarSalida(false) }]} />
      )}
    </section>
  );
}
