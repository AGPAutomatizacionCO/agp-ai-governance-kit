# Cómo dejarlo funcional: acceso, roles y secretos en pasos cortos

Guía para la persona o el agente que acaba de copiar el paquete `templates/auth-estandar/` y quiere que el desarrollo **funcione de punta a punta** (login, menú, «Configuración de roles y secretos», secretos) y llegue a IT sin preguntas.
Cada paso dice qué hacer y dónde está la regla completa. La lista para comprobar que todo quedó en el repositorio está al final (y en `OBLIGATORIOS-DEL-DESARROLLO.md`).

## Pasos

### 1. Identidad: `.agp/entra.yaml`

Copia `templates/auth-estandar/.agp/entra.yaml` y completa `administradores` (al menos el desarrollador funcional, con su correo @agpglass.com). Deja `acceso: organizacion` (la norma) salvo que IT apruebe `asignado` con `justificacion` y `publico`.
No hay secreto de cliente (`secrets: []`). Regla: `ACCESO-Y-ROLES-DEL-DESARROLLO.md` §1.

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

### 5. El backend lee el rol por el túnel

Copia `templates/auth-estandar/backend/src/helpers/roles_mesa.py` (junto a `auth.py`) y úsalo después de validar el token:

```python
from flask import request
from src.helpers import roles_mesa

id_token = request.headers.get("Authorization", "").removeprefix("Bearer ")   # el mismo token que valida require_auth
alcance = roles_mesa.resolver(g.user_email, id_token)
if not alcance.administra:   # nivel global o admin
    return jsonify({"message": "Solo administradores"}), 403
```

Pregunta `GET /api/roles-app/<id>/mios` con el mismo `id_token`, guarda la respuesta 60 s y **falla cerrada** (vista general) si la Mesa no responde. Contrato: `CONTRATO-TUNEL-ROLES.md`.
El frontend usa el cliente `src/services/rolesMesa.js`, el menú `UserMenu` (con «Configuración» directo a `/configuracion`) y la pantalla `ConfiguracionDesarrollo`, todos del paquete.

### 6. La app SOLO usa el túnel: no crea ni escribe tablas de roles

- **Hoy** los roles personalizados y sus asignaciones viven en tablas centrales de la Mesa (`RegistroDesarrollos_Roles*`). La app los lee **por el túnel** y solo la Mesa escribe.
- La app **no crea, no escribe y no necesita** tablas de roles propias, y no tiene una tabla de usuarios propia. No llames a Graph para roles.
- Las tres tablas por desarrollo (`App_<Área>_<Desarrollo>_Roles`, `…_RolesDatos`, `…_RolesPersonas`) son el **modelo objetivo, pendiente y no implementado** (spec 018 de la Mesa). No las declares en el manifiesto de datos ni las leas directamente.
- Los roles son de gestión continua: **sin vigencia** ni fecha de vencimiento.

### 7. En local (sin la Mesa)

- `DISABLE_AUTH=true` y `DEV_USER_EMAIL=tu.correo@agpglass.com` saltan el login **solo en tu equipo** (dentro de Azure se ignoran).
- Con `ROLES_DESDE_MESA` apagado (lo normal en local, porque la plantilla exige una Mesa `https`), el helper no llama a nada: usa `ROLES_LOCAL_NIVEL=admin|usuario|general` (por defecto `general`, solo lectura). La pantalla de «Configuración» dirá que la conexión con la Mesa no está activa: es lo esperado.
- Para ver la pantalla con datos reales, ábrela en un desarrollo ya registrado en la Mesa (con tu sesión de Microsoft), no desde tu equipo.
- Los datos en SQLite (si los usas en local) se declaran como **tabla propia nueva** para el despliegue (`NOMENCLATURA-DATOS.md`); nace vacía.

### 8. Comprueba y pide el despliegue

Recorre la lista de comprobación de abajo y pídele al Agente de Despliegue su informe.

## Lista de comprobación previa a pedir el despliegue

Cada punto es verificable en el repositorio (el Agente de Despliegue lo reporta dentro de `entra`, `roles`, `acceso_usuarios`, `configuracion_roles`, `menu_usuario`, `runtime`, `secretos_norma` y `mecanismo_propio_acceso`).

- [ ] `.agp/entra.yaml`: `acceso`, `administradores[0]` con correo @agpglass.com, `secrets: []`.
- [ ] `ROLES.md` v2 con `permisos` y `perfilesIniciales`, sin `sinAcceso.mensaje`.
- [ ] `.agp/runtime.yaml`: `ROLES_DESDE_MESA`, `MESA_API_URL` (https) y `MESA_ID_PROYECTO` en `env`; `desarrollo:` y todo secreto como `<desarrollo>-<dato>`; sin valores secretos; `python -m agpctl runtime check` sin `issues` ni `avisos`.
- [ ] Backend: lee el rol por `GET /api/roles-app/<id>/mios` con el `id_token` (helper `roles_mesa.py` o equivalente) y falla cerrada.
- [ ] Frontend: `UserMenu` con las marcas `data-agp-menu` y «Configuración» directo a `/configuracion`; `ConfiguracionDesarrollo` montada (`data-agp-configuracion="estandar"`); cliente `rolesMesa.js`.
- [ ] Pantalla `SinAcceso` estándar (sin texto libre) y `GET /api/config` con `contactoNombre` y `contactoCorreo`.
- [ ] Ninguna tabla de usuarios o de roles propia, ningún `CREATE TABLE`/`INSERT`/`UPDATE` sobre tablas de roles, ninguna ruta propia de administración de usuarios o roles; el manifiesto de datos no declara las tres tablas de roles.
- [ ] Sin `.env` real en el repositorio; `DISABLE_AUTH` solo en local.
