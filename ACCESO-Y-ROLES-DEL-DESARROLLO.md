# Acceso y roles de un desarrollo: quién entra, con qué rol y cómo se declara

Norma para todo desarrollo con login de Microsoft Entra ID (todos los que se despliegan con la Mesa de Requerimientos). **Norma de IT del 2026-11-04: todo desarrollo funciona como la Mesa de Ayuda.**
Cualquier persona de AGP entra y ve la vista general; los roles específicos los da el administrador **dentro** de la app, desde su panel «Configuración» (como RPC), por persona o a todo un departamento de Microsoft. La Mesa los guarda y valida por detrás (túnel de roles). Restringir el
ingreso a personas asignadas es la excepción y se justifica. La Mesa lo muestra en el plan que aprueba IT, y los agentes lo documentan y lo verifican. Complementa `templates/auth-estandar/README.md` (el login) y
`PERMISOS-Y-SECRETOS-DEL-WORKER.md` (los datos). El contrato técnico de la API con la que habla la pantalla de configuración (rutas, cuerpos, autenticación y errores) está en `CONTRATO-TUNEL-ROLES.md`; la lista de todo lo obligatorio, con ejemplos, en `OBLIGATORIOS-DEL-DESARROLLO.md`.

## 1. La pregunta que todo desarrollo responde

> **¿Quién es el público del desarrollo?** Toda la organización, un departamento, varios departamentos, o personas concretas.

La respuesta decide `acceso` en `.agp/entra.yaml`:

| `acceso` | Público | Qué pasa en Entra ID | Cómo se dan los roles |
|---|---|---|---|
| `organizacion` (**valor por defecto**) | Toda la organización AGP | La app **no exige asignación**: cualquier cuenta de AGP (un solo tenant) inicia sesión y ve la **vista general** | El administrador asigna los roles dentro de la app, en su panel «Configuración» (por persona o a todo un departamento de Microsoft). Quien no tiene rol ve la vista general (el perfil marcado como vista general) |
| `asignado` (excepción, con `justificacion`) | Un departamento, varios departamentos o personas concretas, cuando la información no puede verla nadie más | La app **exige asignación**: solo entran las personas asignadas | Gestor de roles: el Responsable asigna a personas **del departamento del desarrollo** (motivo de la lista) y a personas **de otro departamento** (justificación propia de al menos 30 letras) |

Reglas:

- **Sin `acceso`, la app queda abierta a toda la organización.** `assignmentRequired: true` a secas ya no la cierra (era el valor de la plantilla, no una decisión): la Mesa lo avisa y la abre. Quita `assignmentRequired`.
- `acceso: organizacion` exige un solo tenant (`signInAudience: AzureADMyOrg`) y no se combina con `assignmentRequired: true`. La `justificacion` es opcional.
- `acceso: asignado` es la excepción: lleva `justificacion` (al menos 40 caracteres: por qué nadie más puede entrar) y describe el público en `publico` (hasta 300 caracteres). La Mesa avisa si faltan.
- **Vista general:** lo que ve quien no tiene rol. Con `ROLES.md` v2 es el perfil que el administrador marca como «vista general» en el panel «Configuración» de la app; nunca incluye funciones administrativas ni datos sensibles.
- **La autenticación corporativa no sustituye a la autorización.** Que cualquiera de AGP entre no abre lo administrativo: el módulo Administrador y toda función sensible siguen condicionados al rol (`Admin`) que valida
  la API con el token, y los permisos sobre datos siguen siendo los aprobados (ver `PERMISOS-Y-SECRETOS-DEL-WORKER.md`).

```yaml
# .agp/entra.yaml (norma: abierto a toda la organización)
acceso: organizacion
administradores:
  - correo: responsable@agpglass.com
```

```yaml
# .agp/entra.yaml (excepción: solo personas asignadas)
acceso: asignado
justificacion: "Nómina individual: solo Compensaciones puede ver los salarios; ni la vista general puede mostrarse a otros departamentos."
publico: "Personal de Compensaciones"
administradores:
  - correo: responsable@agpglass.com
```

## 2. Dónde se documenta (el `ROLES.md` del desarrollo)

El archivo `ROLES.md` (contrato `roles.agp/v1` o `v2`, lo valida la Mesa) es la vista **para personas** de los roles y las áreas. El desarrollo documenta ahí:

