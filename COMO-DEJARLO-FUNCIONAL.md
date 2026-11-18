# Cómo dejarlo funcional: acceso, roles y secretos en pasos cortos

Guía para la persona o el agente que acaba de copiar el paquete `templates/auth-estandar/` y quiere que el desarrollo **funcione de punta a punta** (login, menú, «Configuración de roles y secretos», secretos) y llegue a IT sin preguntas.
Cada paso dice qué hacer y dónde está la regla completa. La lista para comprobar que todo quedó en el repositorio está al final (y en `OBLIGATORIOS-DEL-DESARROLLO.md`).

## Pasos

### 1. Identidad: `.agp/entra.yaml`

Copia `templates/auth-estandar/.agp/entra.yaml` y completa `administradores` (al menos el desarrollador funcional, con su correo @agpglass.com). Deja `acceso: organizacion` (la norma) salvo que IT apruebe `asignado` con `justificacion` y `publico`.
No hay secreto de cliente (`secrets: []`). Regla: `ACCESO-Y-ROLES-DEL-DESARROLLO.md` §1.
**El retorno del login (MSAL 5):** `redirectUriPath` queda en `/auth/redirect`, y el código y el servidor deben usar esa misma ruta: copia también `auth/redirect.html`, `src/auth/redirect.js`, la configuración de Vite de `vite.config.example.js` y `backend/src/flask_config/bp_retorno_msal.py` (regístralo antes del fallback de la SPA). Sin la página puente, el login muestra «Error al iniciar sesión. Intenta de nuevo.»: guía paso a paso en `INTEGRAR-MSAL.md` y comprobación con `python -m agpctl login check --repo .`.

### 2. Roles: `ROLES.md` v2

Declara en `ROLES.md` (`apiVersion: roles.agp/v2`) los `permisos` (módulos = las vistas de la app, funciones = sus acciones) y los `perfilesIniciales` (los roles con los que arranca; el administrador crea y edita más desde la pantalla). Ejemplo: `OBLIGATORIOS-DEL-DESARROLLO.md` §8.
El código de la app oculta y bloquea según esos ids de permiso.

### 3. Conexión con la Mesa: tres variables en `.agp/runtime.yaml`

En `env` (no son secretos):

```yaml
env:
  - { name: ROLES_DESDE_MESA, value: "true" }
  - { name: MESA_API_URL, value: "https://agp-co-registro-desarrollos.azurewebsites.net" }
  - { name: MESA_ID_PROYECTO, value: "<el id del desarrollo en la Mesa>" }   # EJEMPLO: el valor real lo ves en la página del desarrollo en la Mesa
```

`GET /api/config` (`bp_base.py` del paquete) se las entrega a la pantalla. La URL debe ser `https`.

### 4. Secretos: por nombre, `<desarrollo>-<dato>`

En el mismo `runtime.yaml` declara `desarrollo: <nombre>` y cada secreto como `<desarrollo>-<dato>`; nunca el valor.
El valor lo carga el administrador principal desde la pestaña **Secretos** de «Configuración» (o el responsable, antes del primer despliegue, en la ruta «Prepara tu solicitud a IT»). Regla y ejemplos: `ACCESO-Y-ROLES-DEL-DESARROLLO.md` §6.
Comprueba con `python -m agpctl runtime check --repo .`.

### 5. El backend autoriza con las tablas del desarrollo

Copia `templates/auth-estandar/backend/src/helpers/roles_propios.py` y `backend/src/flask_config/bp_configuracion.py` (junto a `auth.py`), edita `PERFILES` con la matriz real, registra el blueprint y úsalo después de validar el token:

```python
from src.helpers import roles_propios

alcance = roles_propios.resolver(g.user_email)   # el correo sale del token validado por require_auth
if not alcance.administra:   # nivel global o admin
    return jsonify({"message": "Solo administradores"}), 403
```

Lee la tabla de personas del esquema del desarrollo (caché de 30 s), **falla cerrada** (vista general) si la base no responde y nunca llama a la Mesa. Los endpoints administrativos releen el permiso en cada llamada. Guía: `CONFIGURACION-LOCAL-ROLES-Y-SECRETOS.md`. El frontend usa `src/services/configuracionLocal.js`, el menú `UserMenu` (con «Configuración» directo a `/configuracion`) y la pantalla `ConfiguracionDesarrollo`, todos del paquete.

