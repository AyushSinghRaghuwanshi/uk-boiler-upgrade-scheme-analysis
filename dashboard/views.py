"""Page summaries and chart specifications computed from notebook exports."""

import pandas as pd

from .charts import (
    INK,
    BLUE,
    SECONDARY_BLUE,
    GREY,
    figure,
    line,
    bar,
    policy_markers,
    actual_expected,
)
from .data import table, records, monthly, councils, TECHNOLOGIES, MODELS


def kpi(label, value, detail, unit=""):
    return dict(label=label, value=value, detail=detail, unit=unit)


def technology_mix(counts):
    total = counts.sum()
    percentages = 100 * counts / total if total > 0 else counts * 0
    labels = list(TECHNOLOGIES)
    values = [
        (
            f"{label}<br>{count:,.0f} · {percentage:.2f}%"
            if total > 0
            else f"{label}<br>{count:,.0f} · n/a"
        )
        for label, count, percentage in zip(labels, counts, percentages)
    ]
    return figure(
        "Technology mix",
        "All three hydronic technologies in the selected date range, regardless of the technology filter. Labels show application counts and share.",
        [
            dict(
                type="bar",
                orientation="h",
                x=percentages.tolist(),
                y=labels,
                customdata=counts.tolist(),
                name="Applications",
                marker=dict(color=[BLUE, SECONDARY_BLUE, INK], cornerradius=5),
                hovertemplate=(
                    "%{y}<br>%{customdata:,.0f} applications<br>%{x:.2f}% of hydronic applications<extra></extra>"
                    if total > 0
                    else "%{y}<br>0 applications<br>Share unavailable: total is zero<extra></extra>"
                ),
            )
        ],
        accent=True,
        showlegend=False,
        bargap=0.5,
        margin=dict(l=145, r=18, t=12, b=56),
        xaxis=dict(
            range=[0, 100],
            ticksuffix="%",
            tickvals=[0, 50, 100],
            title=dict(text="Share of hydronic applications"),
        ),
        yaxis=dict(
            tickmode="array",
            tickvals=labels,
            ticktext=values,
            autorange="reversed",
            showgrid=False,
        ),
        annotations=(
            []
            if total > 0
            else [
                dict(
                    text="No applications recorded",
                    x=0.5,
                    y=1.05,
                    xref="paper",
                    yref="paper",
                    showarrow=False,
                )
            ]
        ),
    )


def overview(root, args):
    frame, shares, filters, months = monthly(root, args)
    regions = table(root, "outputs/regional_uptake_rates.csv").sort_values(
        "paid_per_1000"
    )
    coverage = table(root, "data/processed/geographic_coverage.csv").iloc[0]
    regional_fig = figure(
        "Where uptake is highest",
        "Fixed cumulative hydronic payments · matched councils only; independent of national filters.",
        [
            bar(
                regions.paid_per_1000,
                regions.region,
                "Payments / 1,000",
                SECONDARY_BLUE,
                orientation="h",
                hovertemplate="%{y}<br>%{x:.2f} / 1,000 households<extra></extra>",
            )
        ],
        xaxis=dict(title=dict(text="Payments / 1,000 Census 2021 households")),
        margin=dict(l=120),
        showlegend=False,
    )
    return dict(
        filters=filters,
        months=months,
        technologies=["Combined hydronic", *TECHNOLOGIES],
        scope=f"{filters['technology']} · England & Wales · {filters['start']} to {filters['end']}",
        kpis=[
            kpi(
                "Recorded applications",
                f"{frame.applications.sum():,.0f}",
                "Requests in selected months",
            ),
            kpi(
                "Paid redemptions",
                f"{frame.paid.sum():,.0f}",
                "Payments in selected months",
            ),
            kpi("Months in view", str(len(frame)), "Monthly reporting periods"),
            kpi(
                "Councils modelled",
                str(int(coverage.matched_districts)),
                "Fixed geography · 2 excluded",
            ),
        ],
        charts=[
            figure(
                "The path to cleaner heating",
                "Monthly counts · dotted: 20 Sep announcement · dashed: 23 Oct implementation (2023).",
                [
                    line(frame.index, frame.applications, "Applications"),
                    line(
                        frame.index,
                        frame.paid,
                        "Paid redemptions",
                        SECONDARY_BLUE,
                        dash="dash",
                    ),
                ],
                shapes=policy_markers(),
                xaxis=dict(
                    range=[
                        frame.index[0],
                        (
                            pd.Timestamp(frame.index[-1]) + pd.offsets.MonthEnd()
                        ).strftime("%Y-%m-%d"),
                    ]
                ),
                yaxis=dict(title=dict(text="Monthly vouchers")),
                hovermode="x unified",
            ),
            technology_mix(shares),
            regional_fig,
            figure(
                "The voucher journey",
                "Stage totals for selected months are separate flows, not a linked cohort or conversion rate.",
                [
                    bar(
                        ["Applications", "Issued", "Redemption requests", "Paid"],
                        [
                            float(frame[c].sum())
                            for c in [
                                "applications",
                                "issued",
                                "redemption_applications",
                                "paid",
                            ]
                        ],
                        "Vouchers",
                        BLUE,
                        hovertemplate="%{x}<br>%{y:,.0f}<extra></extra>",
                    )
                ],
                showlegend=False,
                yaxis=dict(title=dict(text="Vouchers in selected months")),
            ),
        ],
        notice="Applications are requests. Payments follow completed installations but reflect payment timing. These series do not measure the wider installation market.",
    )


