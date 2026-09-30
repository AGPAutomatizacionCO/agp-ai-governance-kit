# `agpctl validate` — primera implementación

Ejecutar desde la raíz del kit con Python y `requirements-release.txt` instalados:

```text
python -m agpctl validate --repo <ruta-al-proyecto> --environment dev --approvals <archivo-confiable.json>
```

El comando devuelve JSON con `valid` e `issues` y código de salida 1 si hay bloqueos. Comprueba tres contratos: `.agp/governance.yaml`, `.agp/profile.yaml` y `.github/agp-deploy.json`; la versión del kit debe resolver al SHA aprobado. Para contenedores comprueba rutas, dependencias Python fijadas o lockfile Node, imagen base por digest, usuario no-root y coherencia de puerto/health check. También exige un archivo Bicep en `infra/`, bloquea referencias mutables y contrasta accesos detectados con aprobaciones vigentes si hay datos reales.

El archivo `--approvals` **debe provenir de la Mesa o de un servicio de gobierno confiable**. Un archivo aportado por el mismo PR del desarrollador no constituye autorización. La integración que obtiene y verifica esa evidencia corresponde a T04.5; hasta entonces, el CLI bloquea accesos detectados si no recibe aprobaciones. El esquema y su validación estructural no reemplazan la aprobación humana.

Los tests locales usan un SHA ficticio y omiten únicamente la consulta de tag mediante la función interna `validate_project(..., verify_tag=False)`; el comando público siempre verifica el tag remoto. No hay release del kit publicado aún, por lo que ningún proyecto real puede pasar esa comprobación hasta cerrar T01.2/T01.3.

## Detección explicable de perfil (T03.2 parcial)

`python -m agpctl detect --repo <proyecto>` es **sólo lectura**. Busca señales de `python-api`, `node-api` y `react-static` en raíz, `backend/`, `api/`, `frontend/` y `web/`; devuelve candidatos, ubicaciones, señales, perfil declarado, recomendación y advertencias. Si encuentra varios componentes (por ejemplo API + React) no recomienda uno: `requiresConfirmation: true`. Un frontend React sin `index.html` sigue contando como componente, pero se advierte que el build puede estar incompleto. No interpreta un `package.json` inválido ni sobrescribe Dockerfiles. La selección persistente, generación por perfil y el contrato multicomponente siguen pendientes; una recomendación no equivale a aprobación ni despliegue.

## Prueba Docker local (no formal)

`local plan` aplica los contratos de perfil/despliegue, dependencias, Dockerfile y acceso a datos; omite exclusivamente la exigencia de release publicado y IaC Azure. La salida marca `localOnly: true` y `governanceVerified: false`. Por eso **no** autoriza CI/CD ni despliegue en Azure.

```text
python -m agpctl local plan --repo <proyecto>
python -m agpctl local up --repo <proyecto> --host-port 18000
python -m agpctl local down --repo <proyecto>
```

`up` requiere Docker Engine/CLI local. Construye la imagen desde el Dockerfile existente, la ejecuta sólo en `127.0.0.1`, aplica `no-new-privileges` y elimina capacidades Linux, exige HTTP 2xx en el health check y guarda evidencia en `.agp/local-runs/` (ignorar en Git). Si falla el health check, detiene el contenedor. `down` detiene y conserva el registro con estado `stopped`. No se entregan secretos ni se accede a Azure o ACR. Actualmente soporta perfiles `container`; un perfil `static` debe tener un flujo distinto y no requiere Docker por defecto.

Para Docker Engine dentro de WSL/Ubuntu sin conceder al usuario el grupo privilegiado `docker`, primero ejecutar `sudo -v` en esa consola y añadir `--docker-sudo` a `local up` y `local down`. La opción invoca únicamente el CLI Docker mediante `sudo -n` (no eleva todo Python); si la autorización `sudo` caduca, falla sin esperar una contraseña oculta. Ejecutar `agpctl` desde la misma Ubuntu, con el kit y el proyecto accesibles por `/mnt/c/...`. El CLI de Windows no puede usar automáticamente un daemon instalado sólo dentro de WSL.
