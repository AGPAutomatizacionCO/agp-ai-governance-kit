"""La documentación normativa no se desalinea de lo que el kit realmente trae.

Tres comprobaciones deterministas (sin red): las rutas que llama el cliente de la plantilla están en el contrato del túnel de roles,
cada requisito del Agente de Despliegue está en la lista de obligatorios, y los archivos del kit que citan las normas existen.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

NORMAS = (
    "ACCESO-Y-ROLES-DEL-DESARROLLO.md",
    "ARQUITECTURA-DESPLIEGUE.md",
    "COMO-DEJARLO-FUNCIONAL.md",
    "CONTRATO-TUNEL-ROLES.md",
    "DESPLIEGUE-A-MAIN.md",
    "INTEGRAR-MSAL.md",
    "NOMENCLATURA-DATOS.md",
    "OBLIGATORIOS-DEL-DESARROLLO.md",
    "PERMISOS-Y-SECRETOS-DEL-WORKER.md",
    "agent-despliegue.md",
    "prompt-agente-despliegue-evaluacion.md",
    "templates/auth-estandar/README.md",
)
# Archivos que cita la norma pero que viven en el repositorio de cada desarrollo, no en el kit.
_DEL_DESARROLLO = {"ROLES.md"}
_RUTA_DEL_KIT = re.compile(
    r"^(?:(?:templates|schemas|examples|agpctl|scripts)/[A-Za-z0-9_./-]+\.[A-Za-z0-9]+|[A-Z][A-Z0-9-]+\.md|agent-[a-z-]+\.md|prompt-[a-z-]+\.md)$"
)


def _leer(ruta: str) -> str:
    return (ROOT / ruta).read_text(encoding="utf-8")


class DocumentacionNormativaTests(unittest.TestCase):
    def test_las_rutas_del_cliente_estan_en_el_contrato_del_tunel(self):
        cliente = _leer("templates/auth-estandar/src/services/rolesMesa.js")
        contrato = _leer("CONTRATO-TUNEL-ROLES.md")
        rutas = {re.split(r"[?$]", r.replace("`", ""))[0].rstrip("/") for r in re.findall(r'llamar\(\s*[`"](/[^`"]*)[`"]', cliente)}
        self.assertTrue(rutas, "no se encontraron rutas en el cliente: ¿cambió su forma?")
        for ruta in sorted(rutas):
            base = ruta.split("${")[0].rstrip("/")
            self.assertIn(base, contrato, f"el contrato del túnel no menciona la ruta {ruta} que llama rolesMesa.js")

    def test_el_contrato_lista_todas_las_rutas_de_la_mesa_que_documenta(self):
        contrato = _leer("CONTRATO-TUNEL-ROLES.md")
        for ruta in ("/mios", "/estado", "/personas", "/personas-por-area", "/solicitudes", "/asignacion-por-area", "/peticiones", "/secretos",
                     "/secretos/historial", "/secretos/reiniciar", "/directorio", "/auditoria"):
            self.assertIn(f"`{ruta}", contrato, f"falta la ruta {ruta} en el contrato")

    def test_los_roles_no_tienen_vigencia_en_las_normas(self):
        for nombre in ("ACCESO-Y-ROLES-DEL-DESARROLLO.md", "CONTRATO-TUNEL-ROLES.md", "agent-despliegue.md"):
            texto = _leer(nombre)
            self.assertRegex(texto, r"sin vigencia|no tienen vigencia", nombre)
            self.assertIn("RegistroDesarrollos_Roles", texto, nombre)   # SAC y los que ya tenían roles siguen en las tablas centrales
            self.assertRegex(texto, r"crea y valida", nombre)           # desarrollos nuevos: tres tablas en su esquema, creadas y validadas por el worker
            self.assertRegex(texto, r"nombre reservado|no las declara", nombre)   # el desarrollador no las declara en el manifiesto
            self.assertNotRegex(texto, r"(?i)no está implementado|pendiente y no implementado|el worker no las crea", nombre)

    def test_el_vocabulario_de_area_esta_aclarado(self):
        contrato = _leer("CONTRATO-TUNEL-ROLES.md")
        self.assertIn("## 3.1 Dos cosas llamadas «área»", contrato)
        self.assertIn("EJEMPLO ficticio", contrato)
        self.assertIn("departamento de Microsoft", contrato)
        self.assertRegex(_leer("agent-despliegue.md"), r"no usa nombres de área ni de departamento inventados")

    def test_cada_requisito_del_agente_esta_en_la_lista_de_obligatorios(self):
        prompt = _leer("prompt-agente-despliegue-evaluacion.md")
        bloque = prompt.split("## PASO 2B", 1)[1].split("### Regla de login Microsoft", 1)[0]
        ids = set(re.findall(r"^([a-z_]+)\s{2,}\S", bloque, re.MULTILINE))
        ids |= set(re.findall(r"^([a-z_]+) ", bloque, re.MULTILINE)) & {"pantalla_sin_acceso"}
        self.assertTrue({"perfil", "runtime", "recursos_externos", "secretos_norma", "datos_locales"} <= ids, ids)
        obligatorios = _leer("OBLIGATORIOS-DEL-DESARROLLO.md")
        for requisito in sorted(ids):
            self.assertIn(f"`{requisito}`", obligatorios, f"OBLIGATORIOS-DEL-DESARROLLO.md no menciona el requisito {requisito}")

    def test_los_archivos_del_kit_que_citan_las_normas_existen(self):
        for norma in NORMAS:
            self.assertTrue((ROOT / norma).is_file(), f"falta {norma}")
            for cita in set(re.findall(r"`([^`\s]+)`", _leer(norma))):
                cita = cita.strip(".,;:")
                if "<" in cita or "*" in cita or cita in _DEL_DESARROLLO or not _RUTA_DEL_KIT.match(cita):
                    continue
                self.assertTrue((ROOT / cita).exists() or (ROOT / Path(norma).parent / cita).exists(),
                                f"{norma} cita `{cita}` y no existe en el kit")


if __name__ == "__main__":
    unittest.main()
