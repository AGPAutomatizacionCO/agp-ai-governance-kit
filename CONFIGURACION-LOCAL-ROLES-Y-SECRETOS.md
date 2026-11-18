# Configuración local de roles y secretos

Guía de implementación propuesta a revisión de IT, 2026-11-17. Para desarrollos con autorización propia, el camino de acceso y configuración no requiere llamadas a la Mesa. La gestión de roles sigue siendo opcional para desplegar; esta guía no añade un requisito al test del worker ni al worker IT. No cambia asignaciones ni migra datos automáticamente.

**Tablas de roles:** cómo se crean, con qué permisos y con qué nombres (patrón de dos tablas, AGPTS como referencia, RRHH/People) está en [Roles propios en tablas del desarrollo](ROLES-PROPIOS-EN-TABLAS-DEL-DESARROLLO.md).

## Responsabilidades

- Microsoft Entra ID y MSAL autentican la identidad. La API comprueba firma, tenant, audiencia y vigencia. El navegador no decide quién es administrador.
- El backend del desarrollo autoriza con sus tablas y su matriz real de perfiles/pantallas/acciones. Conserva el alcance aprobado del manifiesto de datos y el principio de mínimo privilegio.
- La configuración escribe asignaciones y auditoría en tablas del esquema propio. La Mesa puede aprobar y aprovisionar ese contrato durante el despliegue; no participa en cada login o cambio de rol.
- Los valores de secretos permanecen en Azure Key Vault. La API del desarrollo utiliza SU identidad administrada y un listado de nombres permitido en su contrato. No usa tokens, endpoints ni permisos de la Mesa para gestionarlos.

## Cómo asignar acceso a la vista

1. Define qué perfil administra el desarrollo y qué pantallas/acciones tiene cada perfil. Asocia las asignaciones a la identidad corporativa comprobada por el backend (tenant + object ID cuando sea posible; si se usa correo, normalizado, corporativo y obtenido del token validado).
2. Declara las tablas propias de personas, perfiles si son dinámicos, y auditoría en `ai/outputs/data-access-manifest.json`, con nombres según NOMENCLATURA-DATOS.md y permisos mínimos. No uses tablas del esquema de la Mesa. No uses los nombres reservados del antiguo túnel sin verificar el contrato de aprovisionamiento.
3. Muestra una única entrada Configuración a quien tenga la capacidad administrativa. Usa el mismo permiso para proteger la ruta de la pantalla. Una persona sin rol conserva la vista general o SinAcceso, según el público documentado; no recibe permisos operativos implícitos.
4. Vuelve a comprobar ese permiso en TODOS los endpoints administrativos. Un JWT con un rol antiguo no debe permitir asignar roles o cargar secretos después de revocar al administrador. Falla cerrada si no puedes confirmar el permiso. No aceptes actor, rol efectivo, SQL, vault ni identidad Azure del cliente.
5. Audita actor, destinatario, perfil anterior/nuevo, fecha y resultado. Asignación y auditoría se guardan en una sola transacción. Documenta la renovación de sesiones y la invalidación de cachés entre instancias. Evita que un administrador se bloquee a sí mismo o retire al administrador inicial desde una operación ordinaria.

Ejemplo de navegación (adaptar al framework, no es control de seguridad):

```jsx
{sesion.puedeConfigurar && <Link to="/settings">Configuración</Link>}
<Route path="/settings" element={sesion.puedeConfigurar ? <Configuracion /> : <SinAcceso />} />
```

La API **no** confía en `sesion.puedeConfigurar` del navegador: valida la sesión y lee su autorización vigente. Si el proyecto usa perfiles fijos, la pantalla debe asignar esos perfiles y mostrar las vistas reales de la matriz. No ofrezcas un editor de permisos que la API después ignora. Si son dinámicos, todas las rutas sensibles deben consultar el mismo catálogo de permisos, con pruebas de revocación.

## Secretos sin túnel

- `.agp/runtime.yaml` declara nombres y referencias, nunca valores. `.env.example` solo enumera variables vacías. No se guardan credenciales en SQL, código, historial, navegador ni archivos de evidencia.
- La pantalla permite cargar o actualizar exclusivamente secretos manuales propios, por nombre permitido del lado servidor. No permite sobrescribir credenciales SQL aprovisionadas, secretos de otros desarrollos, ni elegir un vault arbitrario.
- El backend usa `ManagedIdentityCredential` y `SecretClient.set_secret`, con vault fijado en configuración confiable. No se necesita una contraseña de cliente para esta conexión. No añadir búsqueda de credenciales personales como respaldo en producción.
- IT revisa el permiso de la identidad administrada de ESA aplicación: `Key Vault Secrets Officer` acotado a los secretos autorizados o un rol personalizado de escritura equivalente. Leer referencias en App Service y escribir desde configuración son permisos distintos. No otorgar el rol a usuarios del navegador ni al vault completo por comodidad.
- La API devuelve solo nombres, referencias y confirmación, nunca valores. No llama `get_secret` para rellenar formularios; tampoco enumera todo el vault para acreditar el estado. Un nombre declarado no prueba que el secreto exista.
- No incluir body, valor, token ni errores crudos del SDK en logs, trazas, respuesta de validación o auditoría. Vaciar el campo de contraseña tras intentar la carga; proteger autenticación, transporte y límites de tamaño.
- Registrar intento y resultado sin valor. SQL y Key Vault no comparten transacción: si KV confirma pero falla la auditoría posterior, informar el estado parcial y revisar el registro de KV antes de repetir.
- Cambiar un secreto no equivale a desplegar ni a reiniciar. Documentar cuándo Azure actualiza referencias y cuándo el backend vuelve a leer la configuración; rotar una clave de sesión puede invalidar sesiones.

