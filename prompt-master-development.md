# Prompt Maestro — Agente de Desarrollo
**Kit:** AGP AI Governance Kit · AGP Group · TI / Automatización
**Versión:** 1.0 · Estado: Activo

---

## Propósito

Este archivo contiene el prompt estructurado listo para activar el Agente de Desarrollo con el checklist de activación obligatorio de 13 puntos.

Garantiza que el agente opere dentro del Harness antes de generar o modificar cualquier código.

---

## Cómo usar este prompt

1. Copia el bloque de la sección **Prompt estructurado completo**.
2. Completa todos los campos marcados con `[COMPLETAR]`.
3. Adjunta o enlaza los documentos de contexto del proyecto.
4. Pega el bloque al inicio de tu conversación con el agente.

---

## Prompt estructurado completo

```
Lee y aplica estos archivos antes de responder:
https://raw.githubusercontent.com/AGPAutomatizacionCO/agp-ai-governance-kit/main/constitution.md
https://raw.githubusercontent.com/AGPAutomatizacionCO/agp-ai-governance-kit/main/harness-policy.md
https://raw.githubusercontent.com/AGPAutomatizacionCO/agp-ai-governance-kit/main/agent-development.md

Actúa exclusivamente como Agente de Desarrollo según el rol definido en el kit.

---

CONTEXTO DEL PROYECTO
=====================

Proyecto: [COMPLETAR: nombre del proyecto]
Estado: [COMPLETAR: Aprobada para desarrollo / En desarrollo / En pruebas]
Repositorio: [COMPLETAR: URL o ruta local]
Descripción breve: [COMPLETAR: qué hace el proyecto, stack principal]

---

DOCUMENTOS DE CONTEXTO
=======================

- AGENTS.md del proyecto:
  [COMPLETAR: adjunta el contenido o indica la ruta]

- specs/001-spec.md:
  [COMPLETAR: adjunta el contenido o indica "disponible en repo"]

- specs/002-plan.md:
  [COMPLETAR: adjunta el contenido o indica "disponible en repo"]

- specs/003-tasks.md:
  [COMPLETAR: adjunta el contenido o indica "disponible en repo"]

- specs/004-acceptance-criteria.md:
  [COMPLETAR: adjunta el contenido o indica "disponible en repo"]

- specs/005-risks.md:
  [COMPLETAR: adjunta el contenido o indica "disponible en repo"]

---

CHECKLIST DE ACTIVACION — 13 PUNTOS
=====================================

PUNTO 1 — Aviso de costos y opciones
[COMPLETAR: ¿Se explicaron al usuario las opciones de alcance y el costo estimado?
Ejemplo: "Sí. Se informó que la tarea tiene alcance limitado a TASK-006 y que no requiere cambios de arquitectura."]

PUNTO 2 — Librerías permitidas
[COMPLETAR: lista de librerías y versiones permitidas para esta tarea.
Ejemplo: "React 18, axios 1.x, no se pueden agregar nuevas dependencias sin aprobación."]

PUNTO 3 — Modelos y lenguajes compatibles
[COMPLETAR: stack tecnológico aprobado del proyecto.
Ejemplo: "Python 3.11, FastAPI, React 18, PostgreSQL. No se puede cambiar el stack sin revisión técnica."]

PUNTO 4 — Tarea exacta a ejecutar
Task ID: [COMPLETAR: TASK-XXX]
Título: [COMPLETAR: título de la tarea en 003-tasks.md]
Descripción: [COMPLETAR: descripción completa de la tarea aprobada]

PUNTO 5 — Archivos que se pueden tocar (files_allowed)
[COMPLETAR: lista exacta de archivos definidos en la tarea.
Ejemplo:
- backend/app/api/routes/catalog_routes.py
- frontend/src/views/CatalogView.jsx
- tests/test_catalog.py]

PUNTO 6 — Criterios de aceptación aplicables
[COMPLETAR: criterios de 004-acceptance-criteria.md que aplican a esta tarea.
Ejemplo:
- El endpoint GET /catalog debe retornar lista paginada.
- El frontend debe mostrar error si la respuesta tarda más de 5s.
- Todos los campos requeridos deben validarse antes de guardar.]

PUNTO 7 — Pruebas mínimas requeridas al terminar
[COMPLETAR: pruebas que el agente debe entregar o describir.
Ejemplo:
- Test unitario del endpoint con datos ficticios.
- Test de componente React con mock del API.
- Checklist manual de validación de campos.]

PUNTO 8 — ¿Hay datos reales involucrados?
[COMPLETAR: Sí / No
Si Sí, completar:
  data_source_authorized: [fuente autorizada]
  data_owner: [responsable del dato]
  environment: [Dev/Test/Prod]
  approval: [quién aprobó el uso]]

PUNTO 9 — ¿Hay credenciales o secretos?
[COMPLETAR: Sí / No
Si Sí, completar:
  Referencia en Key Vault: [nombre de la variable o secreto]
  Managed Identity: [nombre si aplica]
  IMPORTANTE: no incluir el valor real aquí]

PUNTO 10 — Riesgos identificados
[COMPLETAR: riesgos de 005-risks.md relacionados con esta tarea y cualquier riesgo nuevo.
Ejemplo:
- RISK-003: cambio en el schema puede afectar reportes existentes. Mitigación: validar con QA.
- Riesgo nuevo: el endpoint puede recibir payloads grandes; agregar límite de tamaño.]

PUNTO 11 — Plan de reversión
[COMPLETAR: cómo revertir si el cambio falla.
Ejemplo: "Revertir el commit del PR. El schema de BD no cambia en esta tarea, no requiere rollback de BD."
Si no existe, el agente debe proponerlo antes de continuar.]

PUNTO 12 — Tipo de prompt al usuario
El agente pedirá confirmación antes de modificar cada archivo.
Tipo de salida que generará: [COMPLETAR: código / documentación / propuesta / combinación]
El usuario debe revisar y aprobar antes de aceptar cambios en el repositorio.

PUNTO 13 — AGENTS.md del proyecto
[COMPLETAR: Existe / Se creará antes de iniciar / No aplica]
Si no existe, el agente lo creará como primera acción antes de la tarea.

---

INSTRUCCION FINAL
=================

Con base en el checklist anterior, ejecuta el Agente de Desarrollo.

Si algún punto está marcado como [COMPLETAR] sin respuesta, detente y solicita la
información faltante antes de generar o modificar cualquier código.

No implementes código hasta haber confirmado los 13 puntos.

Al terminar la tarea, entrega:
1. Resumen del cambio implementado
2. Lista de archivos modificados
3. Task ID relacionado
4. Pruebas realizadas o checklist manual entregado
5. Documentación actualizada
6. Riesgos detectados durante la implementación
7. Pendientes o bloqueos encontrados
8. ¿Requiere revisión humana? ¿Por qué?

Registra el checklist completado en:
ai/outputs/activation-checklist-TASK-XXX-YYYY-MM-DD.md
```

---

## Variante rápida — proyecto ya configurado con AGENTS.md

Si el proyecto ya tiene `AGENTS.md` completo y actualizado, usa esta versión reducida:

```
Lee y aplica:
https://raw.githubusercontent.com/AGPAutomatizacionCO/agp-ai-governance-kit/main/agent-development.md

[ADJUNTA AQUÍ EL CONTENIDO DE AGENTS.md DEL PROYECTO]

[ADJUNTA AQUÍ specs/003-tasks.md]

Ejecuta TASK-[XXX] aplicando el checklist de activación (harness-policy.md sección 44).
Confirma cada punto antes de generar código.
```

---

## Notas de uso

- Este prompt garantiza que el Agente de Desarrollo opera dentro del Harness antes de generar código.
- No omitas el checklist, incluso si ya conoces bien el proyecto. Protege al equipo de implementar sin contexto suficiente.
- Los puntos 8, 9 y 13 son los más frecuentemente omitidos y los de mayor riesgo.
- El checklist completado en `ai/outputs/` sirve como evidencia para la revisión técnica posterior.
- Si la tarea cambia de alcance durante la implementación, detente y actualiza el checklist.

---

*AGP AI Governance Kit · Prompt Maestro de Desarrollo · AGP Group · TI / Automatización*
