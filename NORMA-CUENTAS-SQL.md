# Norma: cuentas SQL de la plataforma (Accesos SQL)

**Decisión de IT del 2026-10-30.** Aplica a IT y a la Mesa de Requerimientos. Un desarrollo **no** crea ni administra estas cuentas: solo declara qué tablas toca
(`PERMISOS-Y-SECRETOS-DEL-WORKER.md`, `NOMENCLATURA-DATOS.md`). Se configuran desde **IED → Configuración → «Accesos SQL»** (solo IT), con una sola credencial de administración
por servidor, que se escribe una vez, se usa en ese momento y se descarta: nunca se guarda en disco, vault, caché ni auditoría.

## 1. Las cuentas

| Cuenta | Una por | Para qué | Qué puede | Qué nunca puede |
|---|---|---|---|---|
| `mesa_aprovisionador` | base | La Mesa crea esquemas, usuarios y roles de cada desarrollo | `CREATE SCHEMA`, `ALTER ANY USER`, `ALTER ANY ROLE` | Leer o escribir datos |
| `worker_datos_user` | base | El worker crea las tablas propias y reparte permisos a los desarrollos | `SELECT`, `INSERT`, `UPDATE` de toda la base **WITH GRANT OPTION** y el rol `worker_datos` (`CREATE TABLE`) | `DELETE`, `ALTER` sobre lo ajeno, `CONTROL` |
| `<servidor>_sql` | servidor | La consola de administrador de IED ejecuta SQL | Leer, escribir y crear o alterar objetos (`db_datareader`, `db_datawriter`, `db_ddladmin`, `EXECUTE`) | **Otorgar o quitar permisos**, administrar usuarios o roles (sin `db_owner` ni `db_securityadmin`; `DENY ALTER ANY USER/ROLE`), tener `CONTROL` |
| `app_<área>_<desarrollo>_app` | desarrollo | La aplicación del desarrollo | Solo lo que declara su manifiesto y IT aprobó (`NOMENCLATURA-DATOS.md`) | Nada fuera de su esquema y de las tablas aprobadas |

**Nombre de la cuenta de consulta de IED:** `<servidor>_sql`, con el nombre corto del servidor en minúsculas y `_` en lugar de `-`: `agpcolsap` → `agpcolsap_sql`,
`agpcolombia` → `agpcolombia_sql`, `agp-sisglass` → `agp_sisglass_sql`. Hay varios servidores y bases: un nombre genérico no diría de cuál es en SQL ni en la auditoría.
Es un login en `master` y un usuario en cada base que IT marque; la credencial es por servidor, los permisos son por base.

## 2. Dónde viven los secretos

| Secreto | Vault | Nombre |
|---|---|---|
| Cuentas del worker y de la Mesa, por base | **vault de desarrollos** (`agp-desarrollos-secrets`) | `datos-<base>-{prov,worker}-{user,pwd}` |
| Cuentas de cada desarrollo | **vault de desarrollos** | `<desarrollo>-db-{user,pwd,server}` |
| Cuenta de consulta de IED, por servidor | **vault de AGP** (`agpcol-db-secrets`) | `ied-sql-<servidor>-{user,pwd}` |

La cuenta de consulta de IED vive aparte porque es la de mayor alcance y solo la usa la Mesa. Para escribir ahí sin dar escritura sobre todo el vault, IT crea de antemano los dos secretos
del servidor con el valor `pendiente-de-configurar` y asigna «Key Vault Secrets Officer» a la identidad de la Mesa **solo sobre esos dos secretos**. La Mesa trata ese valor como
«sin configurar» y lo sobrescribe con la clave real. Nunca se repite el paso de crearlos después de configurar: pisaría la clave real.

## 3. Reglas

1. **Se usa solo desde IED.** La credencial de `<servidor>_sql` no se saca del vault para usarla en SSMS ni en otra herramienta: se saltaría la auditoría.
2. **Cada ejecución queda auditada** (quién, cuándo, base, hash y texto del SQL, modo, resultado y **la cuenta usada**), también cuando se deniega o falla. Crear o reconfigurar una cuenta
   también (sin credenciales).
3. **La consola de administrador sigue bloqueando** `GRANT`, `REVOKE`, `DENY`, `ALTER ROLE`, crear o borrar usuarios y logins, `USE`, `BACKUP`, `xp_*` y similares, aunque la cuenta no podría. Modo
   «ensayo» (revierte todo) y confirmación para lo que modifica o destruye. Solo IT con rol ADMIN en IED.
4. **Las claves nacen en la Mesa** (aleatorias, que cumplen la política de Azure SQL) y van directo al vault: nadie las ve ni las escribe. Rotarlas es una opción explícita.
5. **Una acción por servidor:** «Configurar accesos» crea, con la misma credencial, las cuentas del worker de cada base elegida y la de consulta. Cada parte es independiente: si una falla, las
   demás se hacen igual y el resultado dice qué salió. Repetir el botón repara.
6. **El worker siempre delega** (`SELECT, INSERT, UPDATE` con `WITH GRANT OPTION`): reparte permisos a los desarrollos sobre cualquier tabla de la base, sin pedirle al DBA tabla por tabla. Lo
   que se concede a cada desarrollo lo fija el plan que IT aprueba (script cerrado por hash); las tablas de sensibilidad media o alta las aprueba el dueño del dato.
   El precio: el worker puede leer toda esa base.

## 4. Qué no cubre
Ninguna de estas cuentas se probó contra una base de prueba (no existe una): el T-SQL generado y su orden tienen pruebas de unidad, y se verificó con `SELECT` sobre el catálogo de la base. La
alternativa `db_securityadmin` (repartir permisos sin leer datos) existe en la Mesa pero no se ofrece en pantalla ni se ha probado.
