"""Local explorer for the notebook's cleaned data and held-out model results."""

from pathlib import Path
import json

import altair as alt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data/processed"
OUTPUTS = ROOT / "outputs"
BLUE, TEAL, ORANGE, GREY = "#2463A0", "#168577", "#C58030", "#75818C"

st.set_page_config(page_title="BUS policy & uptake explorer", page_icon="📊", layout="wide")


@st.cache_data
def load_results(file_versions):
    # Modification times invalidate the cache after a notebook rerun.
    monthly = pd.read_csv(DATA / "national_monthly_hydronic.csv", parse_dates=["month"])
    councils = pd.read_csv(DATA / "local_authorities_model.csv")
    predictions = pd.read_csv(OUTPUTS / "council_out_of_fold_predictions.csv")
    metrics = pd.read_csv(OUTPUTS / "geographic_cv_metrics.csv")
    summary = json.loads((OUTPUTS / "analysis_summary.json").read_text(encoding="utf-8"))
    models = metrics.model.tolist()
    assert councils.code.is_unique and predictions.code.is_unique
    councils = councils.merge(predictions[["code"] + models], on="code", validate="one_to_one")
    assert len(councils) == summary["councils_modelled"]
    return monthly, councils, metrics, summary


paths = [
    DATA / "national_monthly_hydronic.csv",
    DATA / "local_authorities_model.csv",
    OUTPUTS / "council_out_of_fold_predictions.csv",
    OUTPUTS / "geographic_cv_metrics.csv",
    OUTPUTS / "analysis_summary.json",
]
if any(not path.exists() for path in paths):
    st.error("The analysis outputs are missing. Run the project notebook first; see README.md.")
    st.stop()

monthly, councils, metrics, summary = load_results(tuple(path.stat().st_mtime_ns for path in paths))
winner = summary["geographic_cv_rate_MAE_winner"]

st.caption("ENGLAND & WALES · PUBLIC DATA THROUGH SEPTEMBER 2026")
st.title("Boiler Upgrade Scheme")
st.markdown("Explore the 2023 grant change and differences in local heat pump uptake.")
page = st.sidebar.radio(
    "View", ["National trends", "Council uptake", "Findings & methods"], key="page"
)
st.sidebar.caption("Independent educational analysis. Not endorsed by ICF, DESNZ or ONS.")
st.sidebar.caption("Hydronic heat pumps only: air-to-water, ground-source and shared ground loop.")

if page == "National trends":
    period = st.sidebar.selectbox(
        "Time window",
        ["Full history", "Around the 2023 uplift", "Intervention model window"],
        key="period",
    )
    limits = {
        "Full history": ("2022-05-01", "2026-09-01"),
        "Around the 2023 uplift": ("2023-04-01", "2024-04-01"),
        "Intervention model window": ("2022-06-01", "2024-04-01"),
    }
    start, end = limits[period]
    selected = monthly.loc[monthly.month.between(start, end)]
    columns = st.columns(3)
    columns[0].metric("Applications in this window", f"{selected.applications.sum():,.0f}")
    columns[1].metric("Paid redemptions in this window", f"{selected.paid.sum():,.0f}")
    columns[2].metric("Months shown", str(len(selected)))
    st.caption(
        f"{selected.month.min():%B %Y}–{selected.month.max():%B %Y}. Payments follow installations but record payment timing."
    )
    if period == "Intervention model window":
        st.caption(
            "September and October 2023 remain visible for context; the regression omits these transition months."
        )

    st.subheader("Applications and payments")
    chart_data = selected.melt(
        id_vars="month",
        value_vars=["applications", "paid"],
        var_name="measure",
        value_name="vouchers",
    )
    chart_data["measure"] = chart_data.measure.map(
        {"applications": "Applications", "paid": "Paid redemptions"}
    )
    lines = (
        alt.Chart(chart_data)
        .mark_line(strokeWidth=2.5)
        .encode(
            x=alt.X("month:T", title=None),
            y=alt.Y("vouchers:Q", title="Monthly vouchers"),
            color=alt.Color(
                "measure:N",
                title=None,
                scale=alt.Scale(domain=["Applications", "Paid redemptions"], range=[BLUE, TEAL]),
            ),
            tooltip=[
                alt.Tooltip("month:T", title="Month", format="%b %Y"),
                "measure:N",
                alt.Tooltip("vouchers:Q", format=",.0f"),
            ],
        )
    )
    events = pd.DataFrame(
        {
            "date": pd.to_datetime(["2023-09-20", "2023-10-23"]),
            "event": ["20 Sep: announcement", "23 Oct: £7,500 grant begins"],
        }
    )
    rules = (
        alt.Chart(events)
        .mark_rule(strokeDash=[5, 4], color=ORANGE)
        .encode(x="date:T", tooltip=["event:N", alt.Tooltip("date:T", format="%d %b %Y")])
    )
    st.altair_chart((lines + rules).properties(height=340), width="stretch")
    st.caption(
        "Dashed markers: announcement on 20 September 2023 and grant uplift on 23 October 2023. Points represent monthly totals, not daily activity."
    )

    difference = selected.assign(flow_difference=selected.applications - selected.paid)
    st.altair_chart(
        alt.Chart(difference)
        .mark_area(color=BLUE, opacity=0.3)
        .encode(
            x=alt.X("month:T", title=None),
            y=alt.Y("flow_difference:Q", title="Applications minus payments"),
            tooltip=[
                alt.Tooltip("month:T", format="%b %Y"),
                alt.Tooltip("flow_difference:Q", format=",.0f"),
            ],
        )
        .properties(height=170),
        width="stretch",
    )
    st.caption(
        "The flow difference compares different cohorts. It is not a conversion rate or a measured backlog."
    )
    with st.expander("What does the intervention model suggest?"):
        st.image(str(OUTPUTS / "its_counterfactual.png"), width="stretch")
        app_result = next(
            row for row in summary["its_contrasts"] if row["outcome"] == "applications"
        )
        st.write(
            f"The fitted post-period application contrast is {app_result['average_post_contrast']:,.0f}/month "
            f"(95% HAC interval {app_result['CI_low']:,.0f}–{app_result['CI_high']:,.0f}). "
            "The payment contrast includes zero. These are model-dependent associations, not causal estimates."
        )