### 6. Las dos tablas de acceso son del desarrollo y se declaran

- Declara en `ai/outputs/data-access-manifest.json` la tabla de personas (`SELECT`/`INSERT`/`UPDATE`/`DELETE`) y la de auditoría (`SELECT`/`INSERT`), propias del desarrollo (`crear_en_despliegue`, PK entera con `autoincremental: true`), y la vista `corporacion.vw_UsuariosCorporacion` como `preexistente` solo `SELECT`. Ejemplo: `examples/data-access-manifest.roles-propios.valid.json`.
- Los nombres `_Roles`, `_RolesDatos` y `_RolesPersonas` están reservados para el modo heredado: no los uses. Los roles son de gestión continua: **sin vigencia** ni fecha de vencimiento.
- El túnel `/api/roles-app` está retirado: `templates/auth-estandar-tunel-heredado/` es solo referencia para migrar.

### 7. En local (sin la Mesa)

- `DISABLE_AUTH=true` y `DEV_USER_EMAIL=tu.correo@agpglass.com` saltan el login **solo en tu equipo** (dentro de Azure se ignoran).
- Con `ROLES_DESDE_MESA` apagado (lo normal en local, porque la plantilla exige una Mesa `https`), el helper no llama a nada: usa `ROLES_LOCAL_NIVEL=admin|usuario|general` (por defecto `general`, solo lectura). La pantalla de «Configuración» dirá que la conexión con la Mesa no está activa: es lo esperado.
- Para ver la pantalla con datos reales, ábrela en un desarrollo ya registrado en la Mesa (con tu sesión de Microsoft), no desde tu equipo.
- Los datos en SQLite (si los usas en local) se declaran como **tabla propia nueva** para el despliegue (`NOMENCLATURA-DATOS.md`); nace vacía.

### 8. Comprueba y pide el despliegue

Recorre la lista de comprobación de abajo y pídele al Agente de Despliegue su informe.

## Lista de comprobación previa a pedir el despliegue

Cada punto es verificable en el repositorio (el Agente de Despliegue lo reporta dentro de `entra`, `roles`, `acceso_usuarios`, `configuracion_roles`, `menu_usuario`, `runtime`, `secretos_norma` y `mecanismo_propio_acceso`).

- [ ] `.agp/entra.yaml`: `acceso`, `administradores[0]` con correo @agpglass.com, `secrets: []`, `redirectUriPath: /auth/redirect`.
- [ ] Login con MSAL 5: `redirectUri` y `postLogoutRedirectUri` de `src/config/msal.js` = `${origin}/auth/redirect`; existen `auth/redirect.html` y `src/auth/redirect.js`; la compilación genera `dist/auth/redirect.html` y el servidor lo sirve en `GET /auth/redirect` (nunca `index.html`).
- [ ] `ROLES.md` v2 con `permisos` y `perfilesIniciales`, sin `sinAcceso.mensaje`.
- [ ] `.agp/runtime.yaml`: `ROLES_DESDE_MESA`, `MESA_API_URL` (https) y `MESA_ID_PROYECTO` en `env`; `desarrollo:` y todo secreto como `<desarrollo>-<dato>`; sin valores secretos; `python -m agpctl runtime check` sin `issues` ni `avisos`.
- [ ] Backend: autoriza con `roles_propios.resolver(g.user_email)` (tablas propias declaradas en el manifiesto), falla cerrada y relee el permiso en cada endpoint administrativo.
- [ ] Frontend: `UserMenu` con las marcas `data-agp-menu` y «Configuración» directo a `/configuracion`; `ConfiguracionDesarrollo` montada (`data-agp-configuracion="estandar"`); cliente `configuracionLocal.js`.
- [ ] Pantalla `SinAcceso` estándar (sin texto libre) y `GET /api/config` con `contactoNombre` y `contactoCorreo`.
- [ ] Ninguna tabla de usuarios o de roles propia, ningún `CREATE TABLE`/`INSERT`/`UPDATE` sobre tablas de roles, ninguna ruta propia de administración de usuarios o roles; el manifiesto de datos no declara las tres tablas de roles.
- [ ] Sin `.env` real en el repositorio; `DISABLE_AUTH` solo en local.
