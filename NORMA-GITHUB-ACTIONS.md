# Norma de GitHub Actions

**Obligatoria** para todo repositorio de la organización `AGPAutomatizacionCO`, para personas y para agentes. Rige desde el 2026-11-17.

**Por qué.** Del 3 al 5 de noviembre de 2026 la organización gastó los 2.000 minutos del mes en tres días. Con el ritmo de hoy (unos 170 PR fusionados por semana), correr todo en los runners de GitHub costaría unos 10.900 minutos al mes, y el presupuesto bloquea Actions en **toda** la organización cuando se agota. Casi todo ese gasto viene de corridas que no aportan: pruebas repetidas en cada push de un PR, jobs que no terminan, artefactos que nadie descarga.

GitHub no puede imponer estas reglas en repositorios privados del plan gratuito (no hay protección de ramas). Las cumplen la plantilla, los agentes y la revisión de IT, y un workflow que no las cumpla se corrige.

## Reglas para los workflows

| # | Regla | Por qué |
|---|---|---|
| 1 | Cada job lleva `timeout-minutes` (30 por defecto; más, solo con la razón escrita en el YAML). | Un job colgado corre hasta 6 horas. |
| 2 | El CI tiene `concurrency` con el grupo `${{ github.workflow }}-${{ github.event.pull_request.number \|\| github.sha }}` y `cancel-in-progress: true`. | En un PR, un push nuevo cancela la corrida vieja. En `main` el grupo es el SHA: **nunca** se cancela la corrida de un commit de `main`, porque la Mesa exige CI verde sobre el commit que se entrega. Un grupo por rama (`github.ref`) cancela commits de `main`: no se usa. |
| 3 | El PR en borrador no corre pruebas: `types: [opened, synchronize, reopened, ready_for_review]` en `pull_request` y `if: ${{ !github.event.pull_request.draft }}` en los jobs que no tienen `needs`. | Se trabaja en borrador sin gastar; las pruebas corren al marcarlo «listo para revisión». |
| 4 | `paths-ignore: ['**/*.md', 'docs/**']` en `pull_request`. **Nunca** en `push` a `main`. | Un cambio de solo documentación no necesita pruebas en el PR; en `main` cada commit necesita su CI (regla 2). |
| 5 | `push` solo a `main`, nunca a todas las ramas. | Las ramas se prueban en su PR; `push` + `pull_request` sin filtro corre todo dos veces. |
| 6 | No construir dos veces lo mismo en una corrida (por ejemplo, un `docker build` de validación y otro igual para publicar). | Es tiempo de máquina repetido. |
| 7 | Pocos jobs que agrupen pasos, en vez de muchos jobs de segundos. | GitHub cobra cada job redondeado al minuto siguiente: en noviembre el redondeo fue el 32 % del tiempo. |
| 8 | Cache de dependencias (`cache: pip` o `cache: npm` en `setup-python` / `setup-node`). | Instalar dependencias es buena parte de cada corrida. |
| 9 | `actions/upload-artifact` con `retention-days: 1` (o lo mínimo que se necesite). | El almacenamiento gratis es de 500 MB para toda la organización. |
| 10 | Tareas programadas (`schedule`) con la menor frecuencia útil; más de una vez por hora, solo con aprobación de IT. | Una tarea cada 15 minutos son unas 2.900 corridas al mes. |
| 11 | `runs-on` solo con las etiquetas que publica IT. Hoy: `agp-corp` (pruebas), `agp-docker` (Docker y despliegues), `agp-mesa-pr` y `agp-mesa-release` (desarrollos de la Mesa). `ubuntu-*` o `windows-*` en un repositorio privado, solo con aprobación de IT. | Los runners de GitHub se cobran por minuto en los repositorios privados. |
| 12 | Un despliegue que dispara GitHub (`push` a `main`, PR cerrado) es **solo** despliegue: no repite las pruebas que ya corrió el CI de ese commit. La excepción es `dev-publish.yml`, que las repite por contrato de la Mesa (`DESPLIEGUE-A-MAIN.md` §5). | Es tiempo repetido. |

Lo que **no** cambia: `ci.yml` sigue corriendo en `push` a `main` (la Mesa lo lee para saber la rama de despliegue y exige su verde sobre el commit que se entrega) y `dev-publish.yml` sigue repitiendo las pruebas antes de construir.

## Bloque estándar del CI

```yaml
on:
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review]
    paths-ignore: ['**/*.md', 'docs/**']
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

## Reglas para las personas y sus agentes

1. **Abre el PR en borrador** mientras trabajas y márcalo «listo para revisión» cuando quieras las pruebas.
2. **Un PR por cambio funcional.** Ni uno por cada ajuste mínimo ni uno gigante con todo el día: el PR gigante es difícil de revisar y de revertir.
3. **Prueba en local antes de empujar.** No empujes commits de uno en uno «para ver si pasa».
4. **No reintentes una corrida fallida sin cambiar nada**, salvo que la falla sea de la infraestructura (runner caído, red).
5. Un workflow nuevo o modificado cumple esta norma desde su primer commit. El agente que lo escriba la aplica sin que se lo pidan.

## Cómo se comprueba

IT audita todos los workflows de la organización (disparadores, `concurrency`, `timeout-minutes`, filtros, artefactos y `runs-on`) y el consumo de Actions por repositorio. Un workflow que no cumpla se corrige con un PR.