## Ejemplos verificables

### SmartBending — configuración local (PR asociado a esta guía)

Repositorio: https://github.com/AGPAutomatizacionCO/AGP_CO_MANUFACTURING_WEB_SMARTBENDING

Archivos que debe revisar el integrador en el PR antes de copiar:
- `docs/CONFIGURACION-LOCAL.md`: operación, tablas, permiso de la identidad y limitaciones.
- `frontend/src/components/UserMenu.tsx`, `frontend/src/pages/SettingsPage.tsx`, `frontend/src/PartialApp.tsx`: mostrar la entrada y proteger la vista.
- `frontend/src/screens/ConfiguracionDesarrollo.tsx`, `frontend/src/services/configuracionLocal.ts`: formulario y cliente de la API propia.
- `backend/api/routers/configuracion.py`, `backend/services/configuracion_local.py`: autorización actual, transacción de perfiles, auditoría y Key Vault acotado.
- `backend/services/roles_propios.py`, `backend/rbac.py`: perfil propio y matriz real de vistas.
- `backend/tests/test_configuracion_local.py`: aceptación y rechazos, sin SQL empresarial ni KV real.

Son dos tablas de `app_manufacturing_smartbending` en AGP_Colombia: `App_Manufacturing_SmartBending_roles_personas` y `App_Manufacturing_SmartBending_roles_auditoria`. No copiar estos nombres a otro desarrollo: cada uno declara sus propias tablas. Los perfiles son los existentes; el catálogo no crea permisos nuevos. El PR no configura IAM ni demuestra conectividad productiva.

### Portal SAC — referencia existente para roles propios

Repositorio: https://github.com/AGPAutomatizacionCO/AGP_CO_FINANCE_PORTAL_SAC

Decisión y migración: [ADR-010](https://github.com/AGPAutomatizacionCO/AGP_CO_FINANCE_PORTAL_SAC/blob/main/ai/decisions/ADR-010-roles-propios-en-agp-colombia.md).
Revisar `backend/app/auth.py`, `backend/app/admin_router.py` y `backend/app/usuarios_store.py` para autorización y gestión de usuarios propios. Este ejemplo acredita ese patrón de roles; no certifica que todos sus servicios o secretos sean independientes de la Mesa. No se modifica SAC ni AGPTS en esta propuesta.

## Migración y pruebas

No retirar controles ni borrar asignaciones para eliminar la dependencia. Inventariar asignaciones vigentes, mapearlas a perfiles admitidos, preservar auditoría y documentar rollback. Confirmar el permiso SQL aprobado del desarrollo antes de publicar; no reutilizar credenciales de la Mesa. Mantener el ensayo sin datos ni secretos: ningún import o health debe abrir SQL o KV.

Pruebas mínimas: sesión válida con rol permitido; 401 sin sesión; 403 sin capacidad; rechazo del administrador revocado; perfil desconocido; rollback si falla auditoría; secretos ajenos/SQL bloqueados; actor no falsificable; ninguna respuesta ni log con valores; arranque de ensayo sin conexiones. Las pruebas usan datos ficticios y dobles de SQL/KV; la revisión de IAM productivo requiere autorización aparte.

## Compatibilidad con el antiguo túnel

`CONTRATO-TUNEL-ROLES.md` y `templates/auth-estandar/src/services/rolesMesa.js` describen una integración heredada, no el backend de esta guía. Conservarla solo para desarrollos que la usan explícitamente durante una migración aprobada. No mezclar ambas fuentes de autorización ni copiar esas rutas al implementar configuración propia. La plantilla de MSAL/login sigue siendo referencia de autenticación; su pantalla antigua de roles/secretos necesita adaptación a la API local.

Referencias oficiales SDK: [Key Vault Python](https://learn.microsoft.com/en-us/python/api/overview/azure/keyvault-secrets-readme), [identidad administrada](https://learn.microsoft.com/en-us/python/api/overview/azure/identity-readme).
