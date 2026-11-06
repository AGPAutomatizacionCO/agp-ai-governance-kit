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
| `src/screens/LoginScreen.jsx` | `src/screens/LoginScreen.jsx` | La pantalla de login aprobada, con el nombre del desarrollo. Su raíz lleva `data-agp-login="estandar"`. Se copia sin cambios. |
| `src/styles/login-estandar.css` | `src/styles/login-estandar.css` | Los estilos que la pantalla toma del CSS global de la Mesa (color de marca, fuente, reinicio de márgenes). Va acotado a `#login-screen` y hace que la pantalla se vea **igual** en cualquier desarrollo. |
| `src/screens/SinAcceso.jsx` | `src/screens/SinAcceso.jsx` | **Pantalla estándar sin acceso**: la ve quien inicia sesión pero no tiene acceso. Sin texto libre: nombre de la app, contacto (desarrollador funcional, `administradores[0]` de `.agp/entra.yaml`) y persona con sesión; ES / PT; botones Copiar correo, Reintentar y Cerrar sesión. Su raíz lleva `data-agp-sin-acceso="estandar"`. Se copia sin cambios. |
| `src/styles/sin-acceso-estandar.css` | `src/styles/sin-acceso-estandar.css` | Sus estilos, acotados a `.agp-sin-acceso`, con los tokens de `agp-tema.css`. |
| `src/screens/SinAcceso.test.jsx` | `src/screens/SinAcceso.test.jsx` | La prueba del contrato (vitest): marca, contacto, botones y que no inventa un contacto. |
| `src/components/UserMenu.jsx` | `src/components/UserMenu.jsx` | **Menú de usuario estándar**: nombre y rol de quien entró; al hacer clic, «Configuración» (directo a `/configuracion`) y «Cerrar sesión». Probado en producción con RPC. Ver abajo. |
| `src/styles/menu-usuario-estandar.css` | `src/styles/menu-usuario-estandar.css` | Sus estilos, acotados a `.agp-menu-usuario`. |
| `src/screens/ConfiguracionDesarrollo.jsx` | `src/screens/ConfiguracionDesarrollo.jsx` | **Pantalla estándar «Configuración de roles y secretos»** (`/configuracion`): pestañas Roles, Usuarios, Secretos y Actividad contra el túnel de la Mesa. Ver «La pantalla de configuración». |
| `src/styles/configuracion-estandar.css` | `src/styles/configuracion-estandar.css` | Sus estilos, acotados a `.agp-config` (usan las variables de `agp-tema.css`). |
| `src/services/rolesMesa.js` | `src/services/rolesMesa.js` | Cliente del túnel de roles y secretos de la Mesa (usa el `id_token` de `AuthContext`). Rutas, cuerpos y errores: `CONTRATO-TUNEL-ROLES.md`. |
| `src/screens/ConfiguracionDesarrollo.test.jsx`, `src/services/rolesMesa.test.js` | ídem | Las pruebas (vitest) de la pantalla y del cliente. Corren en el CI del desarrollo. |
| `src/components/UserMenu.test.jsx` | `src/components/UserMenu.test.jsx` | La prueba del contrato (vitest): nombre, rol, «Configuración» solo con permiso y «Cerrar sesión». Corre en el CI del desarrollo. |
| `src/styles/agp-tema.css` | `src/styles/agp-tema.css` | **Colores y fuente de la Mesa**: las variables (`--bg`, `--surface`, `--border`, `--text`, `--brand`, `--c-*`, `--sem-*`…) en oscuro y en claro (`body.theme-light`) y la base de `html, body`. Se importa una vez en `src/main.jsx`. Ver abajo. |
| `src/components/EncabezadoAgp.jsx` | `src/components/EncabezadoAgp.jsx` | **Encabezado estándar**: nombre del desarrollo, ES / PT, modo claro / oscuro y el menú de usuario. Ver abajo. |
| `src/styles/encabezado-estandar.css` | `src/styles/encabezado-estandar.css` | Sus estilos, acotados a `.agp-encabezado`. |
| `src/hooks/useTemaAgp.js`, `useIdiomaAgp.js` | `src/hooks/` | El modo claro / oscuro y el idioma ES / PT que usa el encabezado; quedan guardados en el navegador. |
| `src/components/EncabezadoAgp.test.jsx` | `src/components/EncabezadoAgp.test.jsx` | La prueba del contrato del encabezado (vitest): marcas, nombre y menú de usuario. Corre en el CI del desarrollo. |
| `src/components/AgpLogo.jsx`, `Icon.jsx` | `src/components/` | Piezas que usan la pantalla y el encabezado (si el desarrollo ya las tiene, no se pisan; el encabezado necesita los iconos `sun` y `moon`). |
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
   @agpglass.com, y **cómo se controla el acceso**: `acceso: organizacion` (norma: toda cuenta de AGP entra con la vista general) o, como
   excepción, `acceso: asignado` (solo personas asignadas; con `justificacion` y `publico`). Ver `ACCESO-Y-ROLES-DEL-DESARROLLO.md`. **No hay secreto de cliente** (`secrets: []`).