def policy(root, args):
    comparison = table(root, "outputs/its_technology_sensitivity.csv")
    fits = table(root, "outputs/its_technology_fitted.csv")
    technology = args.get("technology", "Combined hydronic")
    if technology not in comparison.technology.tolist():
        raise ValueError(
            "Policy estimates are available for combined hydronic and air-to-water only."
        )
    row = comparison.loc[comparison.technology.eq(technology)].iloc[0]
    fit = fits.loc[fits.technology.eq(technology)]
    national, _, _, _ = monthly(
        root, {"start": "2022-06", "end": "2024-04", "technology": technology}
    )
    lower = line(
        fit.month,
        fit.CI_low,
        "Lower interval",
        GREY,
        showlegend=False,
        hoverinfo="skip",
    )
    upper = line(
        fit.month,
        fit.CI_high,
        "95% projected-mean interval",
        GREY,
        fill="tonexty",
        fillcolor="rgba(120,136,150,.18)",
        hoverinfo="skip",
    )
    return dict(
        filters={"technology": technology},
        technologies=comparison.technology.tolist(),
        scope=f"{technology} applications · fixed estimation window · Jun 2022–Apr 2024",
        kpis=[
            kpi(
                "Pre-period mean",
                f"{row.pre_mean:,.0f}",
                "Jun 2022–Aug 2023",
                "/ month",
            ),
            kpi(
                "Post-period mean",
                f"{row.post_mean:,.0f}",
                "Nov 2023–Apr 2024",
                "/ month",
            ),
            kpi(
                "Descriptive change",
                f"{row.change_pct:+.1f}",
                "Difference between period means",
                "%",
            ),
            kpi(
                "Trend-adjusted contrast",
                f"{row.average_post_contrast:+,.0f}",
                f"95% HAC: {row.CI_low:,.0f} to {row.CI_high:,.0f}",
                "/ month",
            ),
        ],
        charts=[
            figure(
                "Around the policy change",
                "Dotted: announcement 20 Sep · dashed: implementation 23 Oct 2023. September and October are omitted from fitting.",
                [line(national.index, national.applications, "Applications", INK)],
                shapes=policy_markers(),
                yaxis=dict(title=dict(text="Application requests")),
            ),
            figure(
                "What the fitted trend implies",
                "Interval describes the conditional no-break mean, not individual observations or causal uncertainty.",
                [
                    lower,
                    upper,
                    line(fit.month, fit.counterfactual, "No-break projection", GREY),
                    line(fit.month, fit.fitted, "Segmented fit", BLUE),
                    dict(
                        type="scatter",
                        mode="markers",
                        x=fit.month.tolist(),
                        y=fit.observed.tolist(),
                        name="Observed",
                        marker=dict(color=INK, size=6),
                    ),
                ],
                shapes=policy_markers(),
                yaxis=dict(title=dict(text="Applications / month")),
            ),
            figure(
                "Does technology scope change the result?",
                "Average fitted post-period contrast · Nov 2023–Apr 2024 · 95% calendar-lag HAC intervals.",
                [
                    bar(
                        comparison.technology,
                        comparison.average_post_contrast,
                        "Application contrast",
                        BLUE,
                        error_y=dict(
                            type="data",
                            symmetric=False,
                            array=(
                                comparison.CI_high - comparison.average_post_contrast
                            ).tolist(),
                            arrayminus=(
                                comparison.average_post_contrast - comparison.CI_low
                            ).tolist(),
                        ),
                    )
                ],
                showlegend=False,
                yaxis=dict(title=dict(text="Applications / month")),
            ),
        ],
        notice="Air-to-water grants rose £5,000 → £7,500; ground-source grants rose £6,000 → £7,500. Both application estimates are positive, but anticipation, confounding and a short window prevent causal attribution. Payment estimates include zero. Later policy changes are outside this estimation window.",
        table_title="Same specification, different technology scope",
        rows=records(comparison),
        columns=[
            ("technology", "Technology"),
            ("pre_mean", "Pre mean / month"),
            ("post_mean", "Post mean / month"),
            ("average_post_contrast", "Contrast / month"),
            ("CI_low", "95% lower"),
            ("CI_high", "95% upper"),
        ],
    )


