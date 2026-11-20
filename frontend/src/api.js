const FALLBACK = "No se pudo completar la operación. Intente nuevamente.";
const KEY = "session";

export class ApiError extends Error {
  constructor(message, { status, errores = [], campo = null, campos = [] } = {}) {
    super(message);
    this.status = status;
    this.errores = errores;
    this.campo = campo;
    this.campos = campos;
  }
}

let onExpired = () => {};
export const setOnExpired = (fn) => (onExpired = fn);

function token() {
  try {
    return JSON.parse(sessionStorage.getItem(KEY))?.token;
  } catch {
    return null;
  }
}

function qs(params = {}) {
  const p = Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== "");
  return p.length ? "?" + new URLSearchParams(p).toString() : "";
}

async function request(method, path, { body, params, raw } = {}) {
  let res;
  try {
    res = await fetch(`/api${path}${qs(params)}`, {
      method,
      headers: {
        ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
        ...(token() ? { Authorization: `Bearer ${token()}` } : {}),
      },
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError("No se pudo conectar con el servidor.");
  }
  if (res.ok && raw) return res;
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    if (res.status === 401 && !path.startsWith("/auth")) onExpired();
    throw new ApiError(typeof data?.detail === "string" ? data.detail : FALLBACK, {
      status: res.status,
      errores: data?.errores,
      campo: data?.campo,
      campos: data?.campos,
    });
  }
  return data;
}

const get = (path, params) => request("GET", path, { params });
const post = (path, body) => request("POST", path, { body });
const put = (path, body) => request("PUT", path, { body });
const del = (path) => request("DELETE", path);
const enc = encodeURIComponent;

// ---- CU001
export const loginConsultor = (username, password) => post("/auth/consultor", { username, password });
export const loginCandidato = (tipoDocumento, nroDocumento, clave) =>
  post("/auth/candidato", { tipo_documento: tipoDocumento, nro_documento: nroDocumento, clave });

// ---- ABM genérico (CU008–024, 029–031)
const abm = (base) => ({
  buscar: (criterios) => get(base, criterios),
  obtener: (id) => get(`${base}/${enc(id)}`),
  alta: (datos) => post(base, datos),
  modificar: (id, datos) => put(`${base}/${enc(id)}`, datos),
  puedeEliminar: (id) => get(`${base}/${enc(id)}/puede-eliminar`),
  eliminar: (id) => del(`${base}/${enc(id)}`),
});

export const puestos = { ...abm("/puestos"), generarIA: (d) => post("/puestos/generar-ia", d) };
export const competencias = abm("/competencias");
export const factores = { ...abm("/factores"), ordenes: (codComp) => get(`/factores/ordenes/${enc(codComp)}`) };
export const preguntas = { ...abm("/preguntas"), generarIA: (d) => post("/preguntas/generar-ia", d) };
export const opcionesRespuesta = abm("/opciones-respuesta");

// ---- CU026
export const cuestionario = {
  ingresar: () => post("/cuestionario/ingresar"),
  estado: () => get("/cuestionario/estado"),
  comenzar: () => post("/cuestionario/comenzar"),
  responderBloque: (bloque) => post("/cuestionario/bloque", bloque),
};

// ---- CU027
export const reporteComparativo = {
  buscarFunciones: (c) => get("/reporte-comparativo/funciones", c),
  candidatosEvaluados: (codigo, filtros) => get(`/funciones/${enc(codigo)}/candidatos-evaluados`, filtros),
  emitir: (codigo_puesto, nro_candidato) => get("/reporte-comparativo", { codigo_puesto, nro_candidato }),
};

// ---- CU028
export const ordenMerito = {
  buscarPuestos: (c) => get("/orden-merito/puestos", c),
  evaluaciones: (codigo) => get(`/orden-merito/puestos/${enc(codigo)}/evaluaciones`),
  emitir: (codigo_puesto, evaluaciones) => post("/orden-merito", { codigo_puesto, evaluaciones }),
  impresora: () => get("/impresora"),
  imprimir: (codigo_puesto, evaluaciones) => post("/orden-merito/imprimir", { codigo_puesto, evaluaciones }),
};

// ---- CU007
export const exportacion = {
  buscarFunciones: (c) => get("/exportacion/funciones", c),
  candidatosEvaluados: (codigo, filtros) => get(`/funciones/${enc(codigo)}/candidatos-evaluados`, filtros),
  async csv(codigo_puesto, filtros) {
    const res = await request("GET", "/exportacion/csv", { params: { codigo_puesto, ...filtros }, raw: true });
    const nombre = decodeURIComponent(res.headers.get("X-Nombre-Archivo") || "resultados.csv");
    return { nombre, blob: await res.blob() };
  },
};
