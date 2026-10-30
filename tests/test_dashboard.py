"""Verify Flask views against real notebook exports and supported filter grains."""

import json
from pathlib import Path
import re
import tempfile
import unittest

import numpy as np
import pandas as pd

from dashboard.app import create_app
from dashboard.data import TECHNOLOGIES, MODELS

ROOT = Path(__file__).resolve().parents[1]


class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.client = create_app({"TESTING": True}).test_client()

    def test_pages_and_local_assets(self):
        for route in ["/", "/policy", "/councils", "/models", "/methodology"]:
            response = self.client.get(route)
            self.assertEqual(response.status_code, 200, route)
            self.assertIn(b"Not endorsed by ICF, DESNZ or ONS", response.data)
            self.assertIn(b'aria-current="page"', response.data)
            if route != "/methodology":
                specs = json.loads(
                    re.search(
                        r'id="chart-data">(.*?)</script>',
                        response.get_data(as_text=True),
                        re.S,
                    ).group(1)
                )
                self.assertGreaterEqual(len(specs), 3)
        for asset in [
            "logo.svg",
            "css/dashboard.css",
            "js/dashboard.js",
            "js/plotly.min.js",
        ]:
            with self.client.get("/static/" + asset) as response:
                self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get("/health").json["status"], "ok")
        self.assertEqual(self.client.get("/nonexistent").status_code, 404)

    def test_national_filters_match_source_and_all_figures(self):
        source = pd.read_csv(
            ROOT / "data/processed/national_monthly_all_technologies_long.csv"
        )
        for label in ["Combined hydronic", *TECHNOLOGIES]:
            response = self.client.get(
                "/api/overview",
                query_string={
                    "start": "2023-11",
                    "end": "2024-04",
                    "technology": label,
                },
            )
            self.assertEqual(response.status_code, 200)
            payload = response.json
            technologies = (
                list(TECHNOLOGIES.values())
                if label == "Combined hydronic"
                else [TECHNOLOGIES[label]]
            )
            subset = source.loc[
                source["Technology type"].isin(technologies)
                & source.month.between("2023-11-01", "2024-04-01")
            ]
            expected = subset.pivot_table(
                index="month", columns="Voucher status", values="value", aggfunc="sum"
            )
            traces = payload["charts"][0]["data"]
            np.testing.assert_allclose(
                traces[0]["y"], expected["Voucher applications received"]
            )
            np.testing.assert_allclose(traces[1]["y"], expected["Redemptions paid"])
            for index, status in [
                (0, "Voucher applications received"),
                (1, "Redemptions paid"),
            ]:
                self.assertEqual(
                    payload["kpis"][index]["value"], f"{expected[status].sum():,.0f}"
                )
            self.assertEqual(payload["kpis"][2]["value"], "6")
            self.assertAlmostEqual(
                sum(payload["charts"][1]["data"][0]["values"]),
                expected["Voucher applications received"].sum(),
            )
            self.assertAlmostEqual(
                payload["charts"][3]["data"][0]["y"][-1],
                expected["Redemptions paid"].sum(),
            )
        payload = self.client.get("/api/overview").json
        self.assertEqual(payload["kpis"][0]["value"], "160,103")
        self.assertEqual(payload["kpis"][1]["value"], "96,185")
        single = self.client.get(
            "/api/overview", query_string={"start": "2025-01", "end": "2025-01"}
        ).json
        self.assertEqual(single["kpis"][2]["value"], "1")
        self.assertEqual(
            single["charts"][0]["layout"]["xaxis"]["range"],
            ["2025-01-01", "2025-01-31"],
        )

    def test_council_regions_models_and_selected_record(self):
        source = pd.read_csv(ROOT / "data/processed/local_authorities_model.csv")
        predictions = pd.read_csv(
            ROOT / "outputs/council_out_of_fold_predictions.csv"
        ).set_index("code")
        selected = source.loc[source.name.str.contains("Ceredigion")].iloc[0]
        for model in MODELS:
            payload = self.client.get(
                "/api/councils",
                query_string={
                    "region": "Wales",
                    "model": model,
                    "council": selected.code,
                },
            ).json
            self.assertEqual(len(payload["rows"]), 22)
            self.assertEqual({r["region"] for r in payload["rows"]}, {"Wales"})
            expected = (
                1000 * predictions.loc[selected.code, model] / selected.households
            )
            self.assertEqual(payload["kpis"][2]["value"], f"{expected:.2f}")
            self.assertEqual(
                payload["kpis"][3]["value"], f"{selected.rate_per_1000-expected:+.2f}"
            )
            row = next(row for row in payload["rows"] if row["code"] == selected.code)
            self.assertAlmostEqual(row["expected_rate"], expected, places=8)
            self.assertAlmostEqual(
                payload["charts"][1]["data"][0]["x"][0], selected.detached_share * 100
            )
            self.assertEqual(len(payload["charts"][2]["data"][0]["x"]), 22)
        for region in source.region.unique():
            payload = self.client.get(
                "/api/councils", query_string={"region": region}
            ).json
            self.assertEqual(len(payload["rows"]), source.region.eq(region).sum())
        self.assertEqual(len(self.client.get("/api/councils").json["rows"]), 316)

    def test_policy_sensitivity_and_same_specification(self):
        comparison = pd.read_csv(ROOT / "outputs/its_technology_sensitivity.csv")
        fits = pd.read_csv(ROOT / "outputs/its_technology_fitted.csv")
        original = (
            pd.read_csv(ROOT / "outputs/its_post_contrasts.csv")
            .set_index("outcome")
            .loc["applications"]
        )
        self.assertAlmostEqual(
            comparison.iloc[0].average_post_contrast, original.average_post_contrast
        )
        for row in comparison.itertuples():
            response = self.client.get(
                "/api/policy", query_string={"technology": row.technology}
            )
            self.assertEqual(response.status_code, 200)
            data = response.json
            self.assertEqual(
                data["kpis"][3]["value"], f"{row.average_post_contrast:+,.0f}"
            )
            expected = fits.loc[fits.technology.eq(row.technology)]
            np.testing.assert_allclose(
                data["charts"][1]["data"][3]["y"], expected.fitted
            )
            self.assertEqual(len(expected), 21)
            self.assertFalse(
                expected.month.str.startswith(("2023-09", "2023-10")).any()
            )
        self.assertGreater(comparison.iloc[1].CI_low, 0)

    def test_validation_scores_and_diagnostics(self):
        scores = pd.read_csv(ROOT / "outputs/geographic_cv_metrics.csv")
        nested = pd.read_csv(ROOT / "outputs/nested_cv_metrics.csv").iloc[0]
        for model in MODELS:
            payload = self.client.get(
                "/api/models", query_string={"region": "London", "model": model}
            ).json
            self.assertEqual(payload["kpis"][0]["value"], f"{nested.MAE_per_1000:.3f}")
            self.assertEqual(payload["kpis"][3]["value"], "33")
            np.testing.assert_allclose(
                payload["charts"][0]["data"][0]["y"], scores.MAE_per_1000
            )
            scatter = payload["charts"][1]["data"][0]
            residual = payload["charts"][2]["data"][0]["x"]
            np.testing.assert_allclose(
                np.array(scatter["y"]) - np.array(scatter["x"]), residual
            )

    def test_invalid_filters_and_missing_data_are_explained(self):
        for endpoint, query in [
            ("overview", {"start": "2024-04", "end": "2022-06"}),
            ("overview", {"technology": "Biomass"}),
            ("policy", {"technology": "Ground source"}),
            ("councils", {"region": "Imaginary"}),
            ("councils", {"council": "E08000038"}),
            ("models", {"model": "Unknown"}),
        ]:
            self.assertEqual(
                self.client.get("/api/" + endpoint, query_string=query).status_code, 400
            )
        with tempfile.TemporaryDirectory() as folder:
            missing = create_app({"TESTING": True, "DATA_ROOT": folder}).test_client()
            self.assertEqual(missing.get("/").status_code, 503)
            self.assertIn(
                b"Required analysis export unavailable", missing.get("/").data
            )
            self.assertEqual(missing.get("/api/models").status_code, 503)
            self.assertEqual(missing.get("/health").status_code, 503)
            self.assertEqual(missing.get("/methodology").status_code, 200)


if __name__ == "__main__":
    unittest.main()