def council(root, args):
    frame, filters, regions = councils(root, args)
    code = args.get("council", frame.sort_values("name").iloc[0].code)
    if code not in frame.code.tolist():
        raise ValueError("Choose a council within the selected region.")
    selected = frame.loc[frame.code.eq(code)].iloc[0]
    filters["council"] = code
    housing = [
        "Detached homes",
        "Flats",
        "Owner occupied",
        "Oil heating",
        "Electric heating",
        "Off-gas properties",
    ]
    shares = [
        selected[x] * 100
        for x in [
            "detached_share",
            "flat_share",
            "owner_share",
            "oil_share",
            "electric_share",
            "offgas_share",
        ]
    ]
    ranking = frame.sort_values("rate_per_1000", ascending=False).copy()
    ranking["rank"] = range(1, len(ranking) + 1)
    return dict(
        filters=filters,
        regions=["All regions", *regions],
        models=MODELS,
        council_options=records(frame.sort_values("name")[["code", "name", "region"]]),
        scope=f"{selected['name']} · {selected.region} · cumulative hydronic payments through Sep 2026",
        kpis=[
            kpi(
                "Paid redemptions",
                f"{selected.paid:,.0f}",
                "Recorded cumulative payments",
            ),
            kpi(
                "Observed uptake",
                f"{selected.rate_per_1000:.2f}",
                "Census 2021 household denominator",
                "/ 1,000",
            ),
            kpi(
                "Held-out expected",
                f"{selected.expected_rate:.2f}",
                filters["model"],
                "/ 1,000",
            ),
            kpi(
                "Observed − expected",
                f"{selected.gap:+.2f}",
                "Descriptive model gap",
                "/ 1,000",
            ),
        ],
        charts=[
            figure(
                "Your council in context",
                "Selected council versus pooled regional and selected-area rates; each uses total payments / total households.",
                [
                    bar(
                        ["Selected council", selected.region, "Filtered councils"],
                        [
                            selected.rate_per_1000,
                            1000
                            * frame.loc[frame.region.eq(selected.region)].paid.sum()
                            / frame.loc[
                                frame.region.eq(selected.region)
                            ].households.sum(),
                            1000 * frame.paid.sum() / frame.households.sum(),
                        ],
                        "Payments / 1,000",
                        BLUE,
                    )
                ],
                showlegend=False,
                yaxis=dict(title=dict(text="Payments / 1,000 households")),
            ),
            figure(
                "Housing context",
                "Census 2021 shares; off-gas is a separate DESNZ 2024 property estimate. Categories overlap.",
                [
                    bar(
                        shares,
                        housing,
                        "Share",
                        SECONDARY_BLUE,
                        orientation="h",
                        hovertemplate="%{y}<br>%{x:.1f}%<extra></extra>",
                    )
                ],
                xaxis=dict(title=dict(text="Share (%)"), range=[0, 100]),
                margin=dict(l=125),
                showlegend=False,
            ),
            figure(
                "Observed and expected uptake",
                f"{len(frame)} filtered councils · held-out predictions · click a point to select its council.",
                actual_expected(frame),
                xaxis=dict(title=dict(text="Expected payments / 1,000")),
                yaxis=dict(title=dict(text="Observed payments / 1,000")),
            ),
        ],
        notice="Model expectations are comparisons, not government targets or estimates of unmet demand. Council aggregates cannot explain individual behaviour. 316 of 318 BUS districts match; Barnsley and Sheffield are excluded after a partial boundary transfer. Rankings and gaps depend on the chosen model.",
        table_title=f"Ranked council comparison · {len(frame)} councils",
        rows=records(ranking),
        columns=[
            ("rank", "Rank"),
            ("name", "Council"),
            ("region", "Region"),
            ("paid", "Paid"),
            ("rate_per_1000", "Observed / 1,000"),
            ("expected_rate", "Expected / 1,000"),
            ("gap", "Gap / 1,000"),
        ],
    )


