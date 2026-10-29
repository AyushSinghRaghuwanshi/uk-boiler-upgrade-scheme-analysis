"""Check target isolation and the provenance of nested validation results."""

import ast
from pathlib import Path
import unittest

import nbformat
import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_poisson_deviance
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[1]


class AnalysisTests(unittest.TestCase):
    def test_held_out_targets_do_not_affect_predictions(self):
        councils = pd.read_csv(ROOT / "data/processed/local_authorities_model.csv")
        folds = pd.read_csv(ROOT / "data/processed/geographic_cv_folds.csv")
        self.assertEqual(councils.code.tolist(), folds.code.tolist())
        features = [
            "detached_share",
            "flat_share",
            "owner_share",
            "oil_share",
            "electric_share",
            "offgas_share",
        ]
        exposure = councils.households.to_numpy()
        namespace = {
            "np": np,
            "sm": sm,
            "HistGradientBoostingRegressor": HistGradientBoostingRegressor,
            "SEED": 42,
            "councils": councils,
            "features": features,
            "groups": councils.region,
            "X": sm.add_constant(councils[features] * 10, has_constant="add"),
            "y": councils.paid.to_numpy().copy(),
            "exposure": exposure,
            "offset": np.log(exposure),
        }
        notebook = nbformat.read(ROOT / "notebooks/01_data_understanding.ipynb", as_version=4)
        source = next(
            cell.source
            for cell in notebook.cells
            if cell.cell_type == "code" and cell.source.startswith("def predict_counts(")
        )
        exec(compile(ast.parse(source), "notebook prediction helper", "exec"), namespace)
        train = np.flatnonzero(folds.fold.to_numpy() != 1)
        held_out = np.flatnonzero(folds.fold.to_numpy() == 1)
        with threadpool_limits(limits=1):
            original, _ = namespace["predict_counts"](train, held_out)
            namespace["y"][held_out] += 100_000
            changed, _ = namespace["predict_counts"](train, held_out)
        for model in original:
            np.testing.assert_allclose(changed[model], original[model], rtol=0, atol=0)

    def test_nested_selection_and_metrics_are_auditable(self):
        selections = pd.read_csv(ROOT / "outputs/nested_cv_selections.csv")
        inner_scores = pd.read_csv(ROOT / "outputs/nested_cv_inner_metrics.csv")
        membership = pd.read_csv(ROOT / "data/processed/nested_cv_folds.csv")
        folds = pd.read_csv(ROOT / "data/processed/geographic_cv_folds.csv")
        predictions = pd.read_csv(ROOT / "outputs/nested_cv_predictions.csv")
        candidates = pd.read_csv(ROOT / "outputs/council_out_of_fold_predictions.csv").set_index(
            "code"
        )
        reported = pd.read_csv(ROOT / "outputs/nested_cv_metrics.csv").iloc[0]
        self.assertTrue(predictions.code.is_unique)
        for row in selections.itertuples():
            inner = inner_scores.loc[inner_scores.outer_fold.eq(row.outer_fold)]
            chosen = inner.set_index("model").MAE_per_1000.idxmin()
            self.assertEqual(row.selected_model, chosen)
            inner_members = membership.loc[membership.outer_fold.eq(row.outer_fold)]
            outer_test = folds.loc[folds.fold.eq(row.outer_fold)]
            self.assertTrue(set(inner_members.code).isdisjoint(outer_test.code))
            self.assertTrue(set(inner_members.region).isdisjoint(outer_test.region))
            self.assertEqual(set(inner_members.code), set(folds.code) - set(outer_test.code))
            test_predictions = predictions.loc[predictions.outer_fold.eq(row.outer_fold)]
            self.assertEqual(set(test_predictions.selected_model), {chosen})
            np.testing.assert_allclose(
                test_predictions.expected_count, candidates.loc[test_predictions.code, chosen]
            )
        actual = predictions.paid.to_numpy()
        expected = predictions.expected_count.to_numpy()
        households = predictions.households.to_numpy()
        self.assertAlmostEqual(reported.MAE_count, mean_absolute_error(actual, expected))
        self.assertAlmostEqual(
            reported.MAE_per_1000,
            mean_absolute_error(1000 * actual / households, 1000 * expected / households),
        )
        self.assertAlmostEqual(reported.Poisson_deviance, mean_poisson_deviance(actual, expected))


if __name__ == "__main__":
    unittest.main()
