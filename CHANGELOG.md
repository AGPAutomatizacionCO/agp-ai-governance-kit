# Historial de cambios

Este historial registra únicamente versiones publicadas o cambios preparados para la siguiente versión. La política está en [RELEASE-POLICY.md](RELEASE-POLICY.md).

## [Sin publicar]

### Preparación

- Agente de despliegue: si el desarrollo usa SQL Server por `pyodbc`, el Dockerfile del perfil debe instalar `msodbcsql18`, `unixodbc` y `libgssapi-krb5-2` juntos; la falta de `libgssapi-krb5-2` es bloqueo (sin ella el driver no carga y toda ruta con SQL responde 503 aunque `/api/health` dé 200). Plantilla verificada en `templates/Dockerfile-odbc-sqlserver.snippet` (caso SOLPED, 27/10/2026).
- Evaluación: usar datos reales ya no es bloqueante. Se retira B03 («datos sensibles reales expuestos») de los bloqueantes automáticos de `prompt-agente-revision-tecnica-evaluacion.md` y `prompt-agente-pruebas-evaluacion.md` deja de invalidar la evidencia por datos reales. Siguen bloqueando, y son obligatorios, la configuración por variables de entorno (`.env.example`, nunca un `.env` real) y la ausencia de secretos escritos en el código (B01 y B02). Cualquier otro hallazgo se reporta como mejora pendiente.
- Nomenclatura de objetos de datos (`NOMENCLATURA-DATOS.md`): esquema por desarrollo `app_<area>_<desarrollo>`, tablas `App_<Área>_<Desarrollo>_<tabla>`, usuario, rol y secretos. El esquema del manifiesto de acceso a datos suma, de forma opcional y retrocompatible, `crear_en_despliegue`, el tipo de cada columna (lista cerrada), `nulable`, `clave_primaria` y `referencia`; las reglas de nombres y tipos solo se exigen cuando una tabla propia lleva `crear_en_despliegue: true`. Ejemplo en `templates/data-access-manifest.crear-tablas.example.json`.
- `agpctl runtime plan|check`: propone y comprueba `.agp/runtime.yaml` a partir de las variables de entorno que usa el desarrollo (solo lectura, sin leer `.env` ni escribir valores secretos).
- Contrato de rutas del perfil explícito: `build.context` y `build.dockerfile` son rutas desde la raíz del repositorio y `az acr build --file` debe ser exactamente `build.dockerfile`. Descripciones en `schemas/profile-v1.schema.json` y regla en el prompt del agente de despliegue (la Mesa lo comprueba contra `dev-publish.yml` antes de publicar).
- Login estándar de AGP: paquete de referencia `templates/auth-estandar/` (pantalla y flujo de la Mesa con el nombre propio del desarrollo, sin secreto de cliente; perfil `python-api`), regla en START-HERE 9.2 y requisito `auth_estandar` en el agente de despliegue. `.agp/entra.yaml` sin `MSAL_CLIENT_SECRET`. La pantalla trae sus propios estilos (`src/styles/login-estandar.css`) para verse igual en cualquier desarrollo.
- Agente de despliegue: MSAL obligatorio para todo desarrollo (`.agp/entra.yaml` con `login: required` implementado y `administradores`), requisitos nuevos `runtime` (`.agp/runtime.yaml` con bases de datos reales) y `contexto_docker` (`.dockerignore` no excluye lo que el Dockerfile copia). Solo aplica a este agente.
- Norma de arquitectura de entrega: monolito desplegable (*single-container deployment*, app single-service, SPA embebida en la app). Documento `ARQUITECTURA-DESPLIEGUE.md`, ejemplo de perfil y reglas en START-HERE, AGENTS.md y los agentes de especificación, documental, desarrollo, revisión técnica y despliegue.
- El RC de prueba declara `agpctl 0.1.0`, contrato `profile.agp/v1` para `python-api` y generación verificable del manifiesto de compatibilidad; el SHA se completa desde el commit publicado.
- Corrección local de rutas y referencias inmutables en `AGENTS.md`.
- Definición inicial de la política de releases y del contrato de compatibilidad.
- Esquemas versionados para gobierno, despliegue v2 y perfiles; el identificador lógico del esquema de acceso a datos ya no apunta a `main`.

> Todavía no existe un tag o release oficial del kit. `v4.0.0-rc.1` es la primera versión candidata propuesta, no una versión publicada.