## El menú de usuario estándar

El elemento que muestra el **nombre y el rol** de quien entró y, al hacer clic, despliega **«Configuración»** (directo a `/configuracion`) y **«Cerrar sesión»** es el mismo en todo desarrollo. Se llama **`UserMenu`** («Menú de usuario»); RPC lo resolvió primero y es la referencia. Se monta una vez en el encabezado de la aplicación: `<UserMenu />` (con react-router, `<UserMenu onNavegar={navigate} />`).

Lo que se exige es el **contrato**, no el archivo: un desarrollo con otro framework de UI (por ejemplo RPC en TypeScript con Tailwind, o SAC con MUI) lo cumple igual si respeta:

| Marca | Qué es |
|---|---|
| `data-agp-menu="usuario"` + `aria-label="Menú de usuario"` | El botón con el nombre y el rol visibles. |
| `data-agp-menu="configuracion"` | La entrada «Configuración»: un enlace directo a `/configuracion` (la pantalla estándar). Solo aparece para quien administra. Con más de un enlace administrativo propio despliega «Administración». |
| `data-agp-menu="cerrar-sesion"` | «Cerrar sesión». |

El rol sale del token (`Admin` → «Administrador», si no «Usuario»); un desarrollo con perfiles propios pasa `rolEtiqueta`. Los enlaces administrativos propios, además de «Configuración», se pasan en `enlaces`. La Mesa **bloquea** el despliegue si falta (pieza «menú de usuario» de `auth_estandar`).

## La pantalla de configuración

`ConfiguracionDesarrollo` es la pantalla estándar de roles y secretos (norma `ACCESO-Y-ROLES-DEL-DESARROLLO.md` §6). Se monta en la ruta `/configuracion`, dentro de la sesión (con react-router: `<Route path="/configuracion" element={<ConfiguracionDesarrollo onVolver={() => navigate("/")} />} />`).

1. **Backend:** `GET /api/config` entrega `roles: { mesaUrl, idProyecto }` cuando están `ROLES_DESDE_MESA=true`, `MESA_API_URL` (https) y `MESA_ID_PROYECTO` (`bp_base.py` del paquete; el frontend lo guarda en `appInfo.roles`). Sin eso la pantalla dice que la conexión con la Mesa no está activa.
2. **Autorización:** con `ROLES_DESDE_MESA=true` el backend le pregunta a la Mesa por la persona (`GET /api/roles-app/<id>/mios` con el mismo `id_token`) y autoriza con lo que responde. `ROLES.md` v2 declara los permisos y los perfiles iniciales.
3. **Quién puede qué** lo decide la Mesa por persona (`estado.yo`): el principal asigna y carga secretos; el secundario solo ve y edita la definición de los roles.
4. **Marcas que verifican la Mesa y los agentes:** `data-agp-configuracion="estandar"` (raíz), `data-agp-pestana="roles|usuarios|secretos|actividad"` (pestañas) y `role="dialog"` con `aria-modal="true"` (modal de asignar).

## Encabezado y colores estándar

Todo desarrollo se ve como la Mesa de Ayuda: la misma barra superior y los mismos colores, fuente y modos claro / oscuro.

1. Copiar **sin cambios** `src/styles/agp-tema.css`, `src/styles/encabezado-estandar.css`, `src/components/EncabezadoAgp.jsx` y los dos
   archivos de `src/hooks/`.