- **Roles:** `Admin` y `Usuario` (básicos) y los personalizados, con qué puede hacer cada uno.
- **Dominios y áreas de `ROLES.md`** (`dominios` → `areas`): qué datos distingue la app y quién pertenece a cada uno. **No son los departamentos de Microsoft**: el departamento es el `department` de Entra ID (lo que muestra Teams) y es lo que permite distinguir «del departamento del desarrollo» de «de otro departamento» al asignar. Las dos cosas llamadas «área» están explicadas en `CONTRATO-TUNEL-ROLES.md` §3.1.
- **Vista general:** qué ve quien entra sin rol (con `acceso: organizacion`, toda persona de AGP).
- **`sinAcceso.mensaje` (obsoleto):** ya no se escribe un mensaje propio. Quien entra sin acceso ve la **pantalla estándar de AGP** (`SinAcceso`, paquete `templates/auth-estandar/`), que le dice que se comunique con el desarrollador funcional (`administradores[0]` de `.agp/entra.yaml`, con su correo @agpglass.com). Un `sinAcceso.mensaje` existente se ignora.
- **Coherencia con el manifiesto:** si `acceso: organizacion`, el texto dice que cualquier cuenta de AGP entra con la vista general; si `asignado`, dice quién puede pedir acceso y a quién.

## 3. Qué hace cada agente

**Agente documental.** Documenta la sección **«Acceso y roles»** del desarrollo (en la documentación funcional y de despliegue del expediente): público, `acceso` elegido y por qué, roles y dominios/áreas de `ROLES.md`, qué es
administrativo y cómo se valida en la API. Si el expediente dice una cosa y `.agp/entra.yaml` otra (por ejemplo, «lo usa toda la organización» y `acceso: asignado`), lo registra como contradicción y no elige por su cuenta.

**Agente de despliegue.** Lee `.agp/entra.yaml` y `ROLES.md` y reporta, en `PreparacionDespliegue`, el requisito «acceso de usuarios»: el valor de `acceso`, si hay `justificacion` o `publico`, y si coinciden con
`ROLES.md` y con el código (`require_auth` para usuarios, `require_admin` o equivalente para lo administrativo). Reporta como hallazgo: `assignmentRequired: true` sin `acceso` (ya no cierra la app);
`organizacion` junto a `assignmentRequired: true`; `asignado` sin `justificacion` o sin `publico`; una vista general que muestra funciones administrativas; y un módulo administrativo que no exige rol.

**La Mesa.** Valida la forma, abre a la organización todo desarrollo que no declare `acceso: asignado`, muestra **«Acceso de usuarios»** en la página del plan y en el popup que IT aprueba (con o sin permisos de datos), y en el modo abierto
lo ata a la aprobación (entra al hash del plan). Un cambio de `acceso` toca `.agp/entra.yaml`, un archivo de contrato: exige la aprobación completa, no el redespliegue rápido.

## 4. El menú de usuario estándar: dónde se configura el acceso

Todo desarrollo trae el **mismo menú de usuario** (`UserMenu`, paquete `templates/auth-estandar/`): el botón con el nombre y el rol de quien entró y, al hacer clic, **«Configuración»** (va **directo** a la pantalla estándar `/configuracion`, §6) y **«Cerrar sesión»**. Es el que RPC ya usa en producción y es **obligatorio**: ahí se llega a la gestión de quién entra y con qué rol, y es lo que el Agente de Despliegue y la Mesa verifican. El contrato (marcas `data-agp-menu`, «Menú de usuario», «Configuración», «Cerrar sesión») está en el README del paquete; un desarrollo con su propio componente lo cumple igual si lo respeta. «Configuración» solo se muestra a quien administra: el rol `Admin` o quien tenga enlaces administrativos propios. Solo si el desarrollo declara **más de un** enlace administrativo propio, «Configuración» despliega la lista «Administración»; con uno solo (la norma) no hay submenú.

## 5. Lista de verificación

1. `.agp/entra.yaml` declara `acceso` (`organizacion` o `asignado`) y su `justificacion` o `publico`.
2. `ROLES.md` describe roles y dominios/áreas, coherentes con `acceso` (sin `sinAcceso.mensaje`: lo reemplaza la pantalla estándar).
3. La API exige el rol `Admin` en todo lo administrativo; lo demás solo exige un token válido del tenant.
4. El expediente tiene la sección «Acceso y roles» y no contradice al manifiesto.
5. El encabezado monta el menú de usuario estándar (§4) y su «Configuración» va directo a la pantalla estándar y solo la ve quien administra.
6. `/configuracion` monta la pantalla estándar (§6) conectada a la Mesa (`ROLES_DESDE_MESA`), y `ROLES.md` es v2.
7. No queda un login ni un gestor de usuarios y roles propios (§7): la fuente de verdad de los roles es la Mesa.
8. Monta la pantalla estándar `SinAcceso` (§2, marca `data-agp-sin-acceso="estandar"`) para quien inicia sesión sin acceso; el contacto es el primer administrador de `.agp/entra.yaml` con correo @agpglass.com. El agente de despliegue lo reporta como hallazgo si falta (aviso, igual que el visual estándar).

## 6. La pantalla estándar «Configuración de roles y secretos»

