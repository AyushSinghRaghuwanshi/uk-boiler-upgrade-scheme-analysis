"""Verify that the allowlisted deployment exports are sufficient to serve the app."""

from pathlib import Path
import shutil
import tempfile
import unittest

from dashboard.app import create_app

ROOT = Path(__file__).resolve().parents[1]


class DeploymentTests(unittest.TestCase):
    def test_minimal_data_bundle_serves_all_pages(self):
        rules = (ROOT / ".dockerignore").read_text().splitlines()
        exports = [
            rule[1:]
            for rule in rules
            if rule.startswith(("!data/processed/", "!outputs/"))
            and rule.endswith(".csv")
        ]
        self.assertEqual(len(exports), 11)
        self.assertLess(sum((ROOT / name).stat().st_size for name in exports), 300_000)
        with tempfile.TemporaryDirectory() as folder:
            for name in exports:
                target = Path(folder) / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / name, target)
            app = create_app({"TESTING": True, "DATA_ROOT": folder})
            self.assertFalse(app.debug)
            with app.test_client() as client:
                for page in [
                    "/",
                    "/policy",
                    "/councils",
                    "/models",
                    "/methodology",
                    "/health",
                ]:
                    self.assertEqual(client.get(page).status_code, 200, page)
                for page, filters in [
                    (
                        "overview",
                        {
                            "start": "2023-11",
                            "end": "2024-04",
                            "technology": "Air-to-water",
                        },
                    ),
                    ("policy", {"technology": "Air-to-water"}),
                    ("councils", {"region": "Wales", "model": "Negative binomial"}),
                    ("models", {"region": "London", "model": "Poisson"}),
                ]:
                    self.assertEqual(
                        client.get("/api/" + page, query_string=filters).status_code,
                        200,
                    )
            self.assertFalse((Path(folder) / "data/raw").exists())
            self.assertFalse((Path(folder) / "notebooks").exists())


if __name__ == "__main__":
    unittest.main()
