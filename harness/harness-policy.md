# Harness Engineering Policy para Desarrollo de Soluciones Digitales Empresariales

## 1. Propósito

Este documento define los controles operativos que permiten cumplir la Constitución de Uso de IA para Desarrollo de Soluciones Digitales Empresariales.

La Constitución establece las reglas superiores.
El Harness Engineering establece cómo esas reglas se aplican, controlan, validan y auditan dentro de cada desarrollo.

El objetivo de este Harness es asegurar que todo proyecto digital asistido por IA tenga límites claros, controles de seguridad, revisión humana, trazabilidad documental, gestión de riesgos y evidencia suficiente para su desarrollo, despliegue, consumo, monitoreo, soporte, redeploy, suspensión o retiro.

---

## 2. Principio operativo

Ningún agente de IA, desarrollador, automatización, pipeline, flujo o solución digital debe operar fuera del alcance aprobado.

Todo desarrollo debe cumplir tres condiciones mínimas:

```text
1. Constitución aplicable.
2. Harness aplicable.
3. Expediente técnico actualizado.
```

Si falta alguno de estos tres elementos, la solución no debe avanzar a desarrollo formal, pruebas, despliegue ni producción.

---

## 3. Qué es Harness Engineering en este contexto

Harness Engineering es el conjunto de controles, reglas, límites, matrices, checklists y validaciones que gobiernan cómo trabajan la IA, los agentes, los desarrolladores y las herramientas dentro de un proyecto.

Para la empresa, Harness Engineering se materializa como:

* Reglas para agentes de IA.
* Reglas de acceso.
* Reglas de secretos.
* Reglas de datos.
* Reglas de bases de datos.
* Reglas de Power Platform.
* Reglas de SAP e integraciones críticas.
* Reglas de repositorio.
* Reglas de documentación.
* Reglas de desarrollo.
* Reglas de despliegue.
* Reglas de consumo.
* Reglas de monitoreo.
* Matrices de aprobación.
* Checklists de validación.
* Bloqueos ante riesgos.
* Evidencias obligatorias.
* Revisión humana.

---

## 4. Relación entre Constitución, Harness y Spec

La relación entre los tres elementos es obligatoria:

```text
Constitución
= Define qué se permite, qué se prohíbe y qué requiere aprobación.

Harness
= Define cómo se controla, bloquea, valida y audita el cumplimiento.

Spec / Expediente técnico
= Define cómo se aplica en un proyecto específico.
```

Ejemplo:

```text
Constitución:
La IA no puede aprobar producción.

Harness:
El pipeline debe exigir aprobación manual de IT antes de desplegar a producción.

Spec:
El proyecto debe documentar en deployment-notes.md quién aprueba producción, qué ambiente se usa, qué checklist aplica y cuál es el plan de rollback.
```

Otro ejemplo:

```text
Constitución:
No se deben usar secretos reales.

Harness:
Si se detecta una cadena de conexión, token o API key, se bloquea el uso, se registra el hallazgo y se exige rotación.

Spec:
El proyecto debe indicar en plan.md cómo gestionará secretos y en acceptance-criteria.md que no se aceptará código con secretos expuestos.
```

---

## 5. Controles mínimos por proyecto

Todo proyecto digital empresarial debe tener, como mínimo:

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

/ai/
  prompts/
  outputs/
  reviews/
  risks/
  decisions/
  change-requests/
