# Despliegue a `main` y despliegue continuo (CD): quién decide y cómo

Norma para todo desarrollo que se despliega con la Mesa de Requerimientos. Cierra una pregunta: **«cuando alguien fusiona a `main`, ¿quién decide si eso se publica y cómo?»** Lo decide **IT, por desarrollo, desde la Mesa**. El equipo de desarrollo, personas y agentes, prepara y fusiona cambios; no despliega. Complementa `ARQUITECTURA-DESPLIEGUE.md` (qué se entrega), `PERMISOS-Y-SECRETOS-DEL-WORKER.md` (qué se concede) y `ACCESO-Y-ROLES-DEL-DESARROLLO.md` (quién entra).

## 1. Principio

- **IT gestiona el cómo.** La publicación de `main` de cada desarrollo la gobierna una **política de CD** que solo IT fija, en la pestaña **Datos técnicos** de la Mesa. Al fijarla IT aprueba de antemano las publicaciones «solo código» que ocurran dentro de ella; queda quién la aprobó, cuándo y el evento `cd_politica_cambiada` en la bitácora.
- **El equipo de desarrollo no despliega, no edita la política y no aprueba permisos.** Un merge a `main` se publica o no según esa política, no según quien lo fusionó.
- **El CD solo publica la imagen.** Nunca concede nada. Lo que toca permisos o recursos pasa por la aprobación completa de IT.

## 2. Los tres modos

| Modo | Qué hace |
|---|---|
| **Apagado** (por defecto) | No se publica nada solo. IT publica con «Publicar ahora» cuando lo pide. |
| **Automático** | Cada push a `main` que solo cambie código se construye y se despliega solo. |
| **Limitado** | Igual que automático, con un tope de N publicaciones automáticas por día (1 a 20, día de Colombia). Pasado el tope, el commit queda sin publicar hasta el próximo push o «Publicar ahora». |

«Publicar ahora» no cuenta para el tope. Una publicación automática que falla **sí** gasta cupo, porque ya consumió recursos.

## 3. Qué publica el CD y qué nunca publica solo

El CD construye la imagen, la publica, actualiza la Web App y comprueba la salud. **No** rehace identidades, roles, Entra, permisos de datos, secretos ni variables de GitHub.

Si el commit toca alguno de estos archivos de contrato, el CD **no publica nada, ni siquiera el código de ese commit**, y deja un aviso «pendiente de IT»:

- `.agp/entra.yaml`
- `.agp/runtime.yaml`
- `.agp/profile.yaml`
- `ai/outputs/data-access-manifest.json`

La razón: el código y el contrato suelen ir juntos. Publicar la imagen sin aplicar las variables o los permisos nuevos dejaría al desarrollo roto. IT lo resuelve con **«Automatizar despliegue»** (aprobación completa del plan).

Tampoco publica solo si el plan cambió en algo más que el commit (acceso, permisos de datos, SKU, nombres), si el plan tiene bloqueos, si el desarrollo aún no tiene un despliegue oficial exitoso, si ya hay un despliegue en curso o si se alcanzó el tope. Ante la duda, no publica (falla cerrado).

## 4. Lo que ve el responsable

El responsable y quienes comparten el desarrollo ven, en el paso **Despliegue** de su ruta, un contador de solo lectura con el logo de GitHub:

- la política vigente: apagado, automático o limitado a X por día;
- cuántas publicaciones automáticas van hoy y cuántas quedan;
- al llegar al tope, un aviso que dice cuándo se reinicia el cupo (00:00, hora de Colombia) y que IT puede publicar con «Publicar ahora»;
- el resultado del último push y, si se omitió, el motivo;
- el aviso «pendiente de IT» cuando el último cambio tocó el contrato, con los archivos.

No ve el correo de quien aprobó la política ni identificadores internos. Cambiar la política sigue siendo solo de IT. Detalle técnico en `specs/019-cd-por-desarrollo.md` de la Mesa.

## 5. Requisitos de cada desarrollo para activar el CD

1. Un **despliegue oficial exitoso previo** (es la base de la comparación).
2. `.github/workflows/dev-publish.yml` según el contrato de la Mesa: solo `workflow_dispatch` con `run_id` y `expected_sha`, que repite las pruebas antes de construir la imagen. Es la red de seguridad: un commit que rompe las pruebas no se publica.
3. `.github/agp-deploy.json`.
4. Los archivos de contrato sin cambios entre commits (si cambian, ese commit va por aprobación completa).

**Recomendado:** `main` protegido con PR y CI obligatorios, porque con CD automático cualquier push a `main` llega a Azure. Si el plan de GitHub no permite proteger la rama (por ejemplo, repositorio privado en plan gratuito), usar el modo **Limitado** y no Automático.

## 6. Reglas para personas y agentes del equipo de desarrollo

1. **No despliegas ni configuras el CD.** Preparas el cambio y lo fusionas por el flujo del repositorio.
2. **Asume que un merge a `main` puede publicarse solo.** Si el desarrollo está en modo automático o limitado, fusionar es publicar. No fusiones lo que no estés dispuesto a ver en producción.
3. **Si un cambio toca el contrato, dilo en el PR** (qué variables, tablas o permisos cambian y por qué) y avisa a IT: no se publicará solo y necesita la aprobación completa.
4. **No mezcles sin avisar** un cambio de contrato con código que depende de él. Si el contrato se queda esperando a IT, el código tampoco sale.
5. **No reintentes con commits vacíos** cuando el contador muestre tope alcanzado o «pendiente de IT»: no cambia nada. Espera el reinicio del cupo o pide a IT «Publicar ahora».
6. Registra el cambio en el historial del desarrollo con quién lo autorizó, como cualquier otro.

## 7. Operación (IT)

- **Webhook de la organización** con los eventos `push` y `repository`, URL `…/api/proyectos/webhooks/github` y el secreto de `GITHUB_WEBHOOK_SECRET`. Sin firma válida la Mesa responde 401 y no hace nada.
- **Always On de la Mesa: recomendado.** GitHub espera 10 segundos la respuesta del webhook. Con Always On apagado, el primer push tras un rato sin uso puede agotar ese plazo y perderse. La Mesa responde de inmediato y evalúa en un hilo, pero un reinicio justo entonces también pierde la evaluación. GitHub permite **reenviar** una entrega desde el panel de webhooks.
- La Mesa corre hoy con una sola instancia; el candado de aprobación es por archivos.
- **Cómo activarlo en un desarrollo nuevo:** probar primero con «Publicar ahora»; después el modo **Limitado con tope 1**; solo entonces decidir si Automático.

## 8. Fuente de verdad

`specs/016-publicar-main-redespliegue.md` y `specs/019-cd-por-desarrollo.md` de la Mesa, y `backend/src/helpers/redespliegue.py` (`ARCHIVOS_DE_CONTRATO`). Si esta norma y el código de la Mesa difieren, manda el código y se corrige esta norma.
