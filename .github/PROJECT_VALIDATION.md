# Validación reutilizable de proyectos (preview MA-03)

Este workflow valida el **repositorio llamador** con una versión inmutable del kit. No aprovisiona Azure, no despliega y no convierte un SHA de PR en release aprobado. El check actual cubre los manifiestos y reglas de `agpctl validate` y secretos con Gitleaks. La auditoría de dependencias/SAST por perfil y los rulesets obligatorios siguen pendientes para cerrar MA-03.

## Consumo desde un proyecto

Crear `.github/workflows/agp-validation.yml` en el proyecto cuando exista un release aprobado del kit. Sustituir ambas apariciones de `<SHA_COMPLETO_DEL_RELEASE>` por el mismo SHA de 40 caracteres del tag protegido; registrar también ese tag y SHA en `.agp/governance.yaml`. No usar `main`, `latest` ni un SHA abreviado.

```yaml
name: agp-validation
on:
  pull_request:
  push:
    branches: [main]
permissions:
  contents: read
jobs:
  governance:
    uses: AGPAutomatizacionCO/agp-ai-governance-kit/.github/workflows/project-validation.yml@<SHA_COMPLETO_DEL_RELEASE>
    with:
      kit_sha: <SHA_COMPLETO_DEL_RELEASE>
```

El workflow llamado comprueba que `kit_sha` sea un SHA completo y que el checkout del kit resuelva exactamente a él. `agpctl validate` verifica además el tag/SHA declarado por el proyecto. Un repo con acceso a datos necesita aprobaciones confiables entregadas fuera del repo consumidor; como este preview no las recibe, falla cerrado en ese caso.

## Condiciones para exigir el gate

1. Publicar el release del kit y probar un proyecto consumidor real con resultado positivo y un PR inválido con resultado negativo.
2. Configurar un ruleset para la rama protegida que exija el check real emitido por la ejecución y bloquee merge con checks ausentes, fallidos o pendientes. Probar específicamente un PR que elimine `.github/workflows/agp-validation.yml`: debe permanecer bloqueado. Restringir bypass a administradores designados y auditar excepciones.
3. Agregar escáneres de dependencias/SAST acordes al perfil, con versiones fijadas, y completar el canal de aprobaciones confiables para acceso a datos. La configuración del proyecto por sí sola nunca debe poder autoaprobar excepciones.

Hasta que esas pruebas y protecciones existan, el resultado es una señal técnica de preview, **no** un gate corporativo no eludible ni autorización de despliegue.
