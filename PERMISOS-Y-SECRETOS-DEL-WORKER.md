# Permisos y secretos: cómo funciona el worker y qué debe declarar un desarrollo

Norma para todo desarrollo que se despliega con la Mesa de Requerimientos y toca una base de datos. Explica **quién hace qué** (la Mesa, el worker, IT, el dueño del dato) para que el
desarrollo declare lo correcto desde el principio y no se entere en el despliegue. Lo que no está declarado **no se concede**. Complementa a `NOMENCLATURA-DATOS.md` (nombres de lo que el desarrollo
crea) y a `ARQUITECTURA-DESPLIEGUE.md` (un contenedor, un recurso).

## 1. Una sola declaración, dos archivos

| Archivo | Qué declara | Quién lo lee |
|---|---|---|
| `ai/outputs/data-access-manifest.json` | **Qué** datos toca: por fuente, `server` (Azure SQL, `*.database.windows.net`) y `database`; por tabla, esquema **real**, `origen` (`preexistente` o `propia_del_desarrollo`), `operaciones_permitidas`, `sensibilidad` y columnas sensibles | La Mesa arma con él el documento de permisos que IT aprueba |
| `.agp/runtime.yaml` | **Cómo** llega la conexión al contenedor: variables y **nombres** de secretos (nunca valores) | La Mesa y el worker configuran la Web App con él |

El manifiesto y el código deben coincidir. Si el código usa una tabla u operación que el manifiesto no declara, el desarrollo no cumple; si el manifiesto declara de más, IT aprueba de más.

## 2. Qué pasa al aprobar el plan (y quién lo hace)

1. **La Mesa** (al aprobar): por cada base del manifiesto crea una cuenta **propia del desarrollo** (`<desarrollo>_<base>_app`, rol `..._crud`), genera su contraseña y la guarda en el vault
   de desarrollos. El desarrollo no ve ni crea contraseñas.
2. **El worker** (al desplegar): otorga `GRANT` tabla por tabla, solo lo que dice el manifiesto aprobado, con el script cerrado cuyo hash aprobó IT, y verifica que quede **exactamente** lo aprobado.
3. **IT** crea una vez por base las cuentas de plataforma (`mesa_aprovisionador` y `worker_datos_user`) desde el botón «Bases de datos» del panel; no hay PowerShell por desarrollo.
4. **El dueño del dato** delega a la cuenta del worker cada tabla que el desarrollo lee o escribe en una base que ya existe (`GRANT SELECT ... WITH GRANT OPTION`). Es el límite real: el worker no puede
   conceder lo que no tiene delegado, y sin delegación el despliegue falla **sin dar acceso a medias**.

## 3. Qué se concede y qué no

- Por tabla: `SELECT`, `INSERT` y `UPDATE`. `INSERT` y `UPDATE` sobre tablas **preexistentes** son una excepción que IT ve resaltada y exige explicar el motivo en la descripción de la tabla.
- **Nunca** `DELETE` ni permisos de esquema (`ALTER`, `CONTROL`, `CREATE`...).
- Sensibilidad **media o alta** sobre tablas preexistentes no se concede por esta vía: la aprueba el dueño del dato.
- Las columnas marcadas como sensibles (p. ej. correos) no bloquean, pero IT las ve resaltadas: aprobar el documento es aprobar esa excepción.
- Una cuenta de solo lectura general del catálogo del IED (`fuentes: [...]` en `runtime.yaml`) existe para casos de consulta amplia y está limitada a una **lista cerrada**; para un desarrollo concreto
  se prefiere la cuenta acotada a sus tablas.

## 4. Cómo se declara la conexión en `.agp/runtime.yaml`

La Mesa reconoce la conexión de una base por **prefijo**. Para cada base declara una variable con el nombre de la base y tres secretos:

```yaml
env:
  - name: CALENDARIO_DB_NAME            # <PREFIJO>DB_NAME o <PREFIJO>DB_DATABASE: el valor es la base del manifiesto
    value: "CalendarioAGP"
secrets:
  - name: CALENDARIO_DB_SERVER          # <PREFIJO>DB_SERVER (o DB_HOST)
    secret: mi-desarrollo-calendario-db-server
  - name: CALENDARIO_DB_USER            # <PREFIJO>DB_USER o DB_USERNAME
    secret: mi-desarrollo-calendario-db-username
  - name: CALENDARIO_DB_PASSWORD        # <PREFIJO>DB_PASSWORD (o DB_PWD)
    secret: mi-desarrollo-calendario-db-password
```

- El secreto de usuario termina en `-db-username` (o `-db-user`): de él sale el nombre de la cuenta (`mi_desarrollo_calendario_app`) y su rol.
- Los secretos se llaman `<desarrollo>-<base>-db-server|username|password`. La Mesa los crea al aprobar; no se cargan a mano.
- El código lee esos nombres de variable de entorno (con valores por defecto para desarrollo local). Nunca lleva credenciales, ni hay `.env` real en el repositorio.
- Las tablas **propias** del desarrollo (`crear_en_despliegue`) viven en su esquema `app_<area>_<desarrollo>` (ver `NOMENCLATURA-DATOS.md`); las preexistentes, en su esquema real (p. ej. `dbo`), nunca en
  uno inventado.

