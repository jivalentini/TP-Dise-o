import { createRef, useEffect, useMemo, useState } from "react";

/** Estado de un formulario de alta/modificación: carga el registro, guarda y expone el error del backend. */
export default function useFormulario({ modo, id, inicial, obtener, guardar, onGuardado, campos }) {
  const [datos, setDatos] = useState(inicial);
  const [error, setError] = useState(null);
  const [cargando, setCargando] = useState(modo === "modificar");
  const [guardando, setGuardando] = useState(false);
  const refs = useMemo(() => Object.fromEntries(campos.map((c) => [c, createRef()])), []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (modo !== "modificar") return;
    obtener(id)
      .then((d) => setDatos(d))
      .catch(setError)
      .finally(() => setCargando(false));
  }, [modo, id]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const campo = error?.campo || error?.campos?.[0];
    if (campo && refs[campo]?.current) refs[campo].current.focus();
  }, [error, refs]);

  const set = (campo, transform = (v) => v) => (e) => setDatos((d) => ({ ...d, [campo]: transform(e.target.value) }));

  async function submit(e) {
    e?.preventDefault();
    if (guardando) return;
    setGuardando(true);
    try {
      const r = await guardar(datos);
      setError(null);
      onGuardado(r);
    } catch (err) {
      setError(err);
    } finally {
      setGuardando(false);
    }
  }

  const invalido = (campo) => !!error && (error.campo === campo || error.campos?.includes(campo));

  return { datos, setDatos, set, error, setError, cargando, guardando, submit, refs, invalido };
}
