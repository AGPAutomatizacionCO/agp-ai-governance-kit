import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml

from agpctl import __main__ as cli
from agpctl import runtime


# Valores de prueba que PARECEN secretos (para comprobar que nunca se copian). Se arman por partes: escritos de corrido, el escáner de secretos del CI
# (gitleaks, que revisa todas las ramas) los tomaría por credenciales reales y bloquearía todos los PR del kit.
VALOR_PARECIDO_A_UN_TOKEN = "".join(["eyJhbGci", "OiJIUzI1NiJ9", "abcdefghijklmnop"])
VALOR_DEL_ENV_REAL = "".join(["NoDebe", "Leerse", "123"])


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.repo = Path(temp.name) / "Mi-Desarrollo"
        self.repo.mkdir()

    def _write(self, relative: str, content: str = "") -> None:
        path = self.repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def _python_app(self):
        self._write("backend/app/main.py", (
            'import os\n'
            'SECRET_KEY = os.getenv("SECRET_KEY")\n'
            'PROVIDER = os.getenv("LLM_PROVIDER", "groq")\n'
            'OLLAMA = os.getenv("OLLAMA_API_URL", "http://192.168.2.112:11434")\n'
            'DB = os.getenv("DATABASE_URL", "sqlite:///./app.db")\n'
            'KEY = os.environ["GROQ_API_KEY"]\n'
            'LIBRE = os.environ.get("MODO_RARO")\n'
            'RUTA = os.getenv("PATH")\n'
        ))

    def test_clasifica_secretos_env_decidir_y_omite_los_del_sistema(self):
        self._python_app()
        plan = runtime.plan(self.repo, "rpc")
        tipos = {v["name"]: v["tipo"] for v in plan["variables"]}
        self.assertEqual("secreto", tipos["SECRET_KEY"])
        self.assertEqual("secreto", tipos["GROQ_API_KEY"])
        self.assertEqual("secreto", tipos["DATABASE_URL"])
        self.assertEqual("env", tipos["LLM_PROVIDER"])
        self.assertEqual("env", tipos["OLLAMA_API_URL"])
        self.assertEqual("decidir", tipos["MODO_RARO"])
        self.assertEqual("omitir", tipos["PATH"])
        self.assertEqual(["MODO_RARO"], plan["porDecidir"])

    def test_el_yaml_propuesto_cumple_el_contrato_y_usa_el_prefijo(self):
        self._python_app()
        plan = runtime.plan(self.repo, "RPC")
        contrato = yaml.safe_load(plan["yaml"])
        self.assertEqual("runtime.agp/v1", contrato["apiVersion"])
        secretos = {s["name"]: s["secret"] for s in contrato["secrets"]}
        self.assertEqual("rpc-secret-key", secretos["SECRET_KEY"])
        self.assertTrue(all(runtime._NOMBRE_SECRETO.fullmatch(s) for s in secretos.values()))
        self.assertEqual("groq", {e["name"]: e["value"] for e in contrato["env"]}["LLM_PROVIDER"])
        self.assertNotIn("MODO_RARO", [e["name"] for e in contrato["env"]])
        self.assertIn("# DECIDIR: MODO_RARO", plan["yaml"])

    def test_duraciones_y_limites_con_token_no_son_secretos(self):
        self._write("a.py", 'import os\nos.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")\nos.getenv("GROQ_MAX_TOKENS", "4096")\n'
                            'os.getenv("SIGNED_URL_TTL_SECONDS", "900")\nos.getenv("API_TOKEN")\nos.getenv("DB_PASSWORD_MAX")\n')
        tipos = {v["name"]: v["tipo"] for v in runtime.plan(self.repo)["variables"]}
        self.assertEqual("env", tipos["ACCESS_TOKEN_EXPIRE_MINUTES"])
        self.assertEqual("env", tipos["GROQ_MAX_TOKENS"])
        self.assertEqual("env", tipos["SIGNED_URL_TTL_SECONDS"])
        self.assertEqual("secreto", tipos["API_TOKEN"])
        self.assertEqual("secreto", tipos["DB_PASSWORD_MAX"])  # PASSWORD manda sobre MAX

    def test_avisa_de_ip_privada_y_de_sqlite(self):
        self._python_app()
        avisos = " | ".join(runtime.plan(self.repo)["avisos"])
        self.assertIn("OLLAMA_API_URL", avisos)
        self.assertIn("no se alcanza desde Azure", avisos)
        self.assertIn("SQLite", avisos)

    def test_nunca_escribe_el_valor_de_un_secreto(self):
        self._write(".env.example", f"JWT_SECRET={VALOR_PARECIDO_A_UN_TOKEN}\nSEED_PWD=cambiame\nMODO=desarrollo\n")
        self._write(".env", f"REAL_SECRET={VALOR_DEL_ENV_REAL}\n")
        plan = runtime.plan(self.repo)
        texto = json.dumps(plan)
        self.assertNotIn(VALOR_PARECIDO_A_UN_TOKEN[:8], texto)
        self.assertNotIn("cambiame", texto)
        self.assertNotIn(VALOR_DEL_ENV_REAL, texto)
        self.assertNotIn("REAL_SECRET", texto)  # el .env real no se lee
        self.assertEqual("desarrollo", {v["name"]: v.get("value") for v in plan["variables"]}["MODO"])

    def test_reservadas_y_build_no_se_declaran(self):
        self._write("frontend/src/cfg.ts", "const a = import.meta.env.VITE_MSAL_CLIENT_ID; const b = process.env.AZURE_CLIENT_ID;\n")
        tipos = {v["name"]: v["tipo"] for v in runtime.plan(self.repo)["variables"]}
        self.assertEqual("build", tipos["VITE_MSAL_CLIENT_ID"])
        self.assertEqual("omitir", tipos["AZURE_CLIENT_ID"])
        self.assertTrue(runtime.check(self.repo)["valid"])

    def test_fuentes_de_solo_lectura_se_declaran_como_fuentes(self):
        self._write("api/db.py", 'import os\nU = os.getenv("CALENDARIO_VIEWER_USER")\nP = os.getenv("CALENDARIO_VIEWER_PWD")\n')
        plan = runtime.plan(self.repo)
        self.assertIn("fuentes: [calendar]", plan["yaml"])
        self.assertNotIn("secrets:", plan["yaml"])

    def test_lee_compose_y_node(self):
        self._write("docker-compose.yml", "services:\n  api:\n    environment:\n      - PORT_EXTERNO=1\n      - TOKEN_API=${TOKEN_API}\n")
        self._write("server.js", "const k = process.env.STRIPE_API_KEY;\n")
        nombres = {v["name"] for v in runtime.plan(self.repo)["variables"]}
        self.assertTrue({"PORT_EXTERNO", "TOKEN_API", "STRIPE_API_KEY"} <= nombres)

    def test_ignora_node_modules_y_tests(self):
        self._write("node_modules/x/index.js", "process.env.DE_UNA_LIBRERIA\n")
        self._write("tests/test_a.py", 'import os\nos.getenv("SOLO_EN_TESTS")\n')
        self.assertEqual([], runtime.plan(self.repo)["variables"])

    def test_check_sin_contrato_falla_si_el_codigo_usa_variables(self):
        self._python_app()
        resultado = runtime.check(self.repo)
        self.assertFalse(resultado["valid"])
        self.assertIn("falta .agp/runtime.yaml", resultado["issues"][0])

    def test_check_detecta_faltantes_sobrantes_y_secretos_en_env(self):
        self._write("app.py", 'import os\nos.getenv("DB_PWD")\nos.getenv("MODO", "x")\n')
        self._write(".agp/runtime.yaml", (
            "apiVersion: runtime.agp/v1\nenv:\n  - name: MODO\n    value: x\n  - name: SOBRANTE\n    value: y\n"
            "  - name: CLAVE\n    value: " + "A" * 44 + "\n"))
        issues = " | ".join(runtime.check(self.repo)["issues"])
        self.assertIn("el código usa DB_PWD", issues)
        self.assertIn("declara SOBRANTE pero el código no lo lee", issues)
        self.assertIn("el valor de CLAVE parece un secreto", issues)

    def test_check_pasa_con_el_contrato_propuesto_cuando_nada_queda_por_decidir(self):
        self._python_app()
        self._write(".agp/runtime.yaml", runtime.plan(self.repo)["yaml"])
        # MODO_RARO quedó «por decidir»: el contrato propuesto no lo declara y check lo exige hasta que una persona lo resuelva.
        self.assertEqual(["el código usa MODO_RARO (backend/app/main.py) y no está en runtime.yaml"], runtime.check(self.repo)["issues"])
        self._write("backend/app/main.py", (self.repo / "backend/app/main.py").read_text(encoding="utf-8").replace('LIBRE = os.environ.get("MODO_RARO")\n', ""))
        resultado = runtime.check(self.repo)
        self.assertTrue(resultado["valid"], resultado["issues"])

    def test_cli_plan_y_check_con_codigo_de_salida(self):
        self._python_app()
        with mock.patch("sys.argv", ["agpctl", "runtime", "plan", "--repo", str(self.repo), "--prefijo", "rpc"]):
            with mock.patch("builtins.print") as imprimir:
                self.assertEqual(0, cli.main())
        salida = json.loads(imprimir.call_args[0][0])
        self.assertTrue(salida["readOnly"])
        with mock.patch("sys.argv", ["agpctl", "runtime", "check", "--repo", str(self.repo)]):
            with mock.patch("builtins.print"):
                self.assertEqual(1, cli.main())


if __name__ == "__main__":
    unittest.main()
