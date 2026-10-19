# Login estándar de AGP (paquete de referencia)

**Norma de IT (2026-10-20).** Todo desarrollo que se despliegue con la Mesa trae el **mismo login de la Mesa**: misma pantalla, mismo flujo
(MSAL en el navegador, PKCE, **sin secreto de cliente**) y misma validación del token en la API. Lo único propio de cada desarrollo es su
**nombre**, que la Mesa fija sola al desplegar. El agente de despliegue **bloquea** si falta esta estructura.

Perfil cubierto hoy: `python-api` (React + Flask, un solo contenedor; ver `ARQUITECTURA-DESPLIEGUE.md`). Otros perfiles se suman después
sin cambiar lo existente.

## Qué copiar al repositorio del desarrollo (misma ruta)

| Archivo del paquete | Va en el repositorio como | Para qué |
|---|---|---|
| `src/config/msal.js` | `src/config/msal.js` | Configura MSAL con lo que entrega la API (`cargarConfigMsal`) y guarda el nombre (`appInfo`). |
| `src/contexts/AuthContext.jsx` | `src/contexts/AuthContext.jsx` | Sesión: restauración silenciosa, `login`, `logout`, `getAuthToken`, `roles`, `isAdmin`. |
| `src/screens/LoginScreen.jsx` | `src/screens/LoginScreen.jsx` | La pantalla de login aprobada, con el nombre del desarrollo. |
| `src/components/AgpLogo.jsx`, `Icon.jsx` | `src/components/` | Piezas que usa la pantalla (si el desarrollo ya las tiene, no se pisan). |
| `backend/src/helpers/auth.py` | `backend/src/helpers/auth.py` | `require_auth`: valida el `id_token` de Entra ID. |
| `backend/src/flask_config/bp_base.py` | ídem (o agregar solo la ruta) | `GET /api/config` (público: tenant, cliente y nombre) y `/api/health`. |
| `.agp/entra.yaml` | `.agp/entra.yaml` | Manifiesto del login: `administradores` y permisos mínimos. |

Dependencias: frontend `@azure/msal-browser`; backend `PyJWT[crypto]` y `requests`.

## Cómo se conecta (resumen)

1. En `src/main.jsx`: `await cargarConfigMsal(API_URL)` **antes** de crear la instancia de MSAL y envolver la app en `<AuthProvider>`
   (ver `main.jsx.example`). Con la imagen de un solo contenedor `API_URL` es `""` (mismo origen).
2. En la app: si `authChecking` muestra «cargando»; si no hay `currentUser`, `<LoginScreen />`; si lo hay, la aplicación.
3. En cada llamada a la API: `Authorization: Bearer ${await getAuthToken()}`; en cada ruta protegida: `@require_auth`.
4. `.agp/entra.yaml`: declara **al menos un administrador** (desarrollador funcional) con el nombre como aparece en Teams y su correo
   @agpglass.com. **No hay secreto de cliente** (`secrets: []`).

## Qué hace la Mesa al desplegar (el desarrollo no necesita acceso a Azure)

Registra la aplicación en Entra ID como **Single-page application**, aprueba `User.Read` y `offline_access`, asigna a los administradores
del manifiesto al rol Admin, entrega `MSAL_CLIENT_ID`/`MSAL_TENANT_ID` y el nombre (`APP_NAME`) como configuración de la Web App. IT asigna
después al resto de personas desde el gestor de roles de la Mesa.

## Nombre propio y local

- En Azure el nombre lo fija la Mesa (`APP_NAME` → `/api/config` → `appName`). En local, defínelo con `APP_NAME=Mi desarrollo` al arrancar la API.
- `DISABLE_AUTH=true` y `DEV_USER_EMAIL` permiten correr la API sin login **solo en tu equipo**; dentro de Azure se ignoran.
- Si cambias el diseño de la pantalla, no es el login estándar: pide a IT una excepción por escrito.
