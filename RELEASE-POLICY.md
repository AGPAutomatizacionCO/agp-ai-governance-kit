# Política de versiones del AGP AI Governance Kit

**Estado:** propuesta operativa; requiere aprobación humana antes del primer release. El kit se declara borrador en `START-HERE.md` y no tiene tags publicados.

## Identidad y consumo de una versión

- El kit usa SemVer `vMAJOR.MINOR.PATCH` y candidatos `-rc.N`.
- Cada release apunta a un único commit. Un tag publicado no se mueve ni se elimina; una corrección crea otra versión.
- Un proyecto registra versión legible y SHA completo de 40 caracteres. La validación y el despliegue descargan reglas por SHA, no por `main` ni por un tag mutable.
- La Mesa registra commit del proyecto, versión/SHA del kit, versión de `agpctl`, esquema, perfil y artefacto que dieron lugar a una decisión.
- `main` sirve para preparar y revisar cambios, no como referencia normativa en automatizaciones.

## Qué cambia cada número

| Tipo | Cuándo usarlo | Ejemplo |
|---|---|---|
| MAJOR | Regla incompatible, cambio de formato que exige migración o cambio de autoridad/aprobación | `v4.0.0` → `v5.0.0` |
| MINOR | Perfil o capacidad compatible, nueva regla optativa o nueva validación que no invalida proyectos conformes | `v4.0.0` → `v4.1.0` |
| PATCH | Corrección editorial o de herramienta sin cambio del resultado normativo | `v4.0.0` → `v4.0.1` |
| RC | Candidato para pilotos y revisión humana; no se presenta como estable | `v4.0.0-rc.1` |

Una nueva regla obligatoria que pueda bloquear proyectos previamente conformes es incompatible y exige MAJOR, aunque el cambio de código sea pequeño. El PR debe explicar el efecto sobre proyectos existentes.

## Compatibilidad

Cada release adjunta un `compatibility.json` basado en `release/compatibility.template.json`. El manifiesto declara la versión/SHA del kit, las versiones de esquemas, el intervalo de `agpctl` compatible y las versiones de perfiles probadas. Un componente marcado `pending` no se anuncia como compatible. El SHA se completa desde el commit seleccionado al publicar, y el proceso comprueba que el tag resuelva a ese mismo SHA.

Las versiones de perfiles y esquemas evolucionan por separado del kit. La Mesa rechaza una combinación no declarada compatible y ofrece un PR de actualización; nunca migra silenciosamente un proyecto.

## Secuencia de publicación

1. Abrir PR con `CHANGELOG.md`, manifiesto de compatibilidad propuesto, impacto, migración y pruebas.
2. Ejecutar validación de rutas, esquemas, ejemplos y controles automáticos. Revisar cambios normativos con los dueños definidos en `CODEOWNERS` cuando existan.
3. Probar `v4.0.0-rc.1` con al menos un proyecto real y un caso negativo que deba bloquearse.
4. Obtener aprobación de gobierno, Tech Lead y DevOps Owner para la versión estable. Resolver las contradicciones normativas antes de `v4.0.0`.
5. Crear tag protegido y release con `compatibility.json`, checksums, notas de migración y enlaces a resultados. Firmar/atestar el artefacto de release cuando el proceso esté habilitado.
6. Comprobar el SHA publicado, registrar evidencia y abrir PRs de actualización en proyectos consumidores.

## Reversión

Un release publicado no se reescribe. Si resulta defectuoso, marcarlo como retirado en el catálogo, publicar una versión nueva y abrir PRs que devuelvan cada proyecto a un SHA aprobado o lo actualicen al parche. La Mesa conserva el SHA usado en evaluaciones previas.
