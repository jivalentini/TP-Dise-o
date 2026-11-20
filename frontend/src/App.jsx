import { useEffect, useState } from "react";
import { setOnExpired } from "./api.js";
import Login from "./pages/Login.jsx";
import Home from "./pages/Home.jsx";

const KEY = "session";

export default function App() {
  const [session, setSession] = useState(() => {
    try {
      return JSON.parse(sessionStorage.getItem(KEY));
    } catch {
      return null;
    }
  });

  const guardar = (s) => {
    if (s) sessionStorage.setItem(KEY, JSON.stringify(s));
    else sessionStorage.removeItem(KEY);
    setSession(s);
  };

  // El candidato que se autentica inicia un nuevo acceso al cuestionario (CU026, precondición de accesos)
  const login = (s) => guardar(s.perfil === "CANDIDATO" ? { ...s, ingresoPendiente: true } : s);
  const logout = () => guardar(null);

  useEffect(() => setOnExpired(logout), []);

  return session ? (
    <Home session={session} onLogout={logout} onIngresoRegistrado={() => guardar({ ...session, ingresoPendiente: false })} />
  ) : (
    <Login onLogin={login} />
  );
}
