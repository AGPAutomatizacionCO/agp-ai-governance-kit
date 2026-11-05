# Acceso y roles de un desarrollo: quién entra, con qué rol y cómo se declara

Norma para todo desarrollo con login de Microsoft Entra ID (todos los que se despliegan con la Mesa de Requerimientos). **Norma de IT del 2026-11-04: todo desarrollo funciona como la Mesa de Ayuda.**
Cualquier persona de AGP entra y ve la vista general; los roles específicos los da el administrador **dentro** de la app, desde su panel «Configuración» (como RPC), por persona o a toda un área de Microsoft. La Mesa los guarda y valida por detrás (túnel de roles). Restringir el
ingreso a personas asignadas es la excepción y se justifica. La Mesa lo muestra en el plan que aprueba IT, y los agentes lo documentan y lo verifican. Complementa `templates/auth-estandar/README.md` (el login) y
`PERMISOS-Y-SECRETOS-DEL-WORKER.md` (los datos).

## 1. La pregunta que todo desarrollo responde

> **¿Quién es el público del desarrollo?** Toda la organización, un área, varias áreas, o personas concretas.

La respuesta decide `acceso` en `.agp/entra.yaml`:

| `acceso` | Público | Qué pasa en Entra ID | Cómo se dan los roles |
|---|---|---|---|
| `organizacion` (**valor por defecto**) | Toda la organización AGP | La app **no exige asignación**: cualquier cuenta de AGP (un solo tenant) inicia sesión y ve la **vista general** | El administrador asigna los roles dentro de la app, en su panel «Configuración» (por persona o a toda un área de Microsoft). Quien no tiene rol ve la vista general (el perfil marcado como vista general) |
| `asignado` (excepción, con `justificacion`) | Un área, varias áreas o personas concretas, cuando la información no puede verla nadie más | La app **exige asignación**: solo entran las personas asignadas | Gestor de roles: el Responsable asigna a personas **del área del desarrollo** (motivo de la lista) y a personas **de otra área** (justificación propia de al menos 30 letras) |

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
justificacion: "Nómina individual: solo Compensaciones puede ver los salarios; ni la vista general puede mostrarse a otras áreas."
publico: "Personal de Compensaciones"
administradores:
  - correo: responsable@agpglass.com
```

## 2. Dónde se documenta (el `ROLES.md` del desarrollo)

El archivo `ROLES.md` (contrato `roles.agp/v1` o `v2`, lo valida la Mesa) es la vista **para personas** de los roles y las áreas. El desarrollo documenta ahí:

- **Roles:** `Admin` y `Usuario` (básicos) y los personalizados, con qué puede hacer cada uno.
- **Áreas y dominios** (`dominios` → `areas`): qué áreas existen en la app y quién pertenece a cada una. Es lo que permite distinguir «del área del desarrollo» de «de otra área» al asignar.
- **Vista general:** qué ve quien entra sin rol (con `acceso: organizacion`, toda persona de AGP).
- **`sinAcceso.mensaje` (obsoleto):** ya no se escribe un mensaje propio. Quien entra sin acceso ve la **pantalla estándar de AGP** (`SinAcceso`, paquete `templates/auth-estandar/`), que le dice que se comunique con el desarrollador funcional (`administradores[0]` de `.agp/entra.yaml`, con su correo @agpglass.com). Un `sinAcceso.mensaje` existente se ignora.
- **Coherencia con el manifiesto:** si `acceso: organizacion`, el texto dice que cualquier cuenta de AGP entra con la vista general; si `asignado`, dice quién puede pedir acceso y a quién.

## 3. Qué hace cada agente

**Agente documental.** Documenta la sección **«Acceso y roles»** del desarrollo (en la documentación funcional y de despliegue del expediente): público, `acceso` elegido y por qué, roles y áreas, qué es
administrativo y cómo se valida en la API. Si el expediente dice una cosa y `.agp/entra.yaml` otra (por ejemplo, «lo usa toda la organización» y `acceso: asignado`), lo registra como contradicción y no elige por su cuenta.

**Agente de despliegue.** Lee `.agp/entra.yaml` y `ROLES.md` y reporta, en `PreparacionDespliegue`, el requisito «acceso de usuarios»: el valor de `acceso`, si hay `justificacion` o `publico`, y si coinciden con
`ROLES.md` y con el código (`require_auth` para usuarios, `require_admin` o equivalente para lo administrativo). Reporta como hallazgo: `assignmentRequired: true` sin `acceso` (ya no cierra la app);
`organizacion` junto a `assignmentRequired: true`; `asignado` sin `justificacion` o sin `publico`; una vista general que muestra funciones administrativas; y un módulo administrativo que no exige rol.

**La Mesa.** Valida la forma, abre a la organización todo desarrollo que no declare `acceso: asignado`, muestra **«Acceso de usuarios»** en la página del plan y en el popup que IT aprueba (con o sin permisos de datos), y en el modo abierto
lo ata a la aprobación (entra al hash del plan). Un cambio de `acceso` toca `.agp/entra.yaml`, un archivo de contrato: exige la aprobación completa, no el redespliegue rápido.

## 4. El menú de usuario estándar: dónde se configura el acceso

Todo desarrollo trae el **mismo menú de usuario** (`UserMenu`, paquete `templates/auth-estandar/`): el botón con el nombre y el rol de quien entró y, al hacer clic, «Configuración» → «Administración» (la pantalla «Configuración del desarrollo», `/configuracion`, y los demás accesos administrativos) y «Cerrar sesión». Es el que RPC ya usa en producción y es **obligatorio**: ahí se llega a la gestión de quién entra y con qué rol, y es lo que el Agente de Despliegue y la Mesa verifican. El contrato (marcas `data-agp-menu`, «Menú de usuario», «Configuración», «Cerrar sesión») está en el README del paquete; un desarrollo con su propio componente lo cumple igual si lo respeta. «Configuración» solo se muestra a quien administra: el rol `Admin` o quien tenga enlaces administrativos propios.

## 5. Lista de verificación

1. `.agp/entra.yaml` declara `acceso` (`organizacion` o `asignado`) y su `justificacion` o `publico`.
2. `ROLES.md` describe roles y áreas, coherentes con `acceso` (sin `sinAcceso.mensaje`: lo reemplaza la pantalla estándar).
3. La API exige el rol `Admin` en todo lo administrativo; lo demás solo exige un token válido del tenant.
4. El expediente tiene la sección «Acceso y roles» y no contradice al manifiesto.
5. El encabezado monta el menú de usuario estándar (§4) y su «Configuración» solo la ve quien administra.
6. Monta la pantalla estándar `SinAcceso` (§2, marca `data-agp-sin-acceso="estandar"`) para quien inicia sesión sin acceso; el contacto es el primer administrador de `.agp/entra.yaml` con correo @agpglass.com. El agente de despliegue lo reporta como hallazgo si falta (aviso, igual que el visual estándar).
