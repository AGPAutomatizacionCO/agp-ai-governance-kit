# Historial de cambios

Este historial registra únicamente versiones publicadas o cambios preparados para la siguiente versión. La política está en [RELEASE-POLICY.md](RELEASE-POLICY.md).

## [Sin publicar]

### Preparación

- El RC de prueba declara `agpctl 0.1.0`, contrato `profile.agp/v1` para `python-api` y generación verificable del manifiesto de compatibilidad; el SHA se completa desde el commit publicado.
- Corrección local de rutas y referencias inmutables en `AGENTS.md`.
- Definición inicial de la política de releases y del contrato de compatibilidad.
- Esquemas versionados para gobierno, despliegue v2 y perfiles; el identificador lógico del esquema de acceso a datos ya no apunta a `main`.
- Agente de despliegue: la extracción usa la referencia inmutable del kit cuando el proyecto la declara; entrega un único JSON parseable con 16 campos; distingue datos observados de nombres de Azure decididos por la Mesa; y deja la persistencia del manifiesto de datos al desarrollador mediante un cambio revisado. Requiere un release posterior; no altera `v4.0.0-rc.1`.
- Se define un modo separado de preparación para el Agente de Despliegue, propietario exclusivo de la validación de artefactos y CI/CD por perfil. No modifica las calificaciones Documental, Pruebas o Revisión Técnica; aún requiere release e integración en la Mesa.

> `v4.0.0-rc.1` ya está publicado como prerelease. Los cambios de esta sección no forman parte de ese tag inmutable.