elif page == "Council uptake":
    region = st.sidebar.selectbox(
        "Region", ["All regions"] + sorted(councils.region.unique()), key="region"
    )
    model = st.sidebar.selectbox(
        "Expected uptake model",
        metrics.model.tolist(),
        index=metrics.model.tolist().index(winner),
        key="model",
    )
    selected = (
        councils.copy()
        if region == "All regions"
        else councils.loc[councils.region.eq(region)].copy()
    )
    selected["expected_count"] = selected[model]
    selected["expected_rate"] = 1000 * selected.expected_count / selected.households
    selected["rate_gap"] = selected.rate_per_1000 - selected.expected_rate
    columns = st.columns(3)
    columns[0].metric("Councils shown", str(len(selected)))
    columns[1].metric("Observed payments", f"{selected.paid.sum():,.0f}")
    columns[2].metric(
        "Payments / 1,000 households", f"{1000*selected.paid.sum()/selected.households.sum():.2f}"
    )
    st.caption(
        "Cumulative payments, May 2022–September 2026, divided by Census 2021 households. This is an area rate, not the share of eligible properties."
    )

    if region == "All regions":
        regional = selected.groupby("region", as_index=False).agg(
            paid=("paid", "sum"), households=("households", "sum")
        )
        regional["rate"] = 1000 * regional.paid / regional.households
        st.subheader("Regional uptake")
        st.altair_chart(
            alt.Chart(regional)
            .mark_bar(color=TEAL)
            .encode(
                x=alt.X("rate:Q", title="Paid redemptions / 1,000 households"),
                y=alt.Y("region:N", sort="-x", title=None),
                tooltip=["region:N", alt.Tooltip("rate:Q", format=".2f")],
            )
            .properties(height=300),
            width="stretch",
        )

    st.subheader("Observed versus expected uptake")
    left, right = st.columns(2)
    points = (
        alt.Chart(selected)
        .mark_circle(size=55, color=BLUE, opacity=0.7)
        .encode(
            x=alt.X("expected_rate:Q", title="Held-out expected / 1,000"),
            y=alt.Y("rate_per_1000:Q", title="Observed / 1,000"),
            tooltip=[
                "name:N",
                "code:N",
                "region:N",
                alt.Tooltip("rate_per_1000:Q", title="Observed", format=".2f"),
                alt.Tooltip("expected_rate:Q", title="Expected", format=".2f"),
                alt.Tooltip("rate_gap:Q", title="Gap", format="+.2f"),
            ],
        )
    )
    maximum = max(selected.expected_rate.max(), selected.rate_per_1000.max())
    equality = (
        alt.Chart(pd.DataFrame({"rate": [0.0, maximum]}))
        .mark_line(color=GREY, strokeDash=[4, 4])
        .encode(x="rate:Q", y="rate:Q")
    )
    left.altair_chart((points + equality).properties(height=300), width="stretch")
    lowest = selected.loc[selected.rate_gap.lt(0)].nsmallest(10, "rate_gap")
    right.altair_chart(
        alt.Chart(lowest)
        .mark_bar(color=ORANGE)
        .encode(
            x=alt.X("rate_gap:Q", title="Observed minus expected / 1,000"),
            y=alt.Y("name:N", title=None, sort="x", axis=alt.Axis(labelLimit=170)),
            tooltip=["name:N", alt.Tooltip("rate_gap:Q", format="+.2f")],
        )
        .properties(height=300, title="Largest negative descriptive gaps"),
        width="stretch",
    )
    st.caption(
        "Expectations come from models trained without these councils' regions. Negative gaps are investigation leads, not evidence of policy failure. Model disagreement is substantial in some areas."
    )

    code = st.selectbox(
        "Inspect a council",
        selected.sort_values("name").code.tolist(),
        format_func=lambda code: f"{selected.set_index('code').loc[code,'name']} ({code})",
        key="council",
    )
    council = selected.set_index("code").loc[code]
    details = st.columns(3)
    details[0].metric("Observed rate", f"{council.rate_per_1000:.2f}")
    details[1].metric("Held-out expected rate", f"{council.expected_rate:.2f}")
    details[2].metric("Descriptive rate gap", f"{council.rate_gap:+.2f}")
    export = selected[
        [
            "code",
            "name",
            "region",
            "paid",
            "households",
            "rate_per_1000",
            "expected_count",
            "expected_rate",
            "rate_gap",
        ]
    ].sort_values("rate_gap")
    st.dataframe(
        export.rename(
            columns={
                "paid": "Observed payments",
                "rate_per_1000": "Observed / 1,000",
                "expected_rate": "Expected / 1,000",
                "rate_gap": "Gap / 1,000",
            }
        ),
        hide_index=True,
    )
    st.download_button(
        "Download this comparison",
        export.to_csv(index=False),
        "bus_council_comparison.csv",
        "text/csv",
    )
    st.caption(
        "Coverage: 316 of 318 BUS councils. Barnsley and Sheffield are excluded because of changed boundaries; four unitary reorganisations use documented sums of predecessor districts."
    )

