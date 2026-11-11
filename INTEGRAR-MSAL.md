# Integrar MSAL paso a paso (login estándar de AGP con `@azure/msal-browser` 5.x)

**Versión probada: `@azure/msal-browser` 5.29.0** (la que usan la plantilla `templates/auth-estandar/` y los starters; exporta `@azure/msal-browser/redirect-bridge`).
Con 5.x el popup de Microsoft ya no se resuelve volviendo a la raíz del sitio: necesita una **página puente**. Esta guía deja el login funcionando sin ese error y es la referencia de
`agpctl login check`, del Agente de Despliegue y de la regla de `OBLIGATORIOS-DEL-DESARROLLO.md` §6.

## El síntoma, en una línea

La persona pulsa «Iniciar sesión con Microsoft», se abre la ventana emergente, vuelve a mostrar **la pantalla de login** (o se queda cargando) y la aplicación dice
**«Error al iniciar sesión. Intenta de nuevo.»**. No hay error en la consola del navegador y `GET /api/config` responde bien. Pasó en AGPTS y en SmartBending.

## La causa

`redirectUri` apunta a la raíz del sitio (`window.location.origin`) con `@azure/msal-browser` ≥ 5. El popup vuelve a la raíz, carga **otra copia de la aplicación** con su pantalla
de login y MSAL nunca recibe la respuesta de Microsoft (`monitor_popup_timeout`, `hash_empty_error`). La plantilla del kit tenía ese `redirectUri` desde el 2026-10-19 hasta este arreglo.

## ¿Me aplica? Cómo detectarlo en un repositorio

| Señal | Dónde mirar | Mala (el error) | Buena |
|---|---|---|---|
| Flujo de login | llamadas a MSAL en el código de la app | `loginPopup` / `acquireTokenPopup` / `logoutPopup` (popup: **aplica todo lo de esta guía**) | `loginRedirect` / `logoutRedirect` / `acquireTokenRedirect` + `handleRedirectPromise`: **no necesita página puente** (ver abajo) |
| Versión de MSAL | `package.json` del frontend | `@azure/msal-browser` `5.x` o superior | (con 4.x no aplica; se recomienda actualizar) |
| Retorno del login | `src/config/msal.js` o `.ts` | `redirectUri: window.location.origin` y sin `postLogoutRedirectUri` | `redirectUri` y `postLogoutRedirectUri` = `${window.location.origin}/auth/redirect` |
| Registro en Entra | `.agp/entra.yaml` | `redirectUriPath: /` | `redirectUriPath: /auth/redirect` (igual que el código) |
| Página puente | `auth/redirect.html` y `src/auth/redirect.js` | no existen | existen; el script llama a `broadcastResponseToMainFrame()` y la página no tiene `id="root"` |
| Compilación | `vite.config.*` | solo `index.html` | `build.rollupOptions.input` con `index.html` **y** `auth/redirect.html` |
| Servidor / hosting | Flask/Node, `serve.json`, `staticwebapp.config.json`, nginx | la ruta `/auth/redirect` cae en el fallback de la SPA (`index.html`) | la ruta sirve `dist/auth/redirect.html` |
| Imagen | `.dockerignore` | lista blanca (`*`) sin `!frontend/auth` | `!frontend/auth` después de `frontend/*` |

### ¿Usa popup o redirección? Solo el popup necesita la página puente

El error nace en el flujo de **popup**: la ventana emergente vuelve a `redirectUri` y MSAL 5 espera que ahí haya una página puente. Si la aplicación inicia sesión por
**redirección de página completa** (`loginRedirect`, `logoutRedirect`, `acquireTokenRedirect` y `handleRedirectPromise()` al arrancar), la misma página regresa a `redirectUri`, la
SPA recoge la respuesta y la raíz como `redirectUri` **funciona**: no añadas página puente ni cambies `entra.yaml` (cambiar un desarrollo que hoy funciona solo agrega riesgo).
Caso real: Portal SAC (`AGP_CO_FINANCE_PORTAL_SAC`, `frontend/src/auth/AuthGate.jsx`, MSAL ^5.25 con `loginRedirect`). `agpctl login check` detecta el flujo: con redirección devuelve
`valid: true` y un aviso; con popup (o si no encuentra ninguna llamada de login) exige la página puente. Si algún día cambias a `loginPopup`, la página puente pasa a ser obligatoria.

