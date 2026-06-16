# AGP AI Governance Kit

Kit de gobierno para el uso de inteligencia artificial en el desarrollo, documentación, pruebas, revisión, despliegue, soporte y mantenimiento de soluciones digitales empresariales.

Este repositorio define reglas, controles, plantillas, agentes y lineamientos para que las soluciones digitales asistidas por IA se desarrollen de forma segura, trazable, mantenible, auditable y alineada con las necesidades del negocio.

---

## 1. Propósito del repositorio

El propósito de este kit es establecer un marco de trabajo para que la IA apoye el desarrollo de soluciones digitales empresariales sin reemplazar la revisión humana, la aprobación de IT, la gobernanza de datos, la seguridad corporativa ni la responsabilidad de los equipos encargados.

Este repositorio busca que las soluciones digitales de la empresa sean:

* Accesibles para usuarios, aplicaciones y agentes autorizados.
* Disponibles según su criticidad.
* Integrales entre procesos, datos y sistemas.
* Auditables desde el diseño hasta el retiro.
* Seguras, trazables y mantenibles.
* Documentadas durante todo su ciclo de vida.

---

## 2. Principio rector

La IA apoya el desarrollo, pero no gobierna, aprueba ni decide por la empresa.

Toda decisión crítica de negocio, datos, seguridad, arquitectura, permisos, integraciones, despliegue o producción debe ser revisada y aprobada por responsables humanos autorizados.

---

## 3. Componentes principales del kit

Este kit se organiza alrededor de tres capas principales:

```text
Constitución
= Define las reglas superiores que no se deben romper.

Harness Engineering
= Define los controles prácticos para cumplir la Constitución.

Spec Kit / Expediente técnico
= Define cómo se documenta, planea, desarrolla, prueba y revisa cada proyecto concreto.
```

La relación entre estas capas es:

```text
Constitución
→ Harness
→ Spec
→ Desarrollo
→ Pruebas
→ Revisión técnica
→ Revisión humana
→ Despliegue controlado
→ Monitoreo y soporte
```

---

## 4. Estructura del repositorio

```text
agp-ai-governance-kit/
│
├── README.md
│
├── constitution/
│   └── constitution.md
│
├── harness/
│   └── harness-policy.md
│
├── agents/
│   ├── agent-context-package.md
│   ├── agent-documental.md
│   ├── agent-specification.md
│   ├── agent-technical-review.md
│   ├── agent-development.md
│   ├── agent-testing.md
│   ├── agent-support.md
│   └── agent-consultation.md
│
└── prompts/
    └── prompt-master-development.md
```

---

## 5. Constitución

La Constitución define las reglas superiores para el uso de IA en soluciones digitales empresariales.

Responde a la pregunta:

```text
¿Qué reglas no se pueden romper?
```

Ejemplos:

* La IA no puede aprobar producción.
* La IA no puede conceder permisos.
* La IA no puede usar secretos reales.
* La IA no puede manipular datos reales sin autorización.
* La IA no puede conectarse directamente a sistemas críticos sin control.
* Toda solución debe tener trazabilidad, documentación, pruebas y revisión humana.

Documento principal:

```text
constitution/constitution.md
```

---

## 6. Harness Engineering

El Harness convierte la Constitución en controles operativos.

Responde a la pregunta:

```text
¿Cómo hacemos cumplir la Constitución en la práctica?
```

Ejemplos:

* Si se detecta un secreto, se bloquea el uso y se exige rotación.
* Si falta una tarea aprobada, el Agente de Desarrollo no puede generar código.
* Si faltan pruebas, el cambio no debe avanzar a revisión técnica.
* Si falta revisión humana, no se permite producción.
* Si una integración toca SAP, debe existir capa de control e intervención de IT.

Documento principal:

```text
harness/harness-policy.md
```

---

## 7. Modelo oficial de agentes

Este kit reconoce siete tipos de agentes de IA:

```text
1. Agente documental.
2. Agente de especificación.
3. Agente de revisión técnica.
4. Agente de desarrollo.
5. Agente de pruebas.
6. Agente de soporte.
7. Agente de consulta.
```

La separación de agentes evita que una misma IA asuma responsabilidades incompatibles, como especificar, construir, probar, revisar y aprobar al mismo tiempo.

---

## 8. Agente documental

Mantiene vivo el expediente técnico, funcional y operativo del proyecto.

Puede:

* Crear documentación.
* Actualizar changelog.
* Registrar decisiones.
* Registrar riesgos.
* Preparar guías.
* Detectar inconsistencias.

No puede:

* Aprobar documentos como definitivos.
* Generar código productivo.
* Conceder permisos.
* Modificar producción.

Documento:

```text
agents/agent-documental.md
```

---