Norma de IT del 2026-11-05 (spec 023 de la Mesa; prototipo aprobado). Todo desarrollo monta la **misma pantalla** (`ConfiguracionDesarrollo`, paquete `templates/auth-estandar/`) en `/configuracion`. Habla con la Mesa por el túnel de roles y secretos: la pantalla **pide** y la Mesa valida, aplica y audita.

- **Rol** es el único concepto que ve quien administra: nombre + **vistas** que puede abrir (cada una con sus acciones) + **datos** que consulta + la marca opcional «vista general» (lo que ve quien entra sin rol; nunca administrativo). «Perfil» es el nombre histórico del mismo concepto y no se muestra; en `ROLES.md` v2 las vistas son los `permisos` (módulos), las acciones son sus funciones y los datos son las áreas.
- **Dónde guarda la Mesa los roles (decisión 2026-11-06).** Los roles personalizados y sus asignaciones de un desarrollo **nuevo** viven en **tres tablas del esquema del propio desarrollo** (`App_<Área>_<Desarrollo>_Roles`, `…_RolesDatos`, `…_RolesPersonas`, **sin vigencia**), que **crea y valida el worker de la Mesa en cada despliegue** desde una plantilla estándar y cuyo SQL aprueba IT en el plan; SAC y todo desarrollo que ya tenía roles en las tablas centrales (`RegistroDesarrollos_Roles*`, con `IDProyecto`) siguen ahí hasta su migración. Un desarrollo está en un solo modo. `Admin`, `AdminApp` y `Usuario` viven en Entra ID. **Para quien desarrolla no cambia nada: la app solo usa el túnel** (`/mios`, `/estado`, `/solicitudes`…), no lee esas tablas directamente (el rol de la app solo tiene `SELECT` y la escritura es de la Mesa) y **no las declara ni las crea**: si el manifiesto de datos declara una tabla con esos nombres, el plan lo bloquea («nombre reservado»). Los roles son de gestión continua: no tienen vigencia ni fecha de vencimiento; una asignación dura hasta que quien administra la cambia o la quita.
- **Cuatro pestañas:** **Roles** (crear, editar, duplicar y eliminar; vista previa «así lo ve quien tenga este rol»), **Usuarios** (lista con filtros por nombre, rol y origen; asignar en un **modal de tres pasos**: usuario → rol → confirmar; si la persona es de otro departamento la Mesa exige dos textos de al menos 20 letras; reglas por departamento de Microsoft de `ROLES.md`), **Secretos** y **Actividad** (peticiones en curso e historial).
- **Quién puede qué:** el administrador **principal** hace todo; el **secundario** ve todo y edita la definición de los roles, pero no asigna usuarios ni carga secretos; quien no administra no ve «Configuración». El servidor lo impone siempre: lo que la pantalla deshabilita, la Mesa igual lo rechaza. En Entra ID el principal es el rol `Admin` (o una persona de IT) y el secundario el rol `AdminApp`; la tabla completa, por ruta, está en `CONTRATO-TUNEL-ROLES.md` §4.
- **Secretos:** solo los que declara `.agp/runtime.yaml` y que no crea la Mesa (ver «Secretos del desarrollo» abajo). El valor viaja una vez, se guarda y **nunca** se muestra ni se registra. «Cargar valor» y «Reiniciar app» son del administrador principal.
- **Contrato que verifican la Mesa y los agentes:** la raíz con `data-agp-configuracion="estandar"`, las pestañas con `data-agp-pestana="roles|usuarios|secretos|actividad"`, el modal con `role="dialog"` y `aria-modal="true"`, y el menú de usuario con `data-agp-menu="configuracion"`. Un frontend que no pueda traer el mismo archivo (otro framework de UI) lo cumple por marcas.
- **Conexión:** `ROLES_DESDE_MESA=true`, `MESA_API_URL` y `MESA_ID_PROYECTO` (no son secretos; se declaran en `env` de `.agp/runtime.yaml` y la API los entrega a la pantalla en `GET /api/config` → `roles`) y un `ROLES.md` v2 con los permisos (módulos y funciones) y los perfiles iniciales. La API de la Mesa con la que habla (`/api/roles-app/<id>/…`), cómo se autentica con el `id_token` de la app y qué devuelve cada ruta están en `CONTRATO-TUNEL-ROLES.md`.

### Qué ve cada persona

