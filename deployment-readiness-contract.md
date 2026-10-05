# Contrato de preparación para despliegue

Este contrato distingue tres decisiones que no deben confundirse:

1. **Evaluación de agentes:** Documental, Pruebas y Revisión Técnica determinan si la evidencia del desarrollo permite revisión humana. No aprueban producción.
2. **Candidato para preflight:** Revisión Técnica informa si el repositorio tiene evidencia suficiente para que la Mesa ejecute verificaciones automáticas del commit exacto. Es una conclusión sobre el candidato, no sobre Azure ni sobre la autorización de despliegue.
3. **Ready to deploy:** lo calcula la Mesa, no un agente, cuando el dictamen de los agentes sigue vigente para el SHA actual, cada gate obligatorio tiene nota >=80 y ningún bloqueante, existe aprobación humana, el perfil está aprobado y el preflight de GitHub/Azure/datos/secretos es satisfactorio. El despliegue conserva su aprobación humana separada.

## Evidencia que aportan los agentes

| Responsable | Verifica en el candidato | No debe afirmar |
| --- | --- | --- |
| Documental | Identidad funcional, área, expediente, `AGENTS.md`, `specs/007-deployment-notes.md`, rollback, `.agp/profile.yaml` y `.agp/governance.yaml` cuando se pide despliegue. | Que el tag del kit o un recurso Azure existen solo porque están escritos en un archivo. |
| Pruebas | Casos y criterios de aceptación, reporte reproducible, prueba de `/health` o equivalente, seguridad básica del contenedor y CI verde para el SHA que se quiere evaluar, con enlace a la corrida. | Que una ejecución antigua o local valida el commit actual; que Easy Auth fue probado localmente. |
| Revisión Técnica | Consistencia entre los dos gates, perfil/código/Dockerfile/workflows, convenciones vigentes, separación de secretos y permisos, digest de imagen cuando ya exista, y pendientes de TR10. | Que la IA aprobó producción o que Azure/RBAC/OIDC/cuota están listos sin consultar la plataforma. |

Un criterio sin acceso a evidencia se marca **no-verificable**, nunca `cumple`. El agente indica el archivo, corrida o configuración exacta que falta, cómo corregirla y cómo demostrar la corrección en el siguiente intento. No convierte errores de la Mesa (migración SQL, worker, permisos de su identidad, límite de entornos de vista previa) en una mala nota del desarrollo: los reporta como `pendientes_plataforma`.

## Dictamen adicional de Revisión Técnica

Cuando `condiciones_activas` incluye `requiere-despliegue`, la salida JSON contiene:

```json
"preparacion_despliegue": {
  "estado": "pendiente",
  "commit_evaluado": "",
  "perfil": "",
  "evidencia_ci": "",
  "pendientes_candidato": ["Falta .agp/governance.yaml con versión y SHA del kit"],
  "pendientes_plataforma": ["El kit todavía no tiene release aprobado"],
  "verificaciones_no_realizadas": ["RBAC/OIDC de Azure no consultados por este agente"]
}
```

`estado` solo admite `candidato_preflight`, `pendiente`, `no_verificable` o `no_aplica`. `candidato_preflight` exige que `pendientes_candidato` esté vacío, que el commit evaluado sea un SHA de 40 caracteres y que la evidencia de CI corresponda a ese SHA. `pendientes_plataforma` no se resuelve por inferencia del agente; la Mesa lo verifica en preflight. Ni `candidato_preflight` ni `puede_avanzar=true` equivalen a `ready_to_deploy`.

## Bloqueos que pertenecen a la Mesa

La Mesa debe fallar cerrada y mostrar una acción concreta si faltan el release/tag inmutable del kit, la migración de su propia base, el vínculo `IDProyecto` ↔ repositorio, CI sobre el SHA actual, aprobación humana, configuración de secretos, permisos OIDC/ACR/RBAC, cuota/capacidad Azure, persistencia de logs, o validación de acceso real a datos cuando aplique. Un test de la Mesa que dependa de otro repositorio privado debe hacerse reproducible; excluirlo del CI es deuda visible, no evidencia de que pasó.

El preflight se repite justo antes de ejecutar. Si cambia el commit, el SHA del kit, el perfil, la aprobación o el destino, la autorización anterior deja de ser suficiente. Un fallo guarda fase, causa y acción requerida; nunca se registra una URL exitosa antes de salud y pruebas de humo.

La tecnología de despliegue productivo debe seguir la Constitución y el Harness vigentes. Una propuesta de cambio de política (por ejemplo, usar GitHub Actions para publicar en producción) no se considera aprobada mientras su ADR no esté formalmente resuelto.
