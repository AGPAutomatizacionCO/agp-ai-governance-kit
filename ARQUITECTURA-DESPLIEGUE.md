# Arquitectura de despliegue AGP — monolito desplegable

**Norma de IT (2026-10-16).** Aplica a todo desarrollo empresarial que se vaya a desplegar con la Mesa de Requerimientos
(agente de despliegue, worker de ensayo y worker de IT). Los agentes de este kit la usan para guiar, escribir y evaluar.

## Definición

Un desarrollo se entrega como **monolito desplegable**: **un repositorio, una imagen de contenedor, un recurso de Azure**
(una Web App con su plan). Si el desarrollo tiene pantalla y API, **la imagen lleva las dos**: el frontend se compila dentro
de la imagen y la misma API lo sirve desde el mismo origen.

### Nombres equivalentes

Estos términos significan lo mismo y los agentes deben reconocerlos como equivalentes:

| Término | Uso |
|---|---|
| **Monolito desplegable** | Nombre corto en español para la norma. |
| **Single-container deployment** | Nombre técnico en inglés: una sola imagen, un solo contenedor en producción. |
| **App single-service** | Una aplicación = un servicio de Azure (un App Service). |
| **SPA embebida en la app** | El frontend (SPA React/Vite) va compilado dentro de la imagen de la API; no es un recurso aparte. |

No es un monolito en el sentido de «código sin módulos»: el código puede estar organizado en módulos y capas. «Monolito» se
refiere solo a la **unidad de despliegue**.

## Qué NO es (arquitecturas repartidas)

Quedan fuera de la norma, salvo excepción escrita de IT:

- API en una Web App y pantalla en una Static Web App (perfil `react-static` / destino `static-web-app`).
- Varios contenedores en un mismo recurso (nginx + backend + frontend como «sidecars»).
- Una aplicación repartida en varios recursos de Azure, cada uno con su URL, su login y su limpieza.

## Por qué

- Una sola pieza que desplegar, probar y retirar: un health check, un plan, una limpieza.
- Mismo origen: sin CORS ni variable con la dirección de la API.
- Un solo redirect URI de login que registrar en Entra.
- La ruta de despliegue solo sabe desplegar un contenedor: menos permisos y menos fallos.
- Para herramientas internas con decenas de usuarios, la CDN y el escalado global de una Static Web App no aportan.

## Patrón de referencia

1. **Dockerfile en dos etapas** en la raíz: etapa 1 (`node`) hace `npm ci` y `npm run build`; etapa 2 (`python` o `node`) instala la API y copia
   `dist/` a la carpeta que la API sirve (`frontend_dist/`). Bases fijadas por digest, usuario sin privilegios, `HEALTHCHECK`.
2. **La API sirve la pantalla**: archivos estáticos y `index.html` para toda ruta que no empiece por `api/`. Una ruta `api/...` desconocida sigue siendo 404 JSON.
3. **El frontend llama a su propio origen** (URL relativa) cuando se compila para la imagen; en local usa `localhost`.
4. **El login es el estándar de AGP** (`templates/auth-estandar/`) y **lo configura la API** con una ruta pública `GET /api/config` que devuelve solo tenant y cliente de Entra (nunca secretos).
5. **Un solo `.agp/profile.yaml`** `kind: container` (contexto en la raíz, `build.dockerfile: Dockerfile`) y un solo `.agp/runtime.yaml`.
6. Healthcheck público y sin autenticación en la propia API (`/health` o `/api/health`); el puerto del perfil es el que escucha la imagen.

Ejemplo de perfil: `examples/profile-container-monolito.valid.yaml`.

## Cómo la aplica cada agente

| Agente | Qué hace con la norma |
|---|---|
| **Especificación** | Al definir alcance y plan, declara la arquitectura (monolito desplegable) o pide la excepción de IT. No propone dos recursos. |
| **Documental** | Documenta la arquitectura en `specs/007-deployment-notes.md` (`architecture:`) y en la documentación técnica. |
| **Desarrollo** | Implementa el patrón de referencia; no crea un segundo servicio ni un Dockerfile de frontend aparte. |
| **Revisión técnica (TR03 y TR10)** | Verifica que frontend y API compartan imagen y origen; si no, lo reporta como hallazgo (hoy informativo, no bloqueante). |
| **Despliegue** | Reporta en `PreparacionDespliegue` si el Dockerfile compila el frontend y si el perfil es `container`. |

## Excepciones

Se piden a IT por escrito, con el motivo (por ejemplo, una pantalla pública con requisitos de CDN), y se registran en
`ai/decisions/`. Mientras la Mesa no sepa desplegar recursos estáticos, una excepción se despliega a mano por IT.

## Solo frontend (sin API)

Un desarrollo que es solo pantalla estática (perfil `react-static`) es hoy una excepción: la Mesa no crea Static Web Apps. La opción dentro de
la norma es servir el `dist/` desde un contenedor mínimo con un servidor web sin privilegios (un solo recurso). Si el desarrollo va a crecer con una API,
parte desde el principio del patrón de referencia.