## 9. Agente de especificación

Convierte necesidades, ideas o solicitudes en expediente técnico.

Puede crear:

* `spec.md`
* `plan.md`
* `tasks.md`
* `acceptance-criteria.md`
* `risks.md`
* `human-review.md`

No puede:

* Aprobar desarrollo.
* Aprobar arquitectura final.
* Crear código productivo.
* Aprobar producción.

Documento:

```text
agents/agent-specification.md
```

---

## 10. Agente de revisión técnica

Valida que los cambios cumplan Constitución, Harness, Spec, arquitectura, seguridad, alcance, documentación y evidencia.

Puede revisar:

* Código.
* Arquitectura.
* Datos.
* Secretos.
* Permisos.
* Riesgos.
* Documentación.
* Evidencia de pruebas.

No puede:

* Aprobar producción.
* Reemplazar revisión humana.
* Ejecutar pruebas como responsabilidad principal.
* Modificar código sin autorización.

Documento:

```text
agents/agent-technical-review.md
```

---

## 11. Agente de desarrollo

Implementa tareas aprobadas.

Puede:

* Generar código.
* Modificar archivos dentro del alcance.
* Refactorizar.
* Corregir errores.
* Crear pruebas básicas asociadas al cambio.
* Actualizar documentación técnica.

No puede:

* Trabajar sobre tareas no aprobadas.
* Usar secretos reales.
* Conectarse a producción.
* Crear permisos.
* Modificar SAP o sistemas núcleo.
* Aprobar su propio código.

Documento:

```text
agents/agent-development.md
```

---

## 12. Agente de pruebas

Diseña, ejecuta o documenta pruebas y evidencia.

Puede crear:

* Matriz de pruebas.
* Casos de prueba.
* Informe de pruebas.
* Registro de defectos.
* Evidencia segura.
* Validaciones de permisos, datos, errores, APIs, frontend, backend, Power Platform o Power BI.

No puede:

* Aprobar producción.
* Inventar resultados.
* Usar datos reales no autorizados.
* Ejecutar pruebas destructivas sin aprobación.
* Modificar datos reales.

Documento:

```text
agents/agent-testing.md
```

---

## 13. Agente de soporte

Apoya operación, usuarios, diagnóstico inicial, incidentes y escalamiento.

Puede:

* Consultar documentación aprobada.
* Explicar errores.
* Crear guías de usuario.
* Clasificar incidentes.
* Recomendar escalamiento.
* Crear artículos de conocimiento.

No puede:

* Modificar código.
* Cambiar datos.
* Otorgar accesos.
* Reiniciar servicios productivos sin autorización.
* Cerrar incidentes críticos sin revisión humana.

Documento:

```text
agents/agent-support.md
```

---

## 14. Agente de consulta

Responde preguntas desde documentación autorizada.

Puede:

* Explicar una solución.
* Resumir estado.
* Explicar decisiones.
* Consultar riesgos.
* Orientar a nuevos usuarios o desarrolladores.
* Identificar información faltante.

No puede:

* Modificar código.
* Modificar documentación sin autorización.
* Aprobar decisiones.
* Cambiar estados.
* Conceder permisos.

Documento:

```text
agents/agent-consultation.md
```

---

## 15. Agent Context Package

El paquete de contexto define cómo se entrega información a cada agente.

Incluye:

* Rol del agente.
* Constitución vigente.
* Harness aplicable.
* Estado del proyecto.
* Expediente técnico.
* Riesgos.
* Decisiones.
* Restricciones.
* Fuentes autorizadas.
* Evidencias.

Documento:

```text
agents/agent-context-package.md
```

---

## 16. Flujo recomendado de uso

El flujo recomendado para una nueva solución digital empresarial es:

```text
1. Registrar necesidad.
2. Activar Agente de Especificación.
3. Crear expediente técnico inicial.
4. Realizar revisión humana.
5. Aprobar desarrollo.
6. Activar Agente de Desarrollo.
7. Implementar tareas aprobadas.
8. Activar Agente de Pruebas.
9. Generar evidencia de pruebas.
10. Activar Agente de Revisión Técnica.
11. Resolver hallazgos.
12. Realizar aprobación humana / IT.
13. Desplegar de forma controlada.
14. Activar monitoreo y soporte.
15. Mantener documentación viva.
```

---

## 17. Expediente técnico mínimo por proyecto

Todo proyecto debe contar, como mínimo, con:

```text
/specs/
  001-spec.md
  002-plan.md
  003-tasks.md
  004-acceptance-criteria.md
  005-risks.md
  006-human-review.md
  007-deployment-notes.md
  008-monitoring-notes.md
  009-change-log.md
```

Cuando aplique, también debe contar con:

