# Historial de cambios

Este historial registra únicamente versiones publicadas o cambios preparados para la siguiente versión. La política está en [RELEASE-POLICY.md](RELEASE-POLICY.md).

## [Sin publicar]

### Preparación

- **Cambio de alcance (incompatible con el prompt de Revisión Técnica 2.1):** la preparación y el mecanismo de despliegue salen de los agentes de evaluación y quedan solo en el Agente de Despliegue. Se retiran de Revisión Técnica el indicador TR10, la condición `requiere-despliegue` y la sección 8.12 de `agent-technical-review.md` (pasa a un puntero); de Documental, los criterios T-FW01 y T-BA03 y las comprobaciones contra `deployment-notes`. Versiones: Revisión Técnica 2.2, Documental 3.2. El plan de corrección por intentos no cambia.
- El RC de prueba declara `agpctl 0.1.0`, contrato `profile.agp/v1` para `python-api` y generación verificable del manifiesto de compatibilidad; el SHA se completa desde el commit publicado.
- Corrección local de rutas y referencias inmutables en `AGENTS.md`.
- Definición inicial de la política de releases y del contrato de compatibilidad.
- Esquemas versionados para gobierno, despliegue v2 y perfiles; el identificador lógico del esquema de acceso a datos ya no apunta a `main`.

> Todavía no existe un tag o release oficial del kit. `v4.0.0-rc.1` es la primera versión candidata propuesta, no una versión publicada.
