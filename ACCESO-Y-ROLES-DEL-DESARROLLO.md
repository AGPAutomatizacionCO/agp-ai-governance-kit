# Acceso y roles del desarrollo

Actualización propuesta por instrucción de IT, 2026-11-17. Para configuración propia, la fuente de verdad es el backend y las tablas del desarrollo; no se requiere una llamada a la Mesa para entrar, resolver roles, asignarlos ni cargar secretos. La gestión de roles sigue siendo opcional para desplegar, como se estableció el 2026-11-11. Esta guía no añade controles al test ni al worker IT.

## Autenticación y público

MSAL/Entra ID autentica, con tenant corporativo, firma, audiencia y vigencia verificadas en la API. No se incluyen secretos de cliente en el navegador. La autenticación no reemplaza la autorización de pantallas, acciones ni datos.

`.agp/entra.yaml` mantiene la decisión del público:
- `acceso: organizacion`: cualquier cuenta del tenant puede autenticarse; quien no tenga rol ve la vista general sin datos sensibles o la pantalla SinAcceso documentada.
- `acceso: asignado`: excepción con justificación y público declarado, sujeta a revisión de IT. No convertir el login abierto en permiso administrativo.

Los administradores iniciales ya aprobados pueden conservarse para iniciar la gestión, sin inventar nuevas personas o ampliar sus permisos. Documentar su protección y recuperación. No confundir el rol Admin de Entra con un permiso que el cliente pueda autodeclarar.

## Configuración dentro de la aplicación

Seguir [Configuración local de roles y secretos](CONFIGURACION-LOCAL-ROLES-Y-SECRETOS.md): contiene cómo mostrar y proteger la vista, asignar los perfiles a personas, auditar en tablas propias y escribir secretos permitidos mediante la identidad administrada propia en Key Vault. Incluye archivos de referencia en SmartBending y Portal SAC y pruebas de aceptación/rechazo.

Para crear las tablas de roles de un desarrollo nuevo (patrón de dos tablas propias, permisos que concede el worker, nombres que no chocan con el túnel, RRHH/People en AGP_RRHH y AGPTS como referencia) seguir [Roles propios en tablas del desarrollo](ROLES-PROPIOS-EN-TABLAS-DEL-DESARROLLO.md).

Si existe `ROLES.md`, documenta perfiles y capacidades reales, vista general, administradores iniciales y correspondencia con la matriz de autorización y el manifiesto de datos. No crear dominios o áreas ficticias para satisfacer una plantilla. Las asignaciones propias se declaran y aprovisionan con su contrato de datos, dentro del esquema normativo de cada desarrollo. No usar tablas de la Mesa para resolver el acceso. Los roles no tienen vigencia: una asignación dura hasta que un administrador la cambie o retire; la expiración de la sesión no elimina la asignación.

La pantalla Configuración es una única entrada administrativa; mostrarla solo a quien tenga capacidad y comprobar el mismo permiso vigente en TODOS los endpoints. Las sesiones antiguas o una caché de respaldo no deben permitir administrar después de revocar el acceso. No basta con ocultar un botón. Sin permiso, devolver 403 y mostrar la vista sin acceso correspondiente.

**Cuándo se muestra `SinAcceso` y cuándo la vista general.** Con `acceso: organizacion` (la norma) quien inicia sesión y no tiene fila en la tabla de personas, o tiene un perfil que ya no existe, ve la **vista general** (solo lectura, sin datos sensibles): `roles_propios.resolver` lo devuelve como nivel `general`. `SinAcceso` (sin texto libre, con el contacto del desarrollador funcional) se monta cuando el desarrollo no tiene vista general que mostrar o con `acceso: asignado` y la persona no está asignada. Si la base no responde, la persona queda en `general` (falla cerrada), nunca con más permisos. Plantillas: `templates/auth-estandar/` (`roles_propios.py`, `bp_configuracion.py`, `ConfiguracionDesarrollo.jsx`, `SinAcceso.jsx`); el ejemplo de manifiesto de las dos tablas y de la vista de usuarios está en `examples/data-access-manifest.roles-propios.valid.json`.

Los secretos se declaran por referencia en `.agp/runtime.yaml`; sus valores se cargan en Key Vault y no aparecen en documentos, código, `.env.example`, manifiestos, respuesta ni auditoría. No sobrescribir las credenciales SQL aprovisionadas desde una pantalla de secretos manuales.

## Integración heredada

[CONTRATO-TUNEL-ROLES.md](CONTRATO-TUNEL-ROLES.md) conserva el contrato histórico de la integración voluntaria con la Mesa. No impone una dependencia para desarrollos con autorización propia ni constituye el patrón a copiar para la migración solicitada. Conservar asignaciones y auditoría antes de retirar el túnel; no mezclar fuentes de permisos. El paquete `templates/auth-estandar` sigue sirviendo para MSAL, login y SinAcceso, pero sus componentes antiguos de roles/secretos requieren adaptación a la API local.

Compatibilidad histórica: `RegistroDesarrollos_Roles*` corresponde a asignaciones centrales que algunos desarrollos conservaban antes de migrar. En el modo de túnel, el worker crea y valida sus tablas estándar y cada nombre reservado sigue sujeto a ese contrato. Esta propuesta no borra ni migra esas asignaciones; las tablas propias nuevas usan nombres no reservados y su manifiesto aprobado.
