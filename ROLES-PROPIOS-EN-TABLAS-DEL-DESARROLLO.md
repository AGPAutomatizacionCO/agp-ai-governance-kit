# Roles propios en tablas del desarrollo

Norma de IT, 2026-11-18. Cómo se crean y se declaran las tablas de roles de **todo desarrollo nuevo**. Complementa [Configuración local de roles y secretos](CONFIGURACION-LOCAL-ROLES-Y-SECRETOS.md) (cómo se autoriza y se configura) con lo que esa guía no dice: **qué crea el worker, con qué permisos, con qué patrón y con qué nombres**. La referencia verificada es **AGPTS** (repositorio `AGP_CO_PEOPLE_AGPTS`, esquema `app_people_agpts`).

> Verificado contra la Mesa (`backend/src/helpers/datos_ddl.py` y `roles_esquema.py`) y contra AGPTS (`ai/outputs/data-access-manifest.json`, `backend/alembic/versions/0021_roles_propios.py`, `backend/app/core/roles_propios.py` y `ROLES.md`). Si la Mesa y este documento difieren, manda la Mesa y se corrige el documento.

## 1. Qué hace el worker y qué no

- **Crea** cada tabla declarada `propia_del_desarrollo` con `crear_en_despliegue: true` con `IF OBJECT_ID(N'<esquema>.<tabla>', N'U') IS NULL BEGIN CREATE TABLE … END`. Si la tabla ya existe **no la toca**: nunca hace `ALTER` ni `DROP` sobre una tabla existente.
- **Un cambio de columnas es una migración propia del desarrollo** (en AGPTS, Alembic: la `0021` crea las dos tablas para las bases de desarrollo y prueba; en producción las crea el worker con el plan que genera la Mesa). Cambiar el manifiesto de una tabla que ya existe no cambia la tabla.
- **Concede** al rol de la app **solo** las operaciones DML que declaras por tabla en `operaciones_permitidas` (`SELECT`, `INSERT`, `UPDATE`, `DELETE`). La app **jamás** recibe `CREATE`, `DROP` ni `ALTER`.
- **Las claves primarias enteras llevan `autoincremental: true`.** Sin eso la tabla se crea sin `IDENTITY` y el primer `INSERT` falla.

## 2. El patrón: dos tablas propias

Se declaran las dos como `origen: propia_del_desarrollo` y `crear_en_despliegue: true`, en el esquema `app_<área>_<desarrollo>` y con el nombre `App_<Área>_<Desarrollo>_<tabla>` (NOMENCLATURA-DATOS.md):

| Tabla (sufijo) | Operaciones | Para qué |
|---|---|---|
| `…_sistema_roles_personas` | `SELECT`, `INSERT`, `UPDATE`, `DELETE` | Un perfil por persona (`correo` único): `id`, `correo`, `perfil`, `asignado_por`, `created_at`, `updated_at`. Quitar el acceso borra la fila. |
| `…_sistema_roles_auditoria` | `SELECT`, `INSERT` | Append-only: `id`, `fecha`, `actor`, `accion`, `correo`, `perfil_anterior`, `perfil_nuevo`, `motivo`, `resultado`. **Sin `UPDATE` ni `DELETE`**: la auditoría no se edita ni se borra. |

Reglas: sin vigencia ni fecha de vencimiento (los roles son de gestión continua); la asignación y su línea de auditoría se escriben en **una sola transacción**; el actor sale del token validado, nunca del cuerpo de la petición.

**Ejemplo para copiar y adaptar:** [`examples/data-access-manifest.roles-propios.valid.json`](examples/data-access-manifest.roles-propios.valid.json) (valida contra `schemas/data-access-manifest.schema.json` y pasa `agpctl datos check`). Incluye además la vista `corporacion.vw_UsuariosCorporacion` de IT como `preexistente` solo `SELECT`, para buscar personas al asignar un perfil. Cambia el esquema, el desarrollo y los nombres por los de tu desarrollo; no copies `app_ejemplo_demo`.

Código listo: `templates/auth-estandar/backend/src/helpers/roles_propios.py` (repositorio, `resolver`, `asignar`) y `backend/src/flask_config/bp_configuracion.py` (API de la pantalla), con la pantalla `ConfiguracionDesarrollo.jsx`. Ver el README de la plantilla.

## 3. Qué NO usar