```text
/tests/
  test-matrix.md
  test-report-YYYY-MM-DD.md
  defects/
```

Y con evidencia de IA en:

```text
/ai/
  prompts/
  outputs/
  reviews/
  risks/
  decisions/
  change-requests/
```

---

## 18. Uso de IA permitido

La IA puede apoyar en:

* Análisis de requerimientos.
* Documentación.
* Generación de código bajo tareas aprobadas.
* Refactorización.
* Diseño de pruebas.
* Revisión técnica.
* Identificación de riesgos.
* Comparación tecnológica.
* Generación de guías.
* Soporte y consulta.
* Propuestas de mejora normativa.

Pero no puede aprobar decisiones críticas ni operar fuera de su rol.

---

## 19. Restricciones críticas

La IA no debe:

* Aprobar producción.
* Crear permisos.
* Usar secretos reales.
* Solicitar credenciales.
* Manipular datos reales sin autorización.
* Conectarse a producción sin control.
* Modificar SAP o sistemas núcleo sin aprobación.
* Ejecutar cambios destructivos sin respaldo y revisión.
* Saltarse revisión humana.
* Ocultar riesgos.
* Inventar información faltante.
* Declarar pruebas exitosas sin evidencia.

---

## 20. Uso de Power Platform

La IA puede apoyar en soluciones Power Platform cuando se trate de:

* Formularios.
* Captura de datos.
* Aprobaciones.
* Procesos internos.
* Automatizaciones.
* Apps departamentales.
* Integración con Microsoft 365.
* Visualización en Power BI.

Debe advertir riesgos cuando existan:

* Datos sensibles.
* Alto volumen.
* Lógica compleja.
* Conectores premium.
* Integraciones críticas.
* SAP.
* Falta de separación entre ambientes.
* Gobernanza insuficiente.

---

## 21. Uso de desarrollo personalizado

La IA puede apoyar desarrollo personalizado cuando se requiera:

* Backend propio.
* Frontend avanzado.
* APIs.
* Seguridad avanzada.
* Auditoría.
* Integraciones complejas.
* Alto volumen de datos.
* Control de versiones.
* Despliegue controlado.
* Monitoreo técnico.

El desarrollo personalizado debe mantener separación entre capas, trazabilidad, pruebas y documentación.

---

## 22. Integraciones críticas

Las integraciones con SAP, sistemas núcleo, financieros, legales, comerciales o de operación central requieren:

* Participación de IT.
* Capa intermedia.
* Validación de datos.
* Manejo de errores.
* Auditoría.
* Trazabilidad.
* Monitoreo.
* Plan de reversión.
* Pruebas controladas.
* Revisión humana.

La IA puede proponer arquitecturas, pero no aprobar ni ejecutar integraciones críticas.

---

## 23. Criterio de preparación

Una solución no se considera lista porque “funciona”.

Una solución solo se considera lista cuando:

* Cumple la necesidad de negocio.
* Tiene expediente técnico.
* Tiene propietario funcional.
* Tiene responsable técnico.
* Tiene responsable IT.
* Tiene datos autorizados.
* Tiene controles de seguridad.
* Tiene criterios de aceptación.
* Tiene pruebas documentadas.
* Tiene revisión técnica.
* Tiene revisión humana.
* Tiene trazabilidad.
* Tiene monitoreo.
* Tiene soporte.
* Tiene plan de reversión.
* Cumple Constitución y Harness.

---

## 24. Cómo usar este repositorio

Para aplicar este kit a un proyecto:

1. Leer `constitution/constitution.md`.
2. Leer `harness/harness-policy.md`.
3. Identificar el estado del proyecto.
4. Identificar qué agente aplica.
5. Consultar `agents/agent-context-package.md`.
6. Crear o actualizar el expediente técnico.
7. Registrar intervención de IA en `ai/`.
8. Ejecutar desarrollo, pruebas y revisión según corresponda.
9. No avanzar a producción sin revisión humana.

---

## 25. Estado del kit

Este kit se encuentra en evolución.

La IA puede proponer mejoras a la Constitución, Harness, agentes, prompts o plantillas cuando detecte que una regla es ambigua, insuficiente o poco práctica.

Toda mejora normativa debe ser revisada y aprobada por personal humano autorizado.

---

## 26. Regla final

Este repositorio no busca frenar el desarrollo.

Busca permitir que la empresa desarrolle más soluciones digitales con IA sin perder seguridad, trazabilidad, documentación, control humano, integridad de información ni capacidad de auditoría.

La IA acelera.
La Constitución limita.
El Harness controla.
El Spec ordena.
Los agentes ejecutan dentro de su rol.
Las pruebas generan evidencia.
La revisión técnica valida cumplimiento.
La revisión humana decide.
