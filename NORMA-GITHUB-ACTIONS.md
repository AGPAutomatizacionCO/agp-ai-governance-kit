# Norma de GitHub Actions

**Obligatoria** para todo repositorio de la organización `AGPAutomatizacionCO`, para personas y para agentes. Rige desde el 2026-11-17.

**Por qué.** Del 3 al 5 de noviembre de 2026 la organización gastó los 2.000 minutos del mes. Cuando el presupuesto se agota, Actions se bloquea en **toda** la organización y nadie despliega. Casi todo ese gasto fueron corridas que no aportaban: pruebas repetidas en cada push de un PR y jobs de segundos cobrados como minutos completos.

## Reglas para las personas

1. **Abre el PR en borrador** mientras trabajas. En borrador no corren pruebas.
2. **Todos tus cambios en un solo PR.** Sube todos tus commits al mismo PR y márcalo «listo para revisión» una sola vez, cuando termines.
3. **Prueba en local antes de empujar.** No empujes commits de uno en uno «para ver si pasa».

## Reglas para los workflows

Las trae la plantilla y las aplica el agente que escriba o modifique un workflow, sin que se lo pidan.

| # | Regla | Por qué |
|---|---|---|
| 1 | `timeout-minutes: 30` en cada job. | Un job colgado corre hasta 6 horas. |
| 2 | `concurrency` del bloque de abajo: grupo por PR o por SHA. **Nunca** por rama (`github.ref`). | En un PR, un push nuevo cancela la corrida vieja. En `main` cada commit conserva su corrida, porque la Mesa exige CI verde sobre el commit que se entrega. |
| 3 | El PR en borrador no corre pruebas (`types` e `if` del bloque de abajo). | Las pruebas corren una vez, al marcarlo «listo para revisión». |
| 4 | Pocos jobs: los pasos cortos van juntos en un mismo job. | GitHub cobra cada job redondeado al minuto siguiente: en noviembre el redondeo fue el 32 % del gasto. |
| 5 | Tareas programadas (`schedule`) máximo una vez por hora. | Una tarea cada 15 minutos son unas 2.900 corridas al mes. |

`ci.yml` sigue corriendo en `push` a `main`: la Mesa lo exige para entregar.

## Bloque estándar del CI

```yaml
on:
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review]
    paths-ignore: ['**/*.md', 'docs/**']   # solo en el PR, nunca en push a main
    branches: [main]
  push:
    branches: [main]

concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.sha }}
  cancel-in-progress: true

jobs:
  pruebas:
    if: ${{ !github.event.pull_request.draft }}
    timeout-minutes: 30
    runs-on: [self-hosted, Linux, X64, agp-corp]
    steps:
      - uses: actions/checkout@v4
      # ... pasos ...
```

Un job que ya tenía `if:` combina las dos condiciones: `if: ${{ !github.event.pull_request.draft && (<condición anterior>) }}`.

IT revisa los workflows y el consumo de Actions por repositorio. Lo que no cumpla se corrige con un PR.