- **No uses `plantilla: roles` del túnel.** Esa plantilla es heredada: deja las tablas en solo lectura (el worker revoca `INSERT`, `UPDATE` y `DELETE`) porque la escritura era de la Mesa, que ya no gestiona roles. Con ella la app no podría asignar a nadie.
- **No uses los nombres reservados del túnel:** `App_<Área>_<Desarrollo>_Roles`, `…_RolesDatos` y `…_RolesPersonas`. Cuando el plan agrega la plantilla heredada, la Mesa rechaza un manifiesto que declare uno de esos nombres (comparación exacta, sin distinguir mayúsculas). El patrón usa `…_sistema_roles_personas` y `…_sistema_roles_auditoria`, que **no chocan** con ellos (AGPTS lo demuestra). Si un desarrollo ya creó tablas con un nombre reservado, las renombra con una migración propia; no se crean tablas nuevas con esos nombres.
- No uses las tablas centrales `RegistroDesarrollos_Roles*` de la Mesa ni llames a `/api/roles-app` (retirado el 2026-11-11).
- No declares otras tablas de roles "por si acaso": solo estas dos.

## 4. Desarrollos de RRHH y People

Si el esquema es `app_rrhh_*` o `app_people_*` (por ejemplo `app_people_agpts`), las tablas propias se crean en la base **AGP_RRHH**, no en la base general, y el plan de despliegue lo **anuncia** («Desarrollo de RRHH/People identificado: validar el plan contra las tablas propias en su base») para que IT lo valide. El manifiesto no cambia: el destino lo decide la Mesa por el área del esquema. IT debe tener creada la cuenta de plataforma del worker en esa base antes del primer despliegue.

## 5. Pasos para quien arranca un desarrollo

1. **Elige el esquema y los nombres** según NOMENCLATURA-DATOS.md y declara las dos tablas (y la vista de usuarios de IT) en `ai/outputs/data-access-manifest.json`, partiendo del ejemplo. Comprueba con `python -m agpctl datos check --repo .`.
2. **Declara en `.agp/runtime.yaml`** las variables `ROLES_PROPIOS_ESQUEMA`, `ROLES_PROPIOS_TABLA_PERSONAS`, `ROLES_PROPIOS_TABLA_AUDITORIA`, `CONFIG_ADMINISTRADORES_INICIALES`, `CONFIG_SECRETOS_PERMITIDOS` y `CONFIG_KEY_VAULT_URL` (no son secretos) y los secretos de conexión por nombre, nunca el valor.
3. **Copia la plantilla** (`roles_propios.py`, `bp_configuracion.py`, `configuracionLocal.js`, `ConfiguracionDesarrollo.jsx`), edita `PERFILES` con la matriz real de vistas y acciones y registra el blueprint.
4. **Para bases de desarrollo y prueba** crea las dos tablas con una migración propia (AGPTS: `backend/alembic/versions/0021_roles_propios.py`): solo añade tablas vacías, no inserta datos y su `downgrade` aborta si hay filas. En producción las crea el worker.
5. **Primer administrador.** Entra por `CONFIG_ADMINISTRADORES_INICIALES` (correos de los administradores ya aprobados, cargados por configuración confiable): esa persona asigna a las demás desde «Configuración». No se siembra una fila inventada ni se ejecuta SQL con datos de ejemplo; si el desarrollo necesita cargar asignaciones existentes, usa el procedimiento de migración que apruebe IT con las personas reales y conserva su auditoría. En AGPTS los administradores salen de `ROLES_ADMINS` (`backend/app/core/roles_propios.py`).
6. **Pruebas mínimas** (con dobles de SQL, sin conexiones reales): sesión válida con perfil permitido; 401 sin sesión; 403 sin capacidad; administrador revocado sin acceso en la siguiente llamada; perfil desconocido rechazado; rollback si falla la auditoría; nadie cambia su propio perfil; el actor no se puede falsificar; ninguna respuesta ni log con valores de secretos. Modelo: `tests/test_configuracion_local_plantilla.py` del kit y `backend/tests/test_roles_propios.py` de AGPTS.
7. **Qué verifica el preflight:** que el manifiesto cumpla el esquema y la norma de nombres, que las tablas propias traigan tipos válidos (`agpctl datos check` lo repite en local), que `.agp/runtime.yaml` declare los secretos de conexión del esquema y, en RRHH/People, el destino en AGP_RRHH. Los nombres reservados del túnel los rechaza la Mesa solo cuando el plan agrega la plantilla heredada. IT aprueba el plan completo (esquema, tablas, permisos por tabla y hash del script) antes de que el worker lo ejecute.

## 6. Referencias en AGPTS

| Archivo | Qué muestra |
|---|---|
| `ai/outputs/data-access-manifest.json` | Las dos tablas `App_People_AGPTS_sistema_roles_personas` (SELECT, INSERT, UPDATE, DELETE) y `…_sistema_roles_auditoria` (SELECT, INSERT), `autoincremental` en sus claves. |
| `backend/alembic/versions/0021_roles_propios.py` | Migración que solo añade las dos tablas vacías; `downgrade` aborta si hay filas. |
| `backend/app/core/roles_propios.py` | Lectura del perfil por correo, caché corta, falla cerrada, administradores de `ROLES_ADMINS`. |
| `ROLES.md` | Perfiles y permisos reales (módulos y funciones). |
