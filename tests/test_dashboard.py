"""Smoke-test dashboard filters against the notebook's actual exports."""

from pathlib import Path
import json
import unittest

import numpy as np
import pandas as pd
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()

    def assert_no_errors(self):
        self.assertEqual([item.message for item in self.app.exception], [])

    def test_national_window_uses_real_totals(self):
        self.assert_no_errors()
        self.app.selectbox(key="period").set_value("Around the 2023 uplift").run()
        self.assert_no_errors()
        monthly = pd.read_csv(ROOT / "data/processed/national_monthly_hydronic.csv")
        selected = monthly.loc[monthly.month.between("2023-04-01", "2024-04-01")]
        values = {item.label: item.value for item in self.app.metric}
        self.assertEqual(
            values["Applications in this window"], f"{selected.applications.sum():,.0f}"
        )
        self.assertEqual(values["Months shown"], str(len(selected)))

    def test_council_region_and_model_filters(self):
        self.app.radio(key="page").set_value("Council uptake").run()
        self.assert_no_errors()
        self.assertEqual(len(self.app.dataframe[0].value), 316)
        self.app.selectbox(key="region").set_value("Wales").run()
        self.assert_no_errors()
        for model in ["Negative binomial", "Pooled rate", "Poisson", "Gradient boosting"]:
            self.app.selectbox(key="model").set_value(model).run()
            self.assert_no_errors()
            shown = self.app.dataframe[0].value
            self.assertEqual(len(shown), 22)
            self.assertEqual(set(shown.region), {"Wales"})
            predictions = pd.read_csv(ROOT / "outputs/council_out_of_fold_predictions.csv")
            expected = shown[["code", "households"]].merge(
                predictions[["code", model]], on="code", validate="one_to_one"
            )
            np.testing.assert_allclose(
                shown["Expected / 1,000"], 1000 * expected[model] / expected.households
            )
            np.testing.assert_allclose(
                shown["Gap / 1,000"], shown["Observed / 1,000"] - shown["Expected / 1,000"]
            )
        self.app.selectbox(key="council").set_value("W06000008").run()
        self.assert_no_errors()
        shown = self.app.dataframe[0].value.set_index("code").loc["W06000008"]
        values = {item.label: item.value for item in self.app.metric}
        self.assertEqual(values["Observed rate"], f"{shown['Observed / 1,000']:.2f}")
        self.app.selectbox(key="region").set_value("London").run()
        self.assert_no_errors()
        self.assertEqual(len(self.app.dataframe[0].value), 33)

    def test_findings_uses_executed_metrics(self):
        self.app.radio(key="page").set_value("Findings & methods").run()
        self.assert_no_errors()
        shown = self.app.dataframe[0].value
        expected = pd.read_csv(ROOT / "outputs/geographic_cv_metrics.csv")
        np.testing.assert_allclose(shown["Rate MAE / 1,000"], expected.MAE_per_1000.round(3))
        self.assertTrue(any("74%" in item.value for item in self.app.info))
        summary = json.loads((ROOT / "outputs/analysis_summary.json").read_text())
        score = summary["nested_cv_metrics"][0]["MAE_per_1000"]
        self.assertTrue(any(f"rate MAE {score:.3f}" in item.value for item in self.app.markdown))


if __name__ == "__main__":
    unittest.main()
