"""El Agente de Despliegue de mínimos (evaluación manual) no se desalinea: prompt, esquema, guías y ejemplos usan los mismos ids y rutas que existen en el kit."""
import json
import re
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
PROMPT = (ROOT / "prompt-agente-despliegue-minimos.md").read_text(encoding="utf-8")
GUIAS = json.loads((ROOT / "schemas" / "despliegue-minimos-guias.json").read_text(encoding="utf-8"))
ESQUEMA = json.loads((ROOT / "schemas" / "agent-despliegue-minimos-v1.schema.json").read_text(encoding="utf-8"))
VALIDO = json.loads((ROOT / "examples" / "agent-despliegue-minimos.valid.json").read_text(encoding="utf-8"))
INVALIDO = json.loads((ROOT / "examples" / "agent-despliegue-minimos.invalid.json").read_text(encoding="utf-8"))
ORDEN = ["login_msal", "perfil", "puerto_salud", "ci_verde", "manifiesto_datos"]


def _errores(instancia):
    return [e.message for e in Draft202012Validator(ESQUEMA).iter_errors(instancia)]


class AgenteDespliegueMinimos(unittest.TestCase):
    def test_el_esquema_es_valido(self):
        Draft202012Validator.check_schema(ESQUEMA)

    def test_los_cinco_minimos_estan_en_el_mismo_orden_en_el_prompt_las_guias_y_el_ejemplo(self):
        self.assertEqual(list(GUIAS["minimos"]), ORDEN)
        self.assertEqual([m["id"] for m in VALIDO["minimos"]], ORDEN)
        posiciones = [PROMPT.index(f"`{i}`") for i in ORDEN]
        self.assertEqual(posiciones, sorted(posiciones))

    def test_el_ejemplo_valido_cumple_el_esquema_y_el_invalido_no(self):
        self.assertEqual(_errores(VALIDO), [])
        errores = _errores(INVALIDO)
        self.assertGreaterEqual(len(errores), 3, errores)

    def test_un_minimo_que_no_cumple_exige_detalle_y_guia(self):
        roto = json.loads(json.dumps(VALIDO))
        roto["minimos"][1] = {"id": "perfil", "estado": "falta"}
        self.assertTrue(_errores(roto))
        roto["minimos"][1] = {"id": "perfil", "estado": "falta", "detalle": "No existe .agp/profile.yaml", "guia": "schemas/profile-v1.schema.json"}
        self.assertEqual(_errores(roto), [])

    def test_no_verificable_tambien_exige_detalle_y_guia_porque_bloquea(self):
        roto = json.loads(json.dumps(VALIDO))
        roto["minimos"][3] = {"id": "ci_verde", "estado": "no_verificable"}
        self.assertTrue(_errores(roto))

    def test_un_minimo_que_cumple_exige_evidencia(self):
        roto = json.loads(json.dumps(VALIDO))
        roto["minimos"][0] = {"id": "login_msal", "estado": "cumple"}
        self.assertTrue(_errores(roto))

    def test_solo_el_manifiesto_admite_no_aplica(self):
        roto = json.loads(json.dumps(VALIDO))
        roto["minimos"][0] = {"id": "login_msal", "estado": "no_aplica", "evidencia": "x"}
        self.assertTrue(_errores(roto))

    def test_deben_venir_los_cinco_en_orden(self):
        faltan = json.loads(json.dumps(VALIDO))
        faltan["minimos"] = faltan["minimos"][:4]
        self.assertTrue(_errores(faltan))
        desordenado = json.loads(json.dumps(VALIDO))
        desordenado["minimos"][0], desordenado["minimos"][1] = desordenado["minimos"][1], desordenado["minimos"][0]
        self.assertTrue(_errores(desordenado))

    def test_todo_lo_que_cita_la_guia_existe_en_el_kit(self):
        rutas = {g["ruta"] for sec in ("minimos", "avisos") for item in GUIAS[sec].values() for g in item["guias"]}
        self.assertGreater(len(rutas), 10)
        for ruta in rutas:
            self.assertTrue((ROOT / ruta).is_file(), f"la guía cita {ruta}, que no existe en el kit")

    def test_cada_mensaje_de_cada_pendiente_dice_de_donde_tomar_la_guia(self):
        for i, m in GUIAS["minimos"].items():
            self.assertTrue(m["queSePide"] and m["comoSeCorrige"] and m["guias"], f"el mínimo {i} no dice cómo corregirlo ni dónde mirar")
        for i, a in GUIAS["avisos"].items():
            self.assertTrue(a["queSePide"] and a["guias"], f"el aviso {i} no dice dónde mirar")

    def test_los_avisos_del_esquema_son_los_de_las_guias(self):
        self.assertEqual(ESQUEMA["$defs"]["aviso"]["properties"]["id"]["enum"], list(GUIAS["avisos"]))
        for i in GUIAS["avisos"]:
            self.assertIn(f"`{i}`", PROMPT, f"el prompt no menciona el aviso {i}")

    def test_el_prompt_cita_cada_guia_y_cada_comando(self):
        for sec in ("minimos", "avisos"):
            for i, item in GUIAS[sec].items():
                for g in item["guias"]:
                    self.assertIn(g["ruta"], PROMPT, f"el prompt no cita {g['ruta']} ({i})")
        for item in GUIAS["minimos"].values():
            for comando in item["comprobar"]:
                self.assertIn(comando.split(" --")[0], PROMPT)

    def test_el_prompt_cierra_las_reglas_clave(self):
        for frase in ("no_verificable", "bloquea", "Nunca pegues valores", "Responde únicamente con este JSON", "Copiar pendientes"):
            self.assertIn(frase, PROMPT)
        self.assertIn("agent-despliegue.md", PROMPT)
        self.assertNotIn("TODO", PROMPT)

    def test_las_rutas_del_prompt_existen_en_el_kit(self):
        patron = re.compile(r"`((?:schemas|examples|templates)/[A-Za-z0-9_./-]+\.[A-Za-z0-9]+|[A-Z][A-Z0-9-]+\.md|agent-[a-z-]+\.md|prompt-[a-z-]+\.md)`")
        for ruta in set(patron.findall(PROMPT)):
            self.assertTrue((ROOT / ruta).is_file(), f"el prompt cita {ruta}, que no existe")


if __name__ == "__main__":
    unittest.main()
