"""Los espejos `agpctl/mesa_datos_*.py` son el código de la Mesa sin cambios de lógica: nadie los edita a mano y no derivan de la Mesa.

Dos niveles:
  · siempre: cada espejo trae su encabezado, la huella de su cuerpo coincide (no se editó a mano) y solo difiere de la Mesa en los imports adaptados;
  · con `AGP_MESA_PATH` (ruta a un clon de la Mesa; opcional `AGP_MESA_REF`, por defecto `origin/main`): se regenera desde la Mesa y se compara, y falla si hay deriva.
"""
import importlib.util
import os
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _cargar_script():
    ruta = ROOT / "scripts" / "sincronizar_espejos_mesa.py"
    spec = importlib.util.spec_from_file_location("sincronizar_espejos_mesa", ruta)
    modulo = importlib.util.module_from_spec(spec)
    sys.modules["sincronizar_espejos_mesa"] = modulo
    spec.loader.exec_module(modulo)
    return modulo


S = _cargar_script()


class EspejosTests(unittest.TestCase):
    def test_cada_espejo_trae_encabezado_y_su_huella_coincide(self):
        for destino in S.ESPEJOS.values():
            texto = (ROOT / "agpctl" / f"{destino}.py").read_text(encoding="utf-8")
            encabezado, cuerpo = S.partir(texto)
            commit = re.search(r"^# ESPEJO-COMMIT: ([0-9a-f]{40})$", encabezado, re.MULTILINE)
            huella = re.search(r"^# ESPEJO-SHA256: ([0-9a-f]{64})$", encabezado, re.MULTILINE)
            self.assertTrue(commit and huella, f"{destino} no trae el commit de la Mesa y la huella")
            self.assertEqual(huella.group(1), S.huella(cuerpo), f"{destino} se editó a mano: regenerar con scripts/sincronizar_espejos_mesa.py")

    def test_el_espejo_no_importa_nada_de_la_mesa(self):
        for destino in S.ESPEJOS.values():
            _, cuerpo = S.partir((ROOT / "agpctl" / f"{destino}.py").read_text(encoding="utf-8"))
            self.assertNotRegex(cuerpo, r"(?m)^\s*(from|import)\s+src\b", f"{destino} importa src.*: el kit no tiene el código de la Mesa")

    def test_adaptar_solo_cambia_los_imports(self):
        mesa = ("import re\nfrom src.helpers import datos_ddl\nfrom src.helpers.datos_permisos import OPERACIONES, _texto_corto\n\nx = 1\n")
        esperado = ("import re\nfrom agpctl import mesa_datos_ddl as datos_ddl\nfrom agpctl.mesa_datos_permisos import OPERACIONES, _texto_corto\n\nx = 1\n")
        self.assertEqual(esperado, S.adaptar(mesa))

    def test_construir_y_partir_son_inversos_y_detectan_la_edicion(self):
        generado = S.construir("backend/src/helpers/datos_x.py", "a" * 40, "x = 1\r\ny = 2\r\n")
        encabezado, cuerpo = S.partir(generado)
        self.assertEqual("x = 1\ny = 2\n", cuerpo)
        self.assertIn(S.huella(cuerpo), encabezado)
        self.assertNotEqual(S.huella(cuerpo), S.huella(cuerpo + "z = 3\n"))
        with self.assertRaises(ValueError):
            S.partir("sin marca")

    @unittest.skipUnless(os.environ.get("AGP_MESA_PATH"), "AGP_MESA_PATH no definido: la comparación con la Mesa corre solo con un clon de la Mesa")
    def test_sin_deriva_frente_a_la_mesa(self):
        resultado = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "sincronizar_espejos_mesa.py"), "--mesa", os.environ["AGP_MESA_PATH"],
             "--ref", os.environ.get("AGP_MESA_REF", "origin/main"), "--check"],
            capture_output=True, text=True, encoding="utf-8", check=False)
        self.assertEqual(0, resultado.returncode, resultado.stderr or resultado.stdout)


if __name__ == "__main__":
    unittest.main()
