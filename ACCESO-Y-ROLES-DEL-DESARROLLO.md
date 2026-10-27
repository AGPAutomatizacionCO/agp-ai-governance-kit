# Acceso y roles de un desarrollo: quién entra, con qué rol y cómo se declara

Norma para todo desarrollo con login de Microsoft Entra ID (todos los que se despliegan con la Mesa de Requerimientos). Cierra una ambigüedad: **«¿se despliega exigiendo asignar a cada persona un rol, o puede entrar
cualquiera de AGP?»** Lo decide y lo declara el desarrollo, la Mesa lo muestra en el plan que aprueba IT, y los agentes lo documentan y lo verifican. Complementa `templates/auth-estandar/README.md` (el login) y
`PERMISOS-Y-SECRETOS-DEL-WORKER.md` (los datos).

## 1. La pregunta que todo desarrollo responde

> **¿Quién es el público del desarrollo?** Toda la organización, un área, varias áreas, o personas concretas.

La respuesta decide `acceso` en `.agp/entra.yaml`:

| `acceso` | Público | Qué pasa en Entra ID | Cómo se dan los roles |
|---|---|---|---|
| `organizacion` | Toda la organización AGP (portales de autoservicio: p. ej. SOLPED Smart Suite, donde cualquier colaborador monta una solicitud) | La app **no exige asignación**: cualquier cuenta de AGP (un solo tenant) inicia sesión con el rol básico de **Usuario** | `Admin` (y los roles que el desarrollo defina) se asignan desde el Gestor de roles. Quien no tiene rol opera como Usuario |
| `asignado` (valor por defecto) | Un área, varias áreas o personas concretas | La app **exige asignación**: solo entran las personas asignadas | Gestor de roles: el Responsable asigna a personas **del área del desarrollo** (motivo de la lista) y a personas **de otra área** (justificación propia de al menos 30 letras) |

Reglas:

- **Siempre se declara.** Sin `acceso` la Mesa asume `asignado` y lo avisa; declararlo evita que un desarrollo abierto a toda la organización quede con restricción de rol por omisión.
- `acceso: organizacion` exige `justificacion` (al menos 40 caracteres: por qué el público es toda la organización y qué sigue protegido), un solo tenant (`signInAudience: AzureADMyOrg`) y no se combina con `assignmentRequired: true`.
- `acceso: asignado` describe el público en `publico` (hasta 300 caracteres: «personal de Supply Chain; otras áreas con justificación»).
- `assignmentRequired: false` a secas es una **excepción temporal de pruebas**, no una forma de abrir el acceso.
- **La autenticación corporativa no sustituye a la autorización.** Que cualquiera de AGP entre no abre lo administrativo: el módulo Administrador y toda función sensible siguen condicionados al rol (`Admin`) que valida
  la API con el token, y los permisos sobre datos siguen siendo los aprobados (ver `PERMISOS-Y-SECRETOS-DEL-WORKER.md`).

```yaml
# .agp/entra.yaml (abierto a toda la organización)
acceso: organizacion
justificacion: "Portal de autoservicio: cualquier colaborador de AGP puede montar una SOLPED; el módulo Administrador sigue exigiendo el rol Admin."
administradores:
  - correo: responsable@agpglass.com
```

```yaml
# .agp/entra.yaml (por asignación)
acceso: asignado
publico: "Personal del área de Supply Chain; personas de otras áreas con justificación del Responsable"
administradores:
  - correo: responsable@agpglass.com
```

## 2. Dónde se documenta (el `ROLES.md` del desarrollo)

El archivo `ROLES.md` (contrato `roles.agp/v1` o `v2`, lo valida la Mesa) es la vista **para personas** de los roles y las áreas. El desarrollo documenta ahí:

- **Roles:** `Admin` y `Usuario` (básicos) y los personalizados, con qué puede hacer cada uno.
- **Áreas y dominios** (`dominios` → `areas`): qué áreas existen en la app y quién pertenece a cada una. Es lo que permite distinguir «del área del desarrollo» de «de otra área» al asignar.
- **`sinAcceso.mensaje`:** qué ve quien entra sin tener acceso (solo tiene sentido con `acceso: asignado`).
- **Coherencia con el manifiesto:** si `acceso: organizacion`, el texto dice que cualquier cuenta de AGP es Usuario; si `asignado`, dice quién puede pedir acceso y a quién.

## 3. Qué hace cada agente

**Agente documental.** Documenta la sección **«Acceso y roles»** del desarrollo (en la documentación funcional y de despliegue del expediente): público, `acceso` elegido y por qué, roles y áreas, qué es
administrativo y cómo se valida en la API. Si el expediente dice una cosa y `.agp/entra.yaml` otra (por ejemplo, «lo usa toda la organización» y `acceso: asignado`), lo registra como contradicción y no elige por su cuenta.

**Agente de despliegue.** Lee `.agp/entra.yaml` y `ROLES.md` y reporta, en `PreparacionDespliegue`, el requisito «acceso de usuarios»: el valor de `acceso`, si hay `justificacion` o `publico`, y si coinciden con
`ROLES.md` y con el código (`require_auth` para usuarios, `require_admin` o equivalente para lo administrativo). Reporta como hallazgo: `acceso` sin declarar; `organizacion` sin justificación o junto a
`assignmentRequired: true`; `asignado` sin `publico`; y un módulo administrativo que no exige rol.

**La Mesa.** Valida la forma (falla si `organizacion` no cumple las reglas), muestra **«Acceso de usuarios»** en la página del plan y en el popup que IT aprueba (con o sin permisos de datos), y en el modo abierto
lo ata a la aprobación (entra al hash del plan). Un cambio de `acceso` toca `.agp/entra.yaml`, un archivo de contrato: exige la aprobación completa, no el redespliegue rápido.

## 4. Lista de verificación

1. `.agp/entra.yaml` declara `acceso` (`organizacion` o `asignado`) y su `justificacion` o `publico`.
2. `ROLES.md` describe roles, áreas y, si aplica, `sinAcceso.mensaje`, coherentes con `acceso`.
3. La API exige el rol `Admin` en todo lo administrativo; lo demás solo exige un token válido del tenant.
4. El expediente tiene la sección «Acceso y roles» y no contradice al manifiesto.