def models(root, args):
    frame, filters, regions = councils(root, args)
    scores = table(root, "outputs/geographic_cv_metrics.csv")
    nested = table(root, "outputs/nested_cv_metrics.csv").iloc[0]
    choices = table(root, "outputs/nested_cv_selections.csv")
    associations = table(root, "outputs/negative_binomial_associations.csv")
    feature_column = associations.columns[0]
    residual = frame.rate_per_1000 - frame.expected_rate
    return dict(
        filters=filters,
        regions=["All regions", *regions],
        models=MODELS,
        scope=f"{filters['model']} · {filters['region']} · diagnostic plots filter; validation scores use all 316 councils",
        kpis=[
            kpi(
                "Nested rate MAE",
                f"{nested.MAE_per_1000:.3f}",
                "Selection procedure · outer holdouts",
                "/ 1,000",
            ),
            kpi(
                "Nested count MAE",
                f"{nested.MAE_count:.2f}",
                "Absolute error per council",
                "payments",
            ),
            kpi(
                "Nested Poisson deviance",
                f"{nested.Poisson_deviance:.2f}",
                "Mean · unitless",
            ),
            kpi(
                "Diagnostic councils",
                str(len(frame)),
                "Selected region · held-out predictions",
            ),
        ],
        charts=[
            figure(
                "How the candidates compare",
                "Five geographic holdouts · comparison scores share selection data; lower MAE is better.",
                [bar(scores.model, scores.MAE_per_1000, "Rate MAE", BLUE)],
                showlegend=False,
                yaxis=dict(title=dict(text="MAE: payments / 1,000 households")),
            ),
            figure(
                "Predictions beyond the training regions",
                "Selected candidate and region · out-of-fold predictions, never training predictions.",
                actual_expected(frame),
                xaxis=dict(title=dict(text="Expected / 1,000")),
                yaxis=dict(title=dict(text="Observed / 1,000")),
            ),
            figure(
                "Where prediction errors fall",
                "Observed minus expected rates · selected candidate and region.",
                [
                    dict(
                        type="histogram",
                        x=residual.tolist(),
                        name="Rate residual",
                        marker=dict(color=SECONDARY_BLUE),
                        nbinsx=22,
                    )
                ],
                showlegend=False,
                xaxis=dict(title=dict(text="Residual: payments / 1,000")),
                yaxis=dict(title=dict(text="Councils")),
            ),
            figure(
                "Conditional housing associations",
                "Full-sample negative binomial rate ratios per +10 percentage points; 95% exploratory intervals. These are not boosting feature importances.",
                [
                    dict(
                        type="scatter",
                        mode="markers",
                        x=associations.rate_ratio_10pp.tolist(),
                        y=associations[feature_column]
                        .str.replace("_share", "")
                        .str.replace("_", " ")
                        .tolist(),
                        marker=dict(color=BLUE, size=9),
                        name="Rate ratio",
                        error_x=dict(
                            type="data",
                            symmetric=False,
                            array=(
                                associations.CI_high - associations.rate_ratio_10pp
                            ).tolist(),
                            arrayminus=(
                                associations.rate_ratio_10pp - associations.CI_low
                            ).tolist(),
                        ),
                    )
                ],
                showlegend=False,
                margin=dict(l=85),
                xaxis=dict(title=dict(text="Rate ratio / +10pp")),
                shapes=[
                    dict(
                        type="line",
                        x0=1,
                        x1=1,
                        y0=0,
                        y1=1,
                        yref="paper",
                        line=dict(color=GREY, dash="dot"),
                    )
                ],
            ),
        ],
        notice=f"Nested validation selects among four fixed candidates in four inner geographic folds, then evaluates the choice on each outer holdout. Gradient boosting was chosen in {int(choices.selected_model.eq('Gradient boosting').sum())} of {len(choices)} outer folds. Regions never overlap between train and validation. Household exposure, NB dispersion and boosting bins respect training splits. Earlier exploration and only ten regions still limit generalisation; future superiority is not guaranteed.",
        table_title="Candidate validation · all 316 councils",
        rows=records(scores),
        columns=[
            ("model", "Candidate"),
            ("MAE_count", "MAE (payments)"),
            ("MAE_per_1000", "MAE / 1,000"),
            ("Poisson_deviance", "Mean deviance"),
        ],
    )
