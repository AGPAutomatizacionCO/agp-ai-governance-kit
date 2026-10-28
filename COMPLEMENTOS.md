# Complementos externos de un desarrollo

Algunos desarrollos tienen una parte que **no corre en Azure**: un robot que maneja SAP GUI en el equipo de una persona, un conector que vive en la red de la planta. Esa parte es un **complemento**. La Mesa no lo despliega, pero lo registra, lo documenta y vigila que esté conectado.

No es el *worker de despliegue* de la Mesa (el Container Apps Job que publica imágenes): ese es plataforma. Un complemento es del desarrollo.

## Declaración: `.agp/complementos.yaml`

Solo nombres y descripciones, nunca valores. Esquema: `schemas/complementos-v1.schema.json`.

```yaml
apiVersion: complementos.agp/v1
complementos:
  - id: worker-sap
    tipo: ejecutor-escritorio
    nombre: SOLPED Worker Windows
    descripcion: Crea en SAP las SOLPED que llegan del portal, una a la vez, y devuelve el número SAP.
    carpeta: SolPed_worker_windows
    operador: persona.operadora@agpglass.com     # quien lo abre y lo mantiene encendido
    respaldo: otra.persona@agpglass.com          # quien lo reemplaza
    dondeCorre: Equipo Windows de Compras Nacionales con SAP Logon (QAS)
    requisitos:
      - SAP GUI con scripting habilitado y una sesión iniciada
      - Python 3.12 con las dependencias de SolPed_worker_windows/requirements.txt
    conexiones:
      - con: rabbitmq
        como: consume solicitudes y liberaciones, publica resultados
        colas: [solped.solicitudes, solped.liberaciones, solped.resultados]
      - con: portal
        como: descarga las cotizaciones de cada solicitud con la clave compartida
    secretos:                                     # los mismos nombres de .agp/runtime.yaml (norma <desarrollo>-<dato>)
      - { variable: SOLPED_RABBIT_URL, secreto: co-supply-chain-solped-smart-suite-solped-rabbit-url }
      - { variable: SOLPED_WORKER_CLAVE, secreto: co-supply-chain-solped-smart-suite-solped-worker-clave }
    configuracion: SolPed_worker_windows/README.md  # donde se explica cómo configurarlo (URL del portal, Rabbit, clave)
```

## Reglas

1. **Sin credenciales de bases de datos.** Un complemento recibe solo lo que necesita para hablar con el desarrollo (URL del broker, clave compartida). Quien lo opera las pide a quien las administra; no se escriben en el repositorio.
2. **Los secretos siguen la norma `<desarrollo>-<dato>`** (`NOMENCLATURA-DATOS.md`) y se cargan en el vault de desarrollos desde la Mesa.
3. **Todo complemento tiene operador y respaldo.** Si corre en el equipo de una sola persona, un solo equipo apagado detiene el flujo.
4. **Se configura por su propia pantalla o archivo documentado.** La configuración (URL del portal, URL del broker, clave) debe estar explicada en el README indicado en `configuracion`. Usar los valores por defecto de las pruebas en local (por ejemplo `http://127.0.0.1:8080`) es el error más común al pasar a Azure.
5. **Un complemento no se despliega con la Mesa.** El documento de aprobación lo lista como «requiere acción manual del operador» tras cada despliegue que cambie el contrato con el complemento (colas, rutas del portal, claves).

## Qué hace la Mesa con él

- Lo muestra en la ficha del desarrollo como «Complemento externo (fuera de Azure)», con su operador, dónde corre y qué necesita.
- Valida el archivo contra el esquema y que cada secreto declarado también esté en `.agp/runtime.yaml` con el prefijo del desarrollo.
- Lo incluye en el documento del plan que IT aprueba.
- Cuando el broker está registrado, consulta en solo lectura cuántos consumidores tiene cada cola declarada para mostrar si el complemento está conectado (sin leer ni consumir mensajes).
