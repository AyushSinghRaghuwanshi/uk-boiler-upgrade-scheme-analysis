"""Small Plotly.js figure builders; no plotting service or model fitting."""

INK = "#1F3C5A"
BLUE = "#2F5D8A"
SECONDARY_BLUE = "#527FA9"
GREY = "#788896"


def figure(title, note, traces, *, accent=False, **layout):
    return {
        "title": title,
        "note": note,
        "accent": accent,
        "data": traces,
        "layout": layout,
    }


def line(x, y, name, color=INK, dash="solid", **kwargs):
    return dict(
        type="scatter",
        mode="lines+markers",
        marker=dict(size=3),
        x=list(x),
        y=list(y),
        name=name,
        line=dict(color=color, width=2.5, dash=dash),
        hovertemplate="%{x|%b %Y}<br>%{y:,.0f}<extra>%{fullData.name}</extra>",
        **kwargs,
    )


def bar(x, y, name, color=BLUE, **kwargs):
    return dict(
        type="bar",
        x=list(x),
        y=list(y),
        name=name,
        marker=dict(color=color, cornerradius=5),
        **kwargs,
    )


def policy_markers():
    return [
        dict(
            type="line",
            xref="x",
            yref="paper",
            x0=date,
            x1=date,
            y0=0,
            y1=1,
            line=dict(color=color, dash=dash, width=1.4),
        )
        for date, color, dash in [
            ("2023-09-20", GREY, "dot"),
            ("2023-10-23", BLUE, "dash"),
        ]
    ]


def actual_expected(frame):
    limit = max(frame.rate_per_1000.max(), frame.expected_rate.max()) * 1.05
    return [
        dict(
            type="scatter",
            mode="markers",
            x=frame.expected_rate.tolist(),
            y=frame.rate_per_1000.tolist(),
            text=frame["name"].tolist(),
            customdata=frame.code.tolist(),
            name="Councils",
            marker=dict(
                color=BLUE, size=8, opacity=0.72, line=dict(color="white", width=1)
            ),
            hovertemplate="%{text}<br>Expected %{x:.2f}<br>Observed %{y:.2f}<extra></extra>",
        ),
        dict(
            type="scatter",
            mode="lines",
            x=[0, limit],
            y=[0, limit],
            name="Equal observed / expected",
            line=dict(color=GREY, dash="dot"),
            hoverinfo="skip",
        ),
    ]