else:
    st.subheader("What the evidence supports")
    st.write(
        f"Mean applications rose {summary['applications_before_after_pct']:.1f}% and paid redemptions "
        f"{summary['paid_before_after_pct']:.1f}% between June 2022–August 2023 and November 2023–April 2024. "
        "These observed changes do not isolate the grant's causal contribution."
    )
    st.write(
        "The policy model has 15 pre and six fully post months. Anticipation, administrative lags, revisions and "
        "later insulation, planning and 2026 grant changes limit interpretation. Paid redemptions are not dated installations."
    )
    st.subheader("Validation on held-out regions")
    st.dataframe(
        metrics.rename(
            columns={
                "model": "Model",
                "MAE_count": "Count MAE",
                "MAE_per_1000": "Rate MAE / 1,000",
                "Poisson_deviance": "Mean Poisson deviance",
            }
        ).round(3),
        hide_index=True,
    )
    st.write(
        "Five frozen folds hold out whole regions or Wales. Poisson and NB2 use household offsets; boosting uses "
        "household-weighted rates. Seed 42 and single-thread numeric operations improve repeatability. "
        "The candidate scores above are used for model comparison, so the winning score is selection-optimistic."
    )
    nested = summary["nested_cv_metrics"][0]
    st.write(
        f"Nested geographic validation evaluates choosing the model inside each training split: "
        f"rate MAE {nested['MAE_per_1000']:.3f} payments per 1,000 Census households, "
        f"count MAE {nested['MAE_count']:.2f} payments and mean Poisson deviance "
        f"{nested['Poisson_deviance']:.2f} (unitless). Four inner geographic folds select "
        "the model; an untouched outer fold evaluates that selection. This remains a small "
        "sample of ten broad geographic groups, not a guarantee of performance elsewhere."
    )
    st.subheader("What remains uncertain")
    st.write(
        "Census households are an old proxy for eligible property stock. Income, costs, deprivation and installer "
        "supply are missing. Council associations do not establish individual behaviour or equitable access. "
        "Gap rankings change across models and require local validation."
    )
    st.info(
        "ICF's reported 74% scheme additionality concerns the overall BUS scheme. It is not the effect of the October 2023 uplift."
    )
    st.markdown(
        "[DESNZ evaluation](https://www.gov.uk/government/publications/evaluation-of-the-boiler-upgrade-scheme-2026) · "
        "[BUS statistics](https://www.gov.uk/government/statistics/boiler-upgrade-scheme-statistics-september-2026) · "
        "[ONS Census data](https://www.ons.gov.uk/datasets/TS044/editions/2021/versions/4)"
    )

st.divider()
st.caption(
    "Contains public sector information licensed under the Open Government Licence v3.0. Source-specific OS and Royal Mail notices remain applicable; see README.md."
)
