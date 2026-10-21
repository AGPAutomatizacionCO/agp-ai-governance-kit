# Nomenclatura de objetos de datos de un desarrollo

Norma de nombres para lo que un desarrollo CREA en una base de datos de AGP (esquema, tablas, usuario, rol y secretos). Es la fuente
normativa: el agente de despliegue la aplica al generar `ai/outputs/data-access-manifest.json`
(ver `schemas/data-access-manifest.schema.json`) y la Mesa de Requerimientos la valida antes de que el plan de despliegue llegue a IT.

Aplica solo a objetos **propios** del desarrollo (`origen: "propia_del_desarrollo"` con `crear_en_despliegue: true`). Las tablas
preexistentes conservan su nombre.

## Reglas

| Objeto | Formato | Ejemplo (área Manufacturing, desarrollo RPC) |
|---|---|---|
| Esquema (uno por desarrollo) | `app_<area>_<desarrollo>` en minúsculas | `app_manufacturing_rpc` |
| Tabla | `App_<Área>_<Desarrollo>_<tabla>` | `App_Manufacturing_RPC_users` |
| Usuario de la aplicación | `<esquema>_app` | `app_manufacturing_rpc_app` |
| Rol de la aplicación | `<esquema>_crud` | `app_manufacturing_rpc_crud` |
| Secretos en el vault de desarrollos | `<desarrollo>-db-user`, `<desarrollo>-db-pwd`, `<desarrollo>-db-server` | `rpc-db-user` |

- `<Área>` y `<Desarrollo>` son una sola palabra de letras y dígitos (sin guiones ni guiones bajos). `<Área>` es el departamento del
  responsable en Entra ID, el mismo que usa la Mesa para nombrar los recursos de Azure.
- `<tabla>` empieza por letra y usa letras, dígitos y guion bajo. Longitud total de la tabla: máximo 128 caracteres.
- El prefijo `App_<Área>_<Desarrollo>_` de la tabla **debe corresponder** al esquema (`app_<area>_<desarrollo>` en minúsculas). La
  Mesa lo comprueba; el esquema JSON no puede expresarlo.
- Columnas: letra inicial y letras, dígitos o guion bajo.
- Nunca se usan nombres reservados (`dbo`, `sys`, `INFORMATION_SCHEMA`, `guest`) ni nombres de objetos que ya existan en la base.

## Por qué el prefijo en la tabla y además un esquema

- **El prefijo identifica la pertenencia.** Las consultas SQL no siempre nombran el esquema y los catálogos y monitores listan tablas
  por su nombre: ver `App_Manufacturing_RPC_users` basta para saber a qué desarrollo pertenece.
- **El esquema es el límite de seguridad.** Todo lo que crea un desarrollo vive en su esquema. La cuenta que construye las tablas solo
  tiene permisos sobre ese esquema, y la cuenta de la aplicación solo opera sobre sus objetos. Así la base misma impide tocar tablas de
  otros desarrollos o de la empresa; no depende solo de la validación de la Mesa.
- **Las consultas sin esquema siguen funcionando** porque el usuario de la aplicación se crea con ese esquema como esquema por
  defecto (`DEFAULT_SCHEMA`). Un nombre sin esquema se resuelve primero ahí y después en `dbo`; el prefijo evita colisiones con `dbo`.

## Qué declara el manifiesto para que la Mesa cree las tablas

Una tabla propia que debe crearse en el despliegue lleva `"crear_en_despliegue": true`. Entonces:

- `origen` debe ser `propia_del_desarrollo`, el esquema debe cumplir el formato anterior y la tabla el prefijo.
- Cada columna declara `tipo` (de una lista cerrada, ver el esquema JSON), y opcionalmente `nulable`, `clave_primaria` y `referencia`
  (`"tabla.columna"` de otra tabla propia del mismo manifiesto).
- `operaciones_permitidas` es lo que el código ejecuta realmente. IT lo convierte en permiso al aprobar el plan: los `GRANT` se
  generan tabla por tabla y operación por operación, nunca a nivel de esquema.

La Mesa genera el T-SQL a partir de este JSON; el worker ejecuta ese script tal cual y su hash forma parte del plan que IT aprueba.
Nada de SQL escrito por el desarrollador se ejecuta con permisos de creación.

## Compatibilidad

Los manifiestos existentes siguen siendo válidos: las reglas de esta norma solo se exigen cuando `crear_en_despliegue` es `true`.