## 5. Lo que valida la Mesa antes de que IT apruebe

Falla (no apto) y dice qué corregir:

- `server` ausente o que no sea Azure SQL; esquema de una tabla sin calificar; sensibilidad media/alta sobre una tabla preexistente.
- Una base del manifiesto sin su conexión declarada en `runtime.yaml` (variable `<PREFIJO>DB_NAME` y los tres secretos).
- El Dockerfile instala `msodbcsql*` sin `libgssapi-krb5-2` (el contenedor arranca y `/api/health` responde 200, pero toda ruta con SQL responde 503). Referencia:
  `templates/Dockerfile-odbc-sqlserver.snippet`.
- Una base cuyas cuentas de plataforma aún no existen (se ve en el botón «Bases de datos» del panel de IT).

## 5.1. Librería de conexión a SQL Server según el framework

La conexión a la base la hace **solo el backend**, y la librería depende de su stack. El agente de despliegue identifica el stack por sus manifiestos (`requirements.txt`, `package.json`, `*.csproj`, `pom.xml`)
y reporta la librería que corresponde y dónde debe estar; la Mesa y el worker no la instalan por el desarrollo.

| Stack del backend | Librería de conexión | Qué más necesita la imagen | Dónde se comprueba |
|---|---|---|---|
| Python (FastAPI, Flask, Django) | `pyodbc` (o SQLAlchemy con `mssql+pyodbc`) | Driver ODBC de Microsoft (`msodbcsql18` o `msodbcsql17`), `unixodbc` y **`libgssapi-krb5-2`** instalados explícitamente en el Dockerfile. Ver `templates/Dockerfile-odbc-sqlserver.snippet` | `requirements.txt` y Dockerfile. La Mesa bloquea el plan si falta `libgssapi-krb5-2` |
| Node.js (Express, NestJS, Next.js en servidor) | `mssql` (usa `tedious`, JavaScript puro) | Nada del sistema: **no necesita ODBC ni `libgssapi`** | `package.json` del backend |
| .NET | `Microsoft.Data.SqlClient` | Nada del sistema (runtime de la imagen base) | `*.csproj` |
| Java | `mssql-jdbc` (`com.microsoft.sqlserver`) | Nada del sistema (JRE de la imagen base) | `pom.xml` o `build.gradle` |

Reglas comunes:

- **El frontend (React, Vite, Vue, Angular) no lleva librería de base de datos ni credenciales.** Corre en el navegador y habla solo con su propia API. Un driver, una cadena de conexión o una variable `DB_*` en el
  código del frontend, o expuesta por Vite (`VITE_*`), es un hallazgo bloqueante: cualquier valor que llega al navegador es público.
- La conexión usa siempre `Encrypt=yes` y `TrustServerCertificate=no` (Azure SQL), con el servidor, la base, el usuario y la clave que llegan por variables de entorno desde los secretos (ver sección 4); nunca
  valores escritos en el código ni en un `.env` del repositorio.
- Si el stack no está en la tabla, el agente no inventa la librería: lo marca como pendiente de decisión de IT.

## 6. Estado local y persistencia

La Mesa crea las Web Apps **sin almacenamiento persistente** (`WEBSITES_ENABLE_APP_SERVICE_STORAGE=false`): un archivo local (SQLite, evidencias, JSON) se pierde al reiniciar. Lo que debe sobrevivir va
en la base de datos declarada en el manifiesto. Un desarrollo que ya está en Azure con su propia Web App y guarda datos en `/home` solo puede adoptarse con un plan acordado con IT, que primero
migra o respalda esos archivos (el despliegue de la Mesa sobre una Web App existente no toca sus App Settings ni su almacenamiento, pero el almacenamiento local sigue sin ser parte de la norma).

## 7. Lista de verificación antes de pedir el despliegue

1. El manifiesto declara cada base con su `server` y cada tabla con su esquema real, operaciones mínimas y sensibilidad honesta.
2. `runtime.yaml` declara, por base, la variable `<PREFIJO>DB_NAME` y los tres secretos, y el código los lee.
3. No hay `DELETE` en lo declarado, ni permisos de esquema sobre tablas preexistentes.
4. Si lee tablas de otra persona o área, el dueño del dato sabe que debe delegar el `SELECT` al worker.
5. La librería de conexión corresponde al stack del backend (sección 5.1); en Python, el Dockerfile instala el driver ODBC completo (`msodbcsql*`, `unixodbc` y `libgssapi-krb5-2`). El frontend no lleva ninguna.
6. Si la Web App ya existe, IT la adopta primero («Adoptar recursos existentes») y el publicador propio se retira: el único camino de publicación es el que dispara la Mesa.
