# Política inicial de controles de seguridad para CI/CD

**Estado:** propuesta para T02.3. El workflow local `release-validation` ya incluye lint, pruebas, `pip-audit`, Gitleaks y Bandit para el código Python del propio kit. Aún no está publicado ni ejecutándose como check obligatorio en repositorios de proyectos; tampoco cubre SAST multilenguaje, IaC ni imágenes.

## Gates por etapa

| Etapa | Control | Herramienta candidata | Resultado exigido |
|---|---|---|---|
| PR | Pruebas y lint del perfil | Pytest/Ruff para Python; test/lint de `package.json` para Node | Exit 0 y evidencia del commit evaluado. |
| PR | Secretos en cambios e historial pertinente | [Gitleaks](https://github.com/gitleaks/gitleaks/releases) | Cualquier secreto real bloquea; redactar valores en logs. |
| PR | SAST | [Bandit](https://pypi.org/project/bandit/) para Python; [Semgrep Community Edition](https://pypi.org/project/semgrep/) con reglas locales versionadas para ampliar lenguajes | Alta/crítica bloquea; hallazgos medios requieren triage. La edición comunitaria de Semgrep tiene límites de análisis entre archivos. |
| PR/build | Dependencias | [pip-audit](https://pypi.org/project/pip-audit/) para Python; `npm audit` con lockfile para Node | Crítica/alta bloquea salvo excepción aprobada. |
| PR/build | IaC | Compilación Bicep y reglas Azure verificadas en un piloto | Plantilla inválida o recurso fuera de política bloquea. Seleccionar y probar el motor de reglas antes de imponerlo. |
| Después del build | Imagen OCI | [Grype](https://github.com/anchore/grype/releases) sobre digest, con base de datos actualizada | Crítica/alta bloquea antes de publicar/promover. |

Versiones candidatas verificadas al redactar: Gitleaks `v8.30.0`, Bandit `1.9.4`, Semgrep `1.177.0`, pip-audit `2.10.1`, Grype `v0.119.0`, Ruff `0.16.8`. El workflow definitivo debe fijar y verificar binarios por SHA/checksum y registrar versión y fecha de la base de vulnerabilidades. Una actualización exige PR y nueva validación. El [aviso oficial de Trivy](https://github.com/aquasecurity/trivy/security/advisories/GHSA-69fq-xp46-6x23) documenta una alteración de tags/releases de su ecosistema en 2026; por eso no se debe instalar un escáner desde `latest` ni confiar sólo en un tag de acción.

La auditoría inicial del kit usa `pip-audit==2.10.1` y `--strict`: falla también si no puede completar la auditoría. Es deliberadamente más estricta que la regla crítica/alta de la tabla porque el reporte de `pip-audit` no proporciona una severidad homogénea para todos los avisos. El paquete del escáner está fijado por versión, pero todavía faltan hashes de distribución/transitivas para cumplir la política de procedencia del workflow definitivo.

El escaneo inicial de secretos descarga Gitleaks `v8.30.0` para Linux x64 y verifica el SHA-256 `79a3ab579b53f71efd634f3aaf7e04a0fa0cf206b7ed434638d1547a2470a66e` antes de ejecutarlo. Escanea historial y árbol actual, con secretos redactados en la salida; un hallazgo o fallo de la herramienta detiene el job. Una autoprueba con un token sintético exige exit 1 para detectar regresiones silenciosas. Falta ejecutar este paso en GitHub; el host local no puede descargar/ejecutar el binario Linux. Se evitó `v8.30.1` por un [reporte de falso negativo](https://github.com/gitleaks/gitleaks/issues/2170); esto no prueba que Linux x64 esté afectado, pero justifica la versión conservadora y la autoprueba.

Bandit `1.9.4` analiza `agpctl/` y `scripts/`, bloqueando hallazgos de severidad alta. Pasó localmente. Es un control inicial del kit, no sustituye Semgrep ni un SAST específico para Node, React u otros perfiles; su instalación aún depende de paquetes transitivos sin hashes fijados.

## Severidad y disponibilidad

- Secretos confirmados: bloqueo inmediato, rotación del secreto y tratamiento del incidente. No publicar el valor en logs ni reportes.
- Crítica/alta: bloqueo del merge o de la promoción. Si el hallazgo es falso positivo o no aplicable, usar excepción temporal aprobada.
- Media: triage obligatorio antes de producción; SLA y fecha de corrección acordados con seguridad y Tech Lead.
- Baja/informativa: registrar y priorizar sin bloqueo inicial.
- Fallo del escáner, base de vulnerabilidades inaccesible o reporte ilegible: estado `pendiente`, nunca `aprobado`. La promoción productiva se bloquea hasta repetir el control o activar un proceso excepcional documentado.

## Excepciones

Cada excepción debe indicar `scanner`, identificador/fingerprint del hallazgo, repositorio, commit o rango, ambiente, motivo, aprobador distinto del autor, ticket y vencimiento. La Mesa o un servicio de gobierno controla y firma/atestigua la excepción; un archivo editable en el PR del proyecto no concede permiso. La excepción se aplica sólo al hallazgo específico y debe reevaluarse al vencer o cambiar el artefacto.

## Evidencia mínima

Conservar versión del escáner, fuente/fecha de reglas o base, commit, kit SHA, perfil, imagen digest, resumen de hallazgos sin secretos, excepción aplicada y enlace de ejecución. La Mesa vincula esa evidencia al despliegue. El build ocurre una sola vez y los escáneres de imagen evalúan el mismo digest que se promueve.