| Quién | Menú de usuario | Pestañas de `/configuracion` | Puede |
|---|---|---|---|
| **Sin sesión o sin acceso** | — | — | Ve la pantalla estándar de login o la de «sin acceso» (§2) |
| **Usuario** (con o sin rol; ve la vista general o los módulos de su rol) | Nombre y rol, «Cerrar sesión». **No** ve «Configuración» | Ninguna | Usar la app con lo que su rol le abre |
| **Administrador secundario** (`AdminApp`) | «Configuración» | Roles, Usuarios, Secretos, Actividad, **en solo lectura salvo la definición de los roles** | Crear, editar, duplicar y eliminar roles; ver secretos (nombre y fecha) y actividad, y la lista de usuarios solo si `ROLES.md` declara `adminAppAsignaRoles: true`. **No** asigna usuarios ni carga secretos (aviso «solo lectura» visible) |
| **Administrador principal** (`Admin`, o IT) | «Configuración» | Las cuatro, completas | Todo lo anterior, asignar usuarios (por persona o por departamento de Microsoft), cargar secretos y reiniciar la app |

Un `AdminApp` con `adminAppAsignaRoles: true` en `ROLES.md` también asigna personas de menor nivel (no a IT ni a otro administrador global). Cambiar **sus propios** permisos no lo permite nadie, salvo IT.

### Secretos del desarrollo: nombre, declaración y quién los carga

Un secreto es un dato que la app necesita para funcionar y que no puede estar en el repositorio (la URL de un servicio externo, una clave compartida, la firma de la sesión). La norma es una sola:

1. **Se declara por nombre, nunca por valor.** En `.agp/runtime.yaml`: `desarrollo: <nombre>` y, en `secrets`, `name` (la variable de entorno que verá la app) y `secret` (el nombre en el vault). El valor no entra al repositorio ni a un chat.
2. **El nombre es `<desarrollo>-<dato>`**: el `desarrollo` que declara el `runtime.yaml`, un guion y el dato en minúsculas, dígitos y guiones (hasta 127 caracteres en total). Un secreto que no empieza con `<desarrollo>-` no pasa la revisión de la Mesa.
3. **Vive en el vault de desarrollos** (`agp-desarrollos-secrets`); la app solo lo recibe como variable de entorno al arrancar. Nadie elige otro vault.
4. **Lo carga una persona, desde la pantalla:** el administrador principal en la pestaña **Secretos** (túnel) o, antes del primer despliegue, el responsable del desarrollo en la ruta «Prepara tu solicitud a IT» de la Mesa (paso «Despliegue», `specs/024` de la Mesa) (`PUT` solo de escritura: el valor jamás se lee ni se devuelve). Declarar un nombre nuevo es un cambio de `runtime.yaml` (un commit) y, como toca el contrato, lo aprueba IT.
5. **Los de conexión a bases de datos los crea la Mesa** al aprobar el plan (`…-db-server|user|username|pwd|password`): se listan como «creado por la Mesa» y no se cargan a mano (`PERMISOS-Y-SECRETOS-DEL-WORKER.md` §4).

```yaml
# .agp/runtime.yaml — correcto
apiVersion: runtime.agp/v1
desarrollo: portal-pedidos
secrets:
  - name: API_REPORTES                    # variable que lee el código
    secret: portal-pedidos-api-reportes   # <desarrollo>-<dato>
```

```yaml
# Incorrecto: no empieza con el desarrollo, tiene mayúsculas y un valor escrito en env
apiVersion: runtime.agp/v1
desarrollo: portal-pedidos
secrets:
  - name: API_REPORTES
    secret: Reportes_API
env:
  - name: CLAVE_REPORTES
    value: "valor-pegado-aqui"           # los valores secretos NO van aquí
```

`python -m agpctl runtime check --repo <ruta>` lo comprueba antes de pedir el despliegue (`agpctl/README.md`).

## 7. Si el desarrollo ya tiene su propio login o su propio gestor de roles

La norma es una sola. Un desarrollo que traiga **su propio mecanismo** (pantalla de login que no es la del kit, o una administración de usuarios y roles propia con su tabla de usuarios, sus rutas de administración y su propia pantalla) **debe pasar al de la norma**:

1. **Login:** el del kit sin cambios (`LoginScreen.jsx`, `login-estandar.css`).
2. **Roles:** la fuente de verdad pasa a la Mesa (`ROLES_DESDE_MESA=true`): el backend le pregunta por la persona con el mismo `id_token` y autoriza con lo que responde. Los roles que hoy tenga el desarrollo se declaran como `perfilesIniciales` en `ROLES.md` (con sus módulos y funciones) y las asignaciones actuales se cargan una vez a través de la Mesa.
3. **Pantalla:** la de §6 reemplaza a la administración propia de usuarios y roles; lo demás de esa administración (por ejemplo, reportes de actividad del desarrollo) puede quedar como enlace administrativo propio.

El Agente de Despliegue lo **detecta y lo reporta** (requisitos `configuracion_roles` y `mecanismo_propio_acceso`): no corrige ni elige; nombra qué mecanismo propio encontró y qué archivo del paquete debe adoptarse. La Mesa lo trata como aviso mientras IT no active el bloqueo, igual que el visual estándar.