2. En `src/main.jsx`, una sola vez: `import "./styles/agp-tema.css";` (ver `main.jsx.example`). Los estilos propios del desarrollo usan esas
   variables (`var(--surface)`, `var(--text)`, `var(--border)`, `var(--brand)`…) en vez de colores fijos; así cambian solos con el modo claro.
3. Arriba de la aplicación: `<EncabezadoAgp nombre="Mi desarrollo" />`. Sin `nombre` usa el que entrega la API (`appInfo`, el mismo de la
   pantalla de login). Ya trae el `UserMenu`: no se monta otro. Lo que necesita el menú va en `menuProps`
   (`<EncabezadoAgp menuProps={{ onNavegar: navigate }} />`) y las acciones propias del desarrollo van dentro, junto al nombre
   (`<EncabezadoAgp><button>Exportar</button></EncabezadoAgp>`).
4. Idioma: el encabezado solo guarda la elección ES / PT; cada desarrollo traduce **sus** textos leyendo `const { idioma } = useIdiomaAgp()`.
   El modo activo se lee con `useTemaAgp()`.

| Marca | Qué es |
|---|---|
| `data-agp-login="estandar"` | La raíz de la pantalla de login (`LoginScreen.jsx`). |
| `data-agp-sin-acceso="estandar"` | La raíz de la pantalla sin acceso (`SinAcceso.jsx`). |
| `data-agp-encabezado="estandar"` | La raíz del encabezado. |
| `data-agp-idioma` | El grupo ES / PT; cada botón con `aria-pressed`. |
| `data-agp-tema` + aria-label «Modo claro» / «Modo oscuro» | El botón de modo; dice a qué modo cambia. |

Al desplegar, la Mesa compara `src/styles/agp-tema.css`, `src/styles/encabezado-estandar.css`, `src/styles/login-estandar.css`,
`src/styles/menu-usuario-estandar.css`, `src/styles/sin-acceso-estandar.css` y `src/screens/LoginScreen.jsx` **byte a
byte** (sin contar los finales de línea) con los del kit en la versión fijada en `.agp/governance.yaml`, y revisa que estén las marcas. Si
hay que cambiar el diseño, se cambia aquí, en el kit. El contenido de cada pantalla, debajo del encabezado, es libre.

## Qué hace la Mesa al desplegar (el desarrollo no necesita acceso a Azure)

Registra la aplicación en Entra ID como **Single-page application**, aprueba `User.Read` y `offline_access`, asigna a los administradores
del manifiesto al rol Admin, entrega `MSAL_CLIENT_ID`/`MSAL_TENANT_ID` y el nombre (`APP_NAME`) como configuración de la Web App. Con `acceso: organizacion` (la norma) la app no exige asignación y los roles los da el administrador en el panel «Configuración» de la app;
con `asignado`, IT y el Responsable asignan además a quién puede entrar.

## Nombre propio y local

- En Azure el nombre lo fija la Mesa (`APP_NAME` → `/api/config` → `appName`). En local, defínelo con `APP_NAME=Mi desarrollo` al arrancar la API.
- `DISABLE_AUTH=true` y `DEV_USER_EMAIL` permiten correr la API sin login **solo en tu equipo**; dentro de Azure se ignoran.
- Si cambias el diseño de la pantalla, no es el login estándar: pide a IT una excepción por escrito.

## Pantalla sin acceso: cómo se conecta

1. `GET /api/config` entrega, además de `appName`, `contactoNombre` y `contactoCorreo`: salen de `administradores[0]` de `.agp/entra.yaml` (o de `CONTACTO_NOMBRE` / `CONTACTO_CORREO` si el archivo no está en la imagen). Solo se acepta un correo `@agpglass.com`. `cargarConfigMsal` los guarda en `appInfo`.
2. En la app: con sesión iniciada y **sin rol ni vista general** (la API de roles responde sin acceso), se monta `<SinAcceso />` en lugar de la aplicación.
3. No hay texto libre: el antiguo `sinAcceso.mensaje` de `ROLES.md` queda **obsoleto** y la Mesa ya no lo muestra.
