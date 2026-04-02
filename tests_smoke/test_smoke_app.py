from __future__ import annotations

import importlib
import sys
from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
API_DIR = REPO_ROOT / "API"

if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))


def load_app_module():
    return importlib.import_module("app")


class SmokeAppTest(unittest.TestCase):
    def test_import_app(self) -> None:
        app_module = load_app_module()
        self.assertTrue(hasattr(app_module, "app"))

    def test_fixed_routes(self) -> None:
        app_module = load_app_module()
        client = app_module.app.test_client()

        response = client.get("/getSession")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.is_json)
        self.assertIn("session", response.get_json())

        response = client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_set_session_clear(self) -> None:
        app_module = load_app_module()
        client = app_module.app.test_client()

        response = client.post("/setSession", json={"case": None})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.is_json)
        self.assertEqual(response.get_json(), {"osycase": None})

    def test_set_session_missing_case(self) -> None:
        app_module = load_app_module()
        client = app_module.app.test_client()

        response = client.post("/setSession", json={})
        self.assertEqual(response.status_code, 404)
        self.assertTrue(response.is_json)


if __name__ == "__main__":
    unittest.main()
