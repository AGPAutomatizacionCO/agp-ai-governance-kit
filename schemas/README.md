# Contratos de datos del kit

| Archivo | Versión lógica (`$id`) | Productor/consumidor | Alcance |
|---|---|---|---|
| `governance-manifest.schema.json` | `urn:agp:governance:manifest:1` | Proyecto / Mesa / CI | Versión legible y SHA completo del kit, más perfil elegido. El esquema comprueba formato; `scripts/validate_governance_ref.py` comprueba que el tag resuelva al SHA. |
| `agp-deploy-v2.schema.json` | `urn:agp:governance:deployment-manifest:2` | Mesa / CI | Forma actual de `.github/agp-deploy.json` generada por `build_agp_deploy_json`. Sus campos son información y evidencia, no autorizaciones de acceso o producción. |
| `profile-v1.schema.json` | `urn:agp:governance:profile:1` | Catálogo de perfiles / `agpctl` | Contrato mínimo de build, runtime y destino para perfiles `container` y `static`. Los ejemplos son ilustrativos; ADR-02 define las convenciones aprobadas. |
| `data-access-manifest.schema.json` | `urn:agp:governance:data-access-manifest:1` | Agente de despliegue / Mesa | Accesos a datos **detectados**. No equivalen a permisos aprobados. El cambio de `$id` retira la referencia mutable a `main` sin cambiar el formato de datos. |

Los ejemplos de `examples/` terminados en `.valid.*` deben pasar su esquema; los `.invalid.*` deben fallar. `scripts/validate_release.py` verifica ambos casos en CI. El SHA ficticio de `governance.valid.yaml` sólo demuestra la estructura: no es un release real.

Un cambio que invalide documentos anteriormente válidos requiere versión nueva de esquema y revisión de impacto. No reemplazar un esquema versionado con reglas incompatibles manteniendo el mismo `$id` después de publicarlo.
