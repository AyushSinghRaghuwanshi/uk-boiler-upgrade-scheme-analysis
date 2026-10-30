"""Load prepared exports and apply only filters supported by each data grain."""

from functools import lru_cache
from pathlib import Path

import pandas as pd

TECHNOLOGIES = {
    "Air-to-water": "Air-to-Water Heat Pumps",
    "Ground source": "Ground Source Heat Pumps",
    "Shared ground loop": "Shared Ground Loop Ground Source Heat Pumps",
}
MODELS = ["Gradient boosting", "Negative binomial", "Poisson", "Pooled rate"]


class DataUnavailable(Exception):
    pass


@lru_cache(maxsize=48)
def read_csv(path, modified):
    return pd.read_csv(path)


def table(root, relative):
    path = Path(root) / relative
    try:
        result = read_csv(str(path), path.stat().st_mtime_ns).copy()
        if result.empty:
            raise ValueError("Empty export")
        return result
    except (OSError, ValueError, pd.errors.ParserError) as error:
        raise DataUnavailable(
            f"Required analysis export unavailable: {relative}"
        ) from error


def records(frame):
    # Pandas converts numpy scalars and missing values to portable JSON values.
    import json

    return json.loads(frame.to_json(orient="records"))


def monthly(root, args):
    frame = table(root, "data/processed/national_monthly_all_technologies_long.csv")
    frame["month"] = pd.to_datetime(frame.month)
    months = sorted(frame.month.dt.strftime("%Y-%m").unique())
    start, end = args.get("start", months[0]), args.get("end", months[-1])
    technology = args.get("technology", "Combined hydronic")
    if start not in months or end not in months or start > end:
        raise ValueError("Choose a valid start and end month in chronological order.")
    if technology not in ["Combined hydronic", *TECHNOLOGIES]:
        raise ValueError("Choose one of the available hydronic technologies.")
    technologies = (
        list(TECHNOLOGIES.values())
        if technology == "Combined hydronic"
        else [TECHNOLOGIES[technology]]
    )
    selected = frame.loc[
        frame["Technology type"].isin(technologies)
        & frame.month.dt.strftime("%Y-%m").between(start, end)
    ]
    pivot = selected.pivot_table(
        index="month", columns="Voucher status", values="value", aggfunc="sum"
    )
    pivot = pivot.rename(
        columns={
            "Voucher applications received": "applications",
            "Redemptions paid": "paid",
            "Vouchers issued": "issued",
            "Redemption applications received": "redemption_applications",
        }
    )
    pivot.index = pivot.index.strftime("%Y-%m-%d")
    shares = (
        frame.loc[
            frame["Technology type"].isin(TECHNOLOGIES.values())
            & frame.month.dt.strftime("%Y-%m").between(start, end)
            & frame["Voucher status"].eq("Voucher applications received")
        ]
        .groupby("Technology type")
        .value.sum()
        .reindex(TECHNOLOGIES.values(), fill_value=0)
    )
    return pivot, shares, {"start": start, "end": end, "technology": technology}, months


def councils(root, args):
    frame = table(root, "data/processed/local_authorities_model.csv")
    predictions = table(root, "outputs/council_out_of_fold_predictions.csv")
    frame = frame.merge(
        predictions[["code", *MODELS]], on="code", validate="one_to_one"
    )
    regions = sorted(frame.region.unique())
    region = args.get("region", "All regions")
    model = args.get("model", MODELS[0])
    if region not in ["All regions", *regions] or model not in MODELS:
        raise ValueError("Choose an available region and prediction model.")
    if region != "All regions":
        frame = frame.loc[frame.region.eq(region)].copy()
    frame["expected_count"] = frame[model]
    frame["expected_rate"] = 1000 * frame.expected_count / frame.households
    frame["gap"] = frame.rate_per_1000 - frame.expected_rate
    return frame, {"region": region, "model": model}, regions