**Comprobación automática:** `python -m agpctl login check --repo .` (solo lectura, devuelve `issues` con «Cómo corregirlo» y código de salida 1 si algo falla).

### ¿Mi plantilla es la vieja?

- **Plantilla del kit** (`templates/auth-estandar`): el `redirectUri` en la raíz entró con el commit `e5f6eb4` (2026-10-19, «Login estándar de AGP: paquete de referencia») y estuvo en
  `main` y en el tag **`v4.0.0-rc.2`** (2026-11-04) hasta este arreglo. Si copiaste `src/config/msal.js` de esa versión, te aplica. El tag `v4.0.0-rc.1` no traía el paquete.
- **Starters** (`agp-dev-starter-template`, `-node-api`, `-react-static`): **nunca trajeron código de login con `@azure/msal-browser`** (el historial de git no tiene ninguna copia). El de
  `node-api` trae solo un ejemplo de servidor con `@azure/msal-node` (flujo de código, no popup), al que no le aplica. Quien tuvo el error lo copió del paquete del kit.
- **Desarrollos ya arreglados, como referencia:** Web SmartBending (PR #281, commit `41ed723`) y AGPTS (`AGP_CO_PEOPLE_AGPTS`, PR #7, que además tuvo que añadir `!frontend/auth` al `.dockerignore`).

## Los pasos

1. **Fija la versión** en el `package.json` del frontend: `"@azure/msal-browser": "5.29.0"` (exacta; es la que se prueba).
2. **Copia del kit** (`templates/auth-estandar/`, misma ruta): `auth/redirect.html`, `src/auth/redirect.js` (+ `redirect.test.js`), `src/config/msal.js`, `src/contexts/AuthContext.jsx`.
   `msal.js` ya trae `redirectUri` y `postLogoutRedirectUri` = `${origin}/auth/redirect`; `AuthContext.jsx` bloquea el doble clic y da mensajes claros por código de error.
3. **Compila las dos páginas:** adapta tu `vite.config.js` a `vite.config.example.js` (`build.rollupOptions.input` con `index.html` y `auth/redirect.html`, y la reescritura de
   `/auth/redirect` en `vite dev` y `vite preview`; los hooks `configureServer` y `configurePreviewServer` van **con llaves**, sin devolver `use()`).
4. **Sirve la ruta** `GET /auth/redirect` con el HTML real, nunca con el fallback de la SPA, sin caché y sin el encabezado `Cross-Origin-Opener-Policy`:
   - Flask: `backend/src/flask_config/bp_retorno_msal.py` del kit; regístralo **antes** del fallback de la SPA.
   - `serve` (`serve -s dist`): `public/serve.json` con `{"rewrites": [{"source": "/auth/redirect", "destination": "/auth/redirect.html"}]}`.
   - Azure Static Web Apps: en `staticwebapp.config.json`, una ruta `/auth/redirect` → `/auth/redirect.html` y `/auth/*` fuera del `navigationFallback`.
   - Node: una ruta que responda `dist/auth/redirect.html` (ver el starter `node-api`).
5. **`.agp/entra.yaml`:** `redirectUriPath: /auth/redirect`. La Mesa lo registra como URI de «Aplicación de una sola página» en Entra ID **al ejecutar la fase «entra»**: si el desarrollo ya
   estaba desplegado con `redirectUriPath: /`, hay que volver a ejecutarla (o pedir a IT que agregue ese URI) o Entra rechaza el retorno (`AADSTS50011`).
6. **`.dockerignore`:** si es una lista blanca, deja pasar la página puente, por ejemplo `!frontend/auth` **después** de `frontend/*` (ver `templates/auth-estandar/.dockerignore.example`).
   Sin esa regla la imagen se construye sin la página: el build falla o la ruta devuelve 404.
7. **Comprueba:** `python -m agpctl login check --repo .` y las pruebas de la plantilla (`npm test`: la prueba de humo del login falla si vuelve la raíz como `redirectUri` con MSAL 5).
   Antes de pedir el despliegue, el resto de la lista está en `COMO-DEJARLO-FUNCIONAL.md`.

## Si falla después de integrarlo

| Lo que ves | Causa | Arreglo |
|---|---|---|
| «Error al iniciar sesión. Intenta de nuevo.» sin error en consola | `redirectUri` en la raíz, o `/auth/redirect` sirve la SPA | pasos 2 a 4 |
| «Microsoft no pudo devolver el acceso…» (`monitor_popup_timeout` / `hash_empty_error`) | la página puente no se sirve, o el servidor manda `Cross-Origin-Opener-Policy` | paso 4 |
| «El navegador bloqueó la ventana de Microsoft» (`popup_window_error`) | el navegador bloquea ventanas emergentes | permitirlas para el sitio |
| «Ya hay una ventana de Microsoft abierta» (`interaction_in_progress`) | doble clic | cerrar la ventana abierta |
| Página de Microsoft con `AADSTS50011` | el URI registrado en Entra no es el que usa el código | paso 5 |
| Página de Microsoft con `AADSTS9002326` | el URI está registrado como «Web» y no como «Aplicación de una sola página» | corregirlo en Entra o repetir la fase «entra» |
| La imagen no trae `auth/redirect.html` | `.dockerignore` | paso 6 |

## El puente debe mostrar el código de error de Entra

Con MSAL 5, `broadcastResponseToMainFrame()` **relanza** la respuesta cuando Entra devuelve un error (`error=...&error_description=AADSTS...`) y antes limpia el hash. Un `.catch` mudo
deja a la persona con «No se pudo completar el acceso» y «Error al iniciar sesión» sin ningún dato: no se sabe si falta asignar al usuario, el consentimiento o el URI.
La plantilla ya lo resuelve (`src/auth/erroresEntra.js`, `src/auth/redirect.js`, `mensajeDeErrorLogin` de `AuthContext.jsx`):

- El puente lee `window.location.hash` y `search` **antes** de llamar a `broadcastResponseToMainFrame()` y, si falla, muestra «Microsoft respondió: <error> (AADSTS…)» con la causa probable.
- Solo se leen y se muestran el `error` y el código `AADSTS#####`. **Nunca** el `code`, el `state`, los tokens ni el texto libre de Microsoft.
- La ventana principal hace lo mismo con los errores de MSAL (`subError`, `errorMessage`): `server_error`, `access_denied`, `consent_required`, `interaction_required` y el código AADSTS.

| Código | Causa probable | Qué hacer |
|---|---|---|
| `AADSTS50105` | El usuario no está asignado a la aplicación (asignación requerida) | TI asigna al usuario o quita «asignación requerida» |
| `AADSTS65001` | Falta el consentimiento de la aplicación | TI concede el consentimiento del administrador (`User.Read`) |
| `AADSTS50011` | El URI de retorno no coincide con el registrado | TI registra `<sitio>/auth/redirect` en Entra (fase «entra») |
| `AADSTS700016` | Microsoft no encuentra el `clientId` en el directorio | Revisar `MSAL_CLIENT_ID` y la app registrada |
| `AADSTS9002326` | El URI está registrado como «Web» y no como «Aplicación de una sola página» | TI lo pasa a la plataforma SPA |
| `access_denied` | La persona canceló o se negó el acceso | Volver a intentar y aceptar los permisos |