```

Si el proyecto no requiere código, deberá existir una estructura equivalente en el sistema documental aprobado.

---

## 6. Regla general sobre generación de código

La generación o modificación de código no está prohibida de forma absoluta.

Solo está permitida cuando se cumplan simultáneamente estas condiciones:

1. El proyecto se encuentra en estado **Aprobada para desarrollo**, **En desarrollo** o **En pruebas**.
2. Existe expediente técnico mínimo actualizado.
3. Existen tareas aprobadas en `003-tasks.md`.
4. El agente tiene rol explícito de **Agente desarrollador**.
5. El trabajo se limita al alcance aprobado.
6. No se usan secretos reales.
7. No se usan datos reales no autorizados.
8. No se modifica producción.
9. No se alteran permisos, accesos o integraciones críticas sin aprobación humana.
10. Todo cambio queda documentado.

Ningún agente diferente al **Agente desarrollador** puede generar o modificar código productivo.

Los agentes documental, de especificación, revisión técnica, pruebas, soporte y consulta pueden generar ejemplos conceptuales, pseudocódigo o recomendaciones técnicas, siempre que estén claramente marcados como referencia y no sean tratados como implementación aprobada.

---

## 7. Estados permitidos del proyecto

Los agentes y desarrolladores solo pueden actuar según el estado del proyecto.

Estados recomendados:

```text
Solicitada
En evaluación
Aprobada para análisis
En generación de expediente técnico
Expediente técnico generado
Pendiente de revisión humana
Aprobada para desarrollo
En desarrollo
En pruebas
Aprobada para despliegue
En producción
En monitoreo
Suspendida
Retirada
Reemplazada
Riesgo crítico
```

---

## 8. Reglas de estado

### 8.1 Solicitada

Permitido:

* Registrar necesidad.
* Hacer preguntas.
* Identificar información faltante.
* Clasificar preliminarmente la solicitud.
* Identificar posibles áreas responsables.
* Identificar si podría requerir Power Platform, desarrollo personalizado, integración, reporte o agente de IA.

No permitido:

* Generar código.
* Crear repositorio productivo.
* Crear Power App productiva.
* Crear conexiones reales.
* Crear permisos.
* Crear integraciones reales.
* Acceder a datos reales.
* Definir arquitectura final.
* Iniciar desarrollo.

Motivo:

En este estado todavía no existe aprobación para análisis técnico ni expediente mínimo. La IA solo puede ayudar a entender, ordenar y registrar la necesidad.

---

### 8.2 En evaluación

Permitido:

* Analizar viabilidad inicial.
* Revisar información disponible.
* Identificar riesgos preliminares.
* Identificar datos involucrados.
* Identificar usuarios potenciales.
* Identificar sistemas relacionados.
* Recomendar información faltante.

No permitido:

* Generar código productivo.
* Crear componentes productivos.
* Conectarse a fuentes reales.
* Crear permisos.
* Desplegar componentes.
* Modificar datos.

Motivo:

Este estado permite análisis, pero todavía no autoriza construcción ni acceso operativo.

---

### 8.3 Aprobada para análisis

Permitido:

* Crear spec inicial.
* Crear plan preliminar.
* Analizar riesgos.
* Evaluar Power Platform, desarrollo personalizado o híbrido.
* Proponer arquitectura preliminar.
* Identificar datos, fuentes, usuarios y permisos requeridos.
* Crear preguntas de aclaración.
* Identificar requerimientos de seguridad.
* Identificar controles Harness aplicables.

No permitido:

* Desarrollar funcionalidad productiva.
* Generar código implementable como solución final.
* Acceder a datos reales sin autorización.
* Crear integraciones reales.
* Crear Power Apps productivas.
* Crear flujos productivos.
* Crear permisos.
* Desplegar componentes.
* Modificar bases de datos reales.

Motivo:

En este estado la IA puede ayudar a estructurar el expediente técnico, pero todavía no debe construir la solución. El resultado esperado es documentación, análisis y preparación para revisión humana.

---

### 8.4 En generación de expediente técnico

Permitido:

* Crear o completar `001-spec.md`.
* Crear o completar `002-plan.md`.
* Crear o completar `003-tasks.md`.
* Crear criterios de aceptación.
* Crear análisis de riesgos.
* Crear documento de revisión humana.
* Crear notas preliminares de despliegue.
* Crear notas preliminares de monitoreo.
* Identificar supuestos.
* Identificar información faltante.

No permitido:

* Generar código productivo.
* Implementar tareas.
* Crear conexiones reales.
* Crear permisos.
* Ejecutar scripts.
* Crear componentes productivos.
* Desplegar.

Motivo:

El objetivo es construir el expediente técnico antes de iniciar el desarrollo.

---

### 8.5 Expediente técnico generado

Permitido:

* Revisar documentación.
* Ajustar spec.
* Revisar riesgos.
* Preparar revisión humana.
* Completar tareas.
* Definir criterios de aceptación.
* Identificar bloqueos.
* Preparar matriz de decisiones pendientes.

No permitido:

* Iniciar desarrollo sin aprobación.
* Generar código productivo.
* Cambiar alcance sin registrar solicitud de cambio.
* Crear integraciones.
* Crear permisos.
* Desplegar componentes.
* Modificar datos reales.

Motivo:

El expediente ya existe, pero aún debe ser revisado y aprobado antes de permitir implementación.

---

### 8.6 Pendiente de revisión humana

Permitido:

* Preparar resumen para revisión.
* Identificar puntos críticos.
* Responder preguntas sobre el expediente.
* Ajustar documentación solicitada por revisores.
* Registrar observaciones humanas.
* Registrar aprobaciones o rechazos.

No permitido:

* Generar código productivo.
* Avanzar a desarrollo sin aprobación.
* Desplegar.
* Crear permisos.
* Ejecutar integraciones.
* Cambiar arquitectura sin revisión.

Motivo:

Este estado existe para asegurar que el expediente no sea aceptado automáticamente por haber sido generado por IA.

---

### 8.7 Aprobada para desarrollo

Permitido:

* Implementar tareas aprobadas.
* Generar código.
* Modificar archivos dentro del alcance.
* Crear pruebas.
* Refactorizar código existente.
* Actualizar documentación.
* Prototipar en ambiente Dev.
* Crear componentes Power Platform en ambiente Dev, si aplica y está aprobado.
* Preparar Pull Requests.
* Registrar decisiones técnicas.
* Registrar riesgos nuevos.

No permitido:

* Desplegar producción.
* Cambiar arquitectura aprobada sin revisión.
* Usar secretos reales.
* Conectarse a sistemas críticos sin autorización.
* Crear permisos.
* Crear integraciones críticas sin aprobación.
* Modificar datos reales sin autorización.
* Ampliar alcance sin solicitud de cambio.

Condición especial:

Solo el **Agente desarrollador** puede generar o modificar código en este estado. Los demás agentes mantienen sus funciones documentales, de revisión, consulta, soporte o especificación.

---

### 8.8 En desarrollo

Permitido:

* Continuar implementación de tareas aprobadas.
* Crear pruebas.
* Actualizar documentación.
* Registrar decisiones.
* Registrar riesgos.
* Solicitar revisión ante bloqueos.
* Preparar cambios para Pull Request.
* Ajustar código según revisión.
* Actualizar `009-change-log.md`.

No permitido:

* Trabajar fuera del alcance aprobado.
* Ignorar el expediente técnico.
* Omitir actualización documental.
* Usar secretos reales.
* Modificar producción.
* Cambiar permisos.
* Ejecutar cambios destructivos sin aprobación.
* Cambiar integraciones críticas sin revisión.
* Alterar datos reales sin autorización.

---

### 8.9 En pruebas

Permitido:

* Ejecutar pruebas.
* Corregir defectos.
* Validar criterios de aceptación.
* Revisar riesgos.
* Preparar despliegue.
* Actualizar documentación.
* Generar evidencias de validación.
* Revisar permisos.
* Validar manejo de errores.
* Validar monitoreo.
* Validar rollback o reversión, si aplica.

No permitido:

* Saltar directamente a producción.
* Ocultar errores.
* Cambiar permisos sin aprobación.
* Ampliar alcance sin solicitud de cambio.
* Usar datos reales no autorizados.
* Desactivar monitoreo o controles.
* Modificar arquitectura sin revisión.
* Aprobar producción automáticamente.

---

### 8.10 Aprobada para despliegue

Permitido:

* Ejecutar pipeline controlado.
* Desplegar en ambiente autorizado.
* Validar monitoreo.
* Ejecutar checklist preproducción.
* Preparar evidencia de aprobación.
* Preparar comunicación de salida.
* Verificar plan de rollback.
* Verificar responsables de soporte.

No permitido:

* Desplegar producción sin aprobación humana.
* Usar pipelines personales.
* Usar secretos manuales no controlados.
* Cambiar variables críticas sin revisión.
* Saltarse pruebas.
* Saltarse validación funcional o técnica.
* Cambiar alcance durante el despliegue.

---

### 8.11 En producción

Permitido:

* Monitorear.
* Soportar.
* Registrar incidentes.
* Crear solicitudes de cambio.
* Ejecutar mantenimiento autorizado.
* Revisar logs.
* Documentar hallazgos.
* Proponer mejoras.
* Revisar accesos.
* Revisar uso.
* Revisar cumplimiento de SLA.

No permitido:

* Modificar directamente sin control.
* Cambiar datos productivos sin aprobación.
* Desactivar monitoreo.
* Cambiar roles sin autorización.
* Crear cambios funcionales sin solicitud.
* Redeplegar sin proceso autorizado.
* Usar secretos no controlados.
* Cambiar integraciones críticas sin revisión.

---

### 8.12 En monitoreo

Permitido:

* Revisar métricas de uso.
* Revisar errores.
* Revisar accesos.
* Revisar logs.
* Identificar mejoras.
* Identificar soluciones sin uso.
* Identificar riesgos.
* Crear recomendaciones.
* Crear solicitudes de cambio.
* Preparar revisión periódica.

No permitido:

* Modificar producción sin proceso de cambio.
* Cambiar roles sin aprobación.
* Apagar servicios sin autorización.
* Eliminar logs.
* Cerrar riesgos sin revisión.

---

### 8.13 Suspendida

Permitido:

* Documentar motivo de suspensión.
* Mantener evidencia.
* Revisar accesos.
* Revocar accesos no necesarios.
* Detener integraciones autorizadas para suspensión.
* Evaluar redeploy o retiro.
* Informar a usuarios.
* Registrar estado en catálogo.

No permitido:

* Reutilizar credenciales sin revisión.
* Mantener integraciones activas sin justificación.
* Dejar usuarios con acceso innecesario.
* Borrar documentación.
* Eliminar trazabilidad.

---

### 8.14 Retirada

Permitido:

* Documentar motivo de retiro.
* Archivar documentación.
* Revocar accesos.
* Rotar o eliminar secretos.
* Apagar recursos autorizados.
* Actualizar catálogo.
* Registrar solución reemplazo, si aplica.
* Definir política de retención de datos.

No permitido:

* Mantener servicios activos sin justificación.
* Mantener secretos vigentes.
* Mantener integraciones activas.
* Perder evidencia histórica.
* Eliminar información sin política de retención.

---

### 8.15 Reemplazada

Permitido:

* Documentar solución reemplazo.
* Migrar documentación.
* Validar migración de datos.
* Revocar accesos a la solución anterior.
* Actualizar catálogo.
* Archivar versión anterior.
* Registrar dependencias.

No permitido:

* Mantener dos soluciones activas con la misma función sin justificación.
* Mantener integraciones duplicadas sin control.
* Dejar usuarios consumiendo solución obsoleta.
* Perder trazabilidad del reemplazo.

---

### 8.16 Riesgo crítico

Permitido:

* Detener actividades.
* Escalar a IT, seguridad o responsable correspondiente.
* Documentar hallazgo.
* Proponer mitigación.
* Revisar impacto.
* Suspender temporalmente si aplica.
* Activar plan de contingencia si está definido.

No permitido:

* Continuar desarrollo como si no hubiera riesgo.
* Desplegar.
* Ampliar alcance.
* Manipular datos.
* Ocultar hallazgo.
* Cerrar riesgo sin validación humana.

---

## 9. Control de agentes de IA

Todo agente debe tener una ficha de rol antes de actuar.

### Ficha mínima de agente

```text
agent_name:
agent_type:
purpose:
allowed_actions:
forbidden_actions:
required_context:
allowed_sources:
forbidden_sources:
output_location:
human_review_required_when:
risk_escalation_rules:
```

### Tipos de agentes reconocidos

La empresa reconoce estos agentes:
* Agente documental.
* Agente de especificación.
* Agente de revisión técnica.
* Agente de desarrollo.
* Agente de pruebas.
* Agente de soporte.
* Agente de consulta.

---

## 9.1 Agente documental

Función:

Mantener vivo el expediente documental del proyecto.

Puede:

* Crear borradores de documentación.
* Actualizar changelog.
* Resumir decisiones.
* Registrar cambios funcionales.
* Detectar inconsistencias.
* Crear guías para usuarios.
* Crear guías para desarrolladores.
* Preparar documentación para revisión humana.
* Identificar documentación desactualizada.
* Proponer mejoras documentales.

No puede:

* Aprobar documentos como definitivos.
* Cambiar arquitectura sin revisión.
* Generar permisos.
* Modificar producción.
* Ocultar riesgos.
* Usar secretos.
* Generar código productivo.

Evidencia requerida:

```text
/ai/outputs/
/ai/decisions/
/ai/reviews/
/ai/change-requests/
```

---

## 9.2 Agente de especificación

Función:

Convertir solicitudes, necesidades o cambios en expediente técnico.

Puede:

* Crear `001-spec.md`.
* Crear `002-plan.md`.
* Crear `003-tasks.md`.
* Crear criterios de aceptación.
* Crear análisis de riesgos.
* Formular preguntas de aclaración.
* Comparar opciones tecnológicas.
* Proponer arquitectura preliminar.
* Proponer estructura documental.

No puede:

* Aprobar desarrollo.
* Aprobar arquitectura final.
* Aprobar producción.
* Crear código productivo antes de revisión.
* Dar por cerrado un requisito sin validación humana.
* Crear permisos.
* Ejecutar integraciones.

Condición de uso:

Solo puede trabajar sobre proyectos registrados o solicitudes formalmente recibidas.

---

## 9.3 Agente desarrollador

Función:

Implementar tareas aprobadas.

Puede:

* Generar código.
* Modificar archivos dentro del alcance aprobado.
* Crear pruebas.
* Refactorizar.
* Corregir errores asociados a una tarea.
* Documentar cambios.
* Sugerir mejoras técnicas.
* Actualizar documentación técnica relacionada con el cambio.
* Preparar cambios para revisión.
* Proponer pruebas adicionales.

No puede:

* Trabajar sobre tareas no aprobadas.
* Cambiar arquitectura aprobada sin revisión.
* Crear permisos.
* Usar secretos.
* Ejecutar cambios destructivos.
* Conectarse a producción.
* Desplegar producción.
* Modificar SAP o sistemas núcleo.
* Crear conexiones reales sin aprobación.
* Aprobar su propio código.
* Ampliar alcance sin solicitud de cambio.
* Ignorar riesgos documentados.

Regla obligatoria:

El agente desarrollador solo puede trabajar contra tareas definidas y aprobadas en `003-tasks.md`.

Si detecta que una tarea requiere información no documentada, debe detenerse y reportar el bloqueo.

---

## 9.4 Agente revisor

Función:

Validar coherencia entre Constitución, Harness, Spec, código, configuración y documentación.

Puede:

* Revisar cumplimiento.
* Detectar secretos.
* Revisar riesgos.
* Detectar cambios fuera de alcance.
* Comparar código contra tareas.
* Revisar documentación faltante.
* Revisar criterios de aceptación.
* Identificar deuda técnica.
* Identificar inconsistencias.
* Identificar riesgos nuevos.
* Proponer correcciones.

No puede:

* Aprobar producción.
* Reemplazar revisión humana.
* Cambiar permisos.
* Modificar código sin autorización.
* Cerrar riesgos sin validación.
* Cambiar estados del proyecto sin autorización.

Salida esperada:

```text
/ai/reviews/review-YYYY-MM-DD.md
```

---

## 9.5 Agente de soporte

Función:

Apoyar operación, mesa de ayuda, usuarios y diagnóstico de incidentes.

Puede:

* Consultar documentación aprobada.
* Explicar errores frecuentes.
* Sugerir pasos de diagnóstico.
* Crear guías de usuario.
* Crear artículos de conocimiento.
* Escalar incidentes.
* Identificar riesgos operativos.
* Orientar sobre canales de soporte.
* Ayudar a clasificar incidentes.

No puede:

* Modificar código.
* Cambiar datos.
* Reiniciar servicios productivos sin autorización.
* Otorgar accesos.
* Ejecutar acciones críticas.
* Cambiar configuraciones productivas.
* Crear permisos.
* Ocultar incidentes.

---

## 9.6 Agente de consulta

Función:

Responder preguntas sobre proyectos, arquitectura, decisiones, riesgos, tareas, cambios y estado.

Puede:

* Leer Constitución.
* Leer Harness.
* Leer specs.
* Leer documentación aprobada.
* Resumir estado de proyecto.
* Explicar decisiones.
* Identificar información faltante.
* Explicar arquitectura.
* Explicar riesgos.
* Explicar tareas pendientes.

No puede:

* Crear código.
* Modificar documentación sin autorización.
* Aprobar decisiones.
* Cambiar estados del proyecto.
* Acceder a información fuera del alcance.
* Otorgar permisos.
* Modificar producción.

---

## 10. Paquete de contexto gobernado para agentes

Todo agente debe recibir un paquete de contexto controlado.

### Paquete mínimo

```text
1. Rol del agente.
2. Constitución vigente.
3. Harness aplicable.
4. Ficha del proyecto.
5. Specs del proyecto.
6. Riesgos del proyecto.
7. Decisiones registradas.
8. Estado del proyecto.
9. Restricciones de acceso.
```

### Orden de lectura obligatorio

El agente debe usar este orden:

```text
1. Constitution.
2. Harness.
3. Project card.
4. Spec.
5. Plan.
6. Tasks.
7. Risks.
8. Human review.
9. Deployment notes.
10. Monitoring notes.
11. Decisions.
12. Change log.
```

Si falta un documento crítico, el agente debe reportarlo y limitar su acción.

---

## 11. Control de secretos

### Regla

Ningún secreto debe aparecer en:

* Código.
* Documentación.
* Prompts.
* Respuestas de IA.
* README.
* Specs.
* Logs.
* Capturas.
* Archivos `.env` versionados.
* Archivos de ejemplo con valores reales.

### Se consideran secretos

* Passwords.
* Tokens.
* API keys.
* Client secrets.
* Certificados privados.
* Cadenas de conexión.
* Account keys.
* Credenciales SAP.
* Credenciales SQL.
* Credenciales de Power BI.
* Secretos Entra ID.
* Archivos `.env` reales.

### Control requerido

Si se detecta un secreto:

```text
1. Detener uso.
2. Reportar posible exposición.
3. Registrar hallazgo en /ai/risks/.
4. Recomendar rotación.
5. Recomendar eliminación del código o documentación.
6. Revisar historial Git si aplica.
7. Reemplazar por Key Vault, Managed Identity o variable controlada.
8. Solicitar validación IT.
```

### Criterio de bloqueo

Un proyecto no puede avanzar a merge, prueba, despliegue o producción si contiene secretos reales expuestos.

---

## 12. Control de datos

### Regla

La IA y los agentes deben operar preferiblemente con:

* Datos ficticios.
* Datos sintéticos.
* Datos anonimizados.
* Ambientes de prueba.
* Esquemas vacíos.
* Fuentes autorizadas.

### Bloqueo obligatorio

El agente debe detenerse si:

* La fuente de datos no está documentada.
* La base no pertenece al alcance aprobado.
* Se solicita consultar datos reales sin autorización.
* Se detectan datos sensibles no autorizados.
* La acción puede afectar datos productivos.
* Se requiere modificación masiva sin respaldo.
* No existe dueño del dato.
* No existe definición de sensibilidad.

### Evidencia requerida

El proyecto debe documentar:

```text
data_sources:
data_sensitivity:
data_owner:
allowed_operations:
forbidden_operations:
test_data_strategy:
```

---

## 13. Control de bases de datos

La IA puede proponer:

* Modelos.
* Tablas.
* Vistas.
* Scripts.
* Migraciones.
* Diccionarios de datos.
* Consultas.
* Validaciones.

Pero no puede ejecutar cambios en bases reales sin autorización.

### Cambios que requieren aprobación

* Crear tablas productivas.
* Alterar tablas productivas.
* Eliminar tablas.
* Eliminar columnas.
* Truncar tablas.
* Modificar datos masivos.
* Cambiar llaves.
* Cambiar relaciones.
* Crear usuarios.
* Cambiar permisos.
* Crear procedimientos en producción.
* Ejecutar migraciones irreversibles.

### Requisito mínimo

Toda propuesta de cambio en base de datos debe incluir:

```text
objetivo:
ambiente:
script propuesto:
impacto:
riesgo:
respaldo requerido:
plan de reversión:
aprobador:
```

---

## 14. Control de Power Platform

La IA puede apoyar soluciones Power Platform en ambientes controlados.

Puede:

* Proponer modelo de datos.
* Proponer pantallas.
* Proponer flujos.
* Proponer fórmulas.
* Documentar Power Apps.
* Documentar Power Automate.
* Documentar Power BI.
* Crear guías de usuario.
* Identificar limitaciones.
* Recomendar Dataverse, SharePoint o SQL según el caso.
* Apoyar prototipos en ambiente Dev si el proyecto está aprobado.

No puede:

* Aprobar Power Apps.
* Publicar en producción sin revisión.
* Crear conexiones críticas sin aprobación.
* Usar conectores premium o sensibles sin validación.
* Crear flujos que modifiquen datos críticos sin autorización.
* Integrarse con SAP sin capa de control.
* Asignar permisos a usuarios.
* Crear soluciones productivas sin expediente técnico.

### Regla de ambiente

Toda solución Power Platform debe diferenciar, cuando aplique:

```text
Dev
Test
Prod
```

### Criterios de revisión

Antes de producción, se debe validar:

* Fuente de datos.
* Dueño funcional.
* Dueño técnico.
* Accesos.
* Conectores.
* Flujos.
* Riesgos.
* Licenciamiento, si aplica.
* Monitoreo.
* Soporte.
* Documentación.
* Criterios de aceptación.

---

## 15. Control de SAP y sistemas núcleo

Toda integración con SAP, sistemas financieros, nómina, clientes, operación central o sistemas núcleo requiere revisión IT.

### Regla

No se permiten integraciones directas sin capa de control.

Toda propuesta debe contemplar:

* Capa intermedia.
* Validación de datos.
* Seguridad.
* Manejo de errores.
* Trazabilidad.
* Auditoría.
* Estados.
* Reintentos.
* Registro de respuestas.
* Ambientes de prueba.
* Aprobación humana.
* Monitoreo.
* Plan de reversión.

### Bloqueo automático

El agente debe detenerse si una solicitud implica:

* Escritura directa en SAP.
* Modificación de datos núcleo.
* Uso de credenciales SAP.
* Integración sin responsable IT.
* Ausencia de ambiente de prueba.
* Falta de trazabilidad.
* Falta de capa intermedia.
* Falta de plan de reversión.

---

## 16. Control de documentación

Todo proyecto debe tener documentación viva.

### Documentos obligatorios mínimos

```text
README.md
/specs/001-spec.md
/specs/002-plan.md
/specs/003-tasks.md
/specs/004-acceptance-criteria.md
/specs/005-risks.md
/specs/006-human-review.md
/specs/007-deployment-notes.md
/specs/008-monitoring-notes.md
/specs/009-change-log.md
```

### Regla

No se debe aceptar un cambio funcional o técnico relevante si no actualiza la documentación correspondiente.

### Bloqueo documental

Debe bloquearse o devolverse un cambio si:

* No hay tarea asociada.
* No hay criterio de aceptación.
* No hay registro de riesgo.
* No se actualizó changelog.
* No se documentó impacto.
* No se registró decisión relevante.
* No se registró revisión humana cuando aplica.

---

## 17. Control de desarrollo

### Regla

El desarrollo debe avanzar por tareas aprobadas.

Flujo:

```text
Task aprobada
→ Implementación
→ Pruebas
→ Documentación
→ Revisión
→ Merge
```

### El agente desarrollador debe detenerse si:

* La tarea no existe.
* La tarea no está aprobada.
* La tarea contradice la Constitución.
* La tarea contradice el Harness.
* La tarea requiere datos no autorizados.
* La tarea requiere secretos.
* La tarea cambia arquitectura.
* La tarea afecta producción.
* La tarea afecta SAP.
* La tarea implica permisos.
* Falta información crítica.
* El estado del proyecto no permite desarrollo.

---

## 18. Control de repositorio

Todo proyecto con código debe usar repositorio corporativo.

### Reglas

* No usar repositorios personales para soluciones corporativas.
* No subir secretos.
* No subir `.env` reales.
* No subir datos sensibles.
* No subir dumps reales.
* No mezclar código productivo con pruebas improvisadas.
* No dejar archivos temporales críticos.
* No omitir documentación.
* No hacer cambios grandes sin explicación.

### Pull Request mínimo

Todo PR debe indicar:

```text
task_id:
descripción:
archivos afectados:
riesgos:
pruebas realizadas:
documentación actualizada:
impacto en datos:
impacto en seguridad:
requiere aprobación:
```

---

## 19. Control de despliegue

### Regla

La IA no puede aprobar despliegue ni producción.

### Flujo recomendado

```text
GitHub
→ Pull Request
→ Revisión
→ Pruebas
→ Build
→ Deploy Dev
→ Validación técnica
→ Deploy Test
→ Validación funcional
→ Aprobación humana
→ Deploy Prod
```

### Requisitos antes de producción

* Checklist preproducción.
* Pruebas ejecutadas.
* Riesgos revisados.
* Documentación actualizada.
* Secretos controlados.
* Variables revisadas.
* Accesos definidos.
* Monitoreo activo.
* Plan de rollback.
* Responsable de soporte.
* Aprobación funcional.
* Aprobación técnica.
* Aprobación IT.

### Bloqueo

No se debe desplegar producción si falta cualquiera de los controles anteriores.

---

## 20. Control de consumo

Toda solución debe definir cómo será consumida.

Debe documentar:

```text
usuarios:
roles:
canales:
datos visibles:
acciones permitidas:
acciones prohibidas:
soporte:
logs:
SLA:
```

Canales posibles:

* Navegador.
* Power Apps.
* Power BI.
* API.
* Teams.
* SharePoint.
* Aplicación móvil.
* Agente de IA.
* Flujo automatizado.

### Regla

No se debe liberar una solución a usuarios sin definir roles, accesos, soporte y trazabilidad de consumo.

---

## 21. Control de monitoreo y auditoría

Toda solución en producción debe tener monitoreo proporcional a su criticidad.

Debe definirse:

* Herramienta de monitoreo.
* Ubicación de logs.
* Métricas técnicas.
* Métricas de uso.
* Métricas de seguridad.
* Alertas.
* Responsable de revisión.
* SLA level.
* Frecuencia de revisión.

Herramientas posibles:

* Azure Monitor.
* Log Analytics.
* Application Insights.
* Microsoft Entra logs.
* Azure Activity Logs.
* Key Vault logs.
* Power Platform CoE.
* Power BI audit logs.
* Microsoft Sentinel, si aplica.

### Bloqueo

No se debe pasar a producción una solución crítica sin monitoreo definido.

---

## 22. Control de cambios funcionales

Ningún cambio funcional debe ir directo a código.

Flujo obligatorio:

```text
Solicitud de cambio
→ Registro en /ai/change-requests/
→ Análisis de impacto
→ Actualización de spec
→ Actualización de plan, si aplica
→ Actualización de tasks
→ Actualización de risks
→ Revisión humana
→ Desarrollo
→ Pruebas
→ Changelog
```

Cada cambio debe documentar:

```text
change_id:
fecha:
solicitante:
descripción:
motivo:
impacto funcional:
impacto técnico:
impacto en datos:
impacto en seguridad:
impacto en despliegue:
riesgos:
decisión:
aprobador:
estado:
```

---

## 23. Control de revisión normativa

La IA debe revisar si Constitución, Harness y Spec son coherentes con el proyecto.

Puede proponer mejoras cuando detecte:

* Reglas ambiguas.
* Controles imprácticos.
* Controles faltantes.
* Riesgos no cubiertos.
* Nuevas necesidades del negocio.
* Nuevos tipos de solución.
* Cambios en tecnología.
* Problemas repetidos en proyectos.
* Fricción excesiva sin valor.

No puede aprobar cambios normativos.

### Flujo de mejora normativa

```text
Hallazgo
→ Propuesta de mejora
→ Registro en /ai/decisions/ o /ai/risks/
→ Revisión IT
→ Aprobación humana
→ Actualización de Constitución, Harness o plantillas
→ Comunicación al equipo
```

### Criterio

Toda mejora debe hacer el modelo más práctico sin sacrificar:

* Seguridad.
* Integridad.
* Trazabilidad.
* Auditabilidad.
* Control humano.
* Protección de datos.

---

## 24. Control de soporte

El soporte debe operar desde documentación aprobada.

El agente de soporte puede ayudar a:

* Diagnosticar errores.
* Guiar usuarios.
* Explicar mensajes.
* Consultar documentación.
* Escalar incidentes.
* Crear artículos de conocimiento.

No puede:

* Cambiar datos.
* Cambiar permisos.
* Modificar producción.
* Reiniciar servicios críticos sin autorización.
* Ejecutar scripts.
* Saltarse mesa de ayuda o IT.

Todo incidente relevante debe registrar:

```text
incident_id:
fecha:
usuario:
solución:
descripción:
impacto:
acción sugerida:
acción ejecutada:
responsable:
estado:
```

---

## 25. Control de ciclo de vida

Toda solución debe poder apagarse, suspenderse, redeplegarse o retirarse.

Debe documentar:

```text
shutdown_allowed:
shutdown_reason:
shutdown_approver:
shutdown_process:
redeploy_allowed:
redeploy_source:
redeploy_process:
rollback_plan:
retirement_status:
retirement_date:
replacement_solution:
data_retention_policy:
access_revocation_status:
secrets_revocation_status:
final_review_owner:
```

### Regla

No deben existir soluciones activas sin dueño, sin documentación, sin monitoreo o sin revisión periódica.

---

## 26. Evidencia mínima por fase

### Antes de desarrollo

* Registro de solución.
* Spec inicial.
* Plan preliminar.
* Riesgos.
* Owner funcional.
* Owner técnico.
* Responsable IT.
* Datos identificados.
* Estado aprobado.

### Durante desarrollo

* Tasks actualizadas.
* Prompts relevantes.
* Salidas IA importantes.
* Cambios documentados.
* Riesgos actualizados.
* Pruebas.
* Changelog.

### Antes de despliegue

* Checklist.
* Pruebas.
* Revisión técnica.
* Revisión funcional.
* Revisión de seguridad.
* Plan de rollback.
* Monitoreo.
* Aprobación humana.

### En producción

* Logs.
* Soporte.
* Métricas de uso.
* Métricas de error.
* Accesos.
* Revisión periódica.
* Incidentes.
* Solicitudes de cambio.

### Retiro

* Motivo.
* Aprobación.
* Revocación de accesos.
* Rotación o eliminación de secretos.
* Archivo de documentación.
* Actualización del catálogo.
* Evidencia de cierre.

---

## 27. Criterios de bloqueo general

Un proyecto debe detenerse si:

* No tiene propietario funcional.
* No tiene responsable técnico.
* No tiene responsable IT.
* No tiene fuente de datos autorizada.
* Usa secretos reales.
* Usa datos reales sin autorización.
* Afecta SAP sin capa de control.
* Cambia producción sin aprobación.
* No tiene documentación mínima.
* No tiene riesgos registrados.
* No tiene plan de rollback para cambios críticos.
* No tiene monitoreo para producción.
* El agente trabaja fuera de su rol.
* La IA inventa información faltante.
* Hay contradicción con la Constitución.
* El estado del proyecto no permite la acción solicitada.
* Se intenta generar código sin tarea aprobada.
* Un agente distinto al Agente desarrollador intenta modificar código productivo.

---

## 28. Cierre

Este Harness no busca frenar el desarrollo. Busca que la empresa pueda desarrollar más soluciones digitales sin perder control, seguridad, trazabilidad, continuidad ni capacidad de auditoría.

El Harness convierte la Constitución en controles reales y convierte el desarrollo asistido por IA en un proceso gobernado, documentado y mantenible.

Toda solución debe poder responder:

```text
Qué se construyó.
Por qué se construyó.
Quién lo pidió.
Quién lo aprobó.
Qué datos usa.
Qué permisos tiene.
Qué riesgos existen.
Qué agente intervino.
Qué decisiones se tomaron.
Qué versión está activa.
Cómo se desarrolla.
Cómo se despliega.
Cómo se consume.
Cómo se monitorea.
Cómo se apaga.
Cómo se retira.
```
