# Historial de cambios

Este historial registra únicamente versiones publicadas o cambios preparados para la siguiente versión. La política está en [RELEASE-POLICY.md](RELEASE-POLICY.md).

## [Sin publicar]

### Preparación

- Login estándar de AGP: paquete de referencia `templates/auth-estandar/` (pantalla y flujo de la Mesa con el nombre propio del desarrollo, sin secreto de cliente; perfil `python-api`), regla en START-HERE 9.2 y requisito `auth_estandar` en el agente de despliegue. `.agp/entra.yaml` sin `MSAL_CLIENT_SECRET`.
- Agente de despliegue: MSAL obligatorio para todo desarrollo (`.agp/entra.yaml` con `login: required` implementado y `administradores`), requisitos nuevos `runtime` (`.agp/runtime.yaml` con bases de datos reales) y `contexto_docker` (`.dockerignore` no excluye lo que el Dockerfile copia). Solo aplica a este agente.
- Norma de arquitectura de entrega: monolito desplegable (*single-container deployment*, app single-service, SPA embebida en la app). Documento `ARQUITECTURA-DESPLIEGUE.md`, ejemplo de perfil y reglas en START-HERE, AGENTS.md y los agentes de especificación, documental, desarrollo, revisión técnica y despliegue.
- El RC de prueba declara `agpctl 0.1.0`, contrato `profile.agp/v1` para `python-api` y generación verificable del manifiesto de compatibilidad; el SHA se completa desde el commit publicado.
- Corrección local de rutas y referencias inmutables en `AGENTS.md`.
- Definición inicial de la política de releases y del contrato de compatibilidad.
- Esquemas versionados para gobierno, despliegue v2 y perfiles; el identificador lógico del esquema de acceso a datos ya no apunta a `main`.

> Todavía no existe un tag o release oficial del kit. `v4.0.0-rc.1` es la primera versión candidata propuesta, no una versión publicada.
