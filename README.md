# TP 2026 – Evaluación de candidatos (Capit@l Humano)

Implementados: **CU001** y **CU007 a CU033** (excepto CU025), sobre la arquitectura de las entregas 1 a 6
(ver `docs/ARQUITECTURA.md`). CU006 y CU025 quedan con sus métodos `pendiente(...)` para integrar.

## Puesta en marcha

### 1. Base de datos
```bash
docker compose up -d
```

### 2. Backend (Python 3.11+)
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python -m app.seed               # se puede volver a correr: solo agrega lo que falta
uvicorn app.main:app --reload    # http://localhost:8000/docs
```

### 3. Frontend
```bash
cd frontend
npm install
npm run dev                      # http://localhost:5173
```

## Credenciales de prueba (AUTH_MODE=mock)
- Consultor: usuario `CONSULTOR` / contraseña `consultor123`
- Candidato con cuestionario **Activo** (para probar el CU026): tipo `DNI`, número `12345678`, clave `AB12CD34`

El seed también carga 3 competencias, 6 factores, 17 preguntas, 3 opciones de respuesta, 2 puestos y una
evaluación ya rendida del puesto P001 (4 cuestionarios Completos, 1 Incompleto, 1 Sin Contestar) para probar
CU007, CU027 y CU028.

Para usar el LDAP real, poner `AUTH_MODE=ldap` y completar `LDAP_SERVER` y
`LDAP_USER_DN_TEMPLATE` en `backend/.env` (en producción `ldaps://servidor:636`).
El consultor debe existir también en la tabla `consultor` (legajo + username).

## Servicio de IA (CU033 y alta de puestos con GenAI)
- `IA_MODE=mock` (por defecto): genera contenido de ejemplo sin credenciales.
- `IA_MODE=anthropic`: usa la API de Claude con `IA_API_KEY` (y opcionalmente `IA_MODEL`).
- `IA_MODE=api`: REST propio en `IA_BASE_URL` (`POST /preguntas`, `POST /puestos`).

Si el servicio falla se muestra *"Ocurrió un error al comunicarse con el servicio de IA. Intente nuevamente más tarde"* (CU033 4.A).

## CU032 – Finalizar cuestionarios
Corre solo cada `BATCH_INTERVALO_MINUTOS` mientras el backend está levantado. También se puede ejecutar a mano
o desde el programador de tareas del SO:
```bash
python -m app.batch
```

## Pruebas
```bash
cd backend
pip install pytest
python -m pytest -q          # SQLite temporal; con TEST_DATABASE_URL=... usa una BD Postgres vacía
```
