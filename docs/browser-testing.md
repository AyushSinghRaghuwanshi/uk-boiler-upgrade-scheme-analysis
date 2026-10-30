# Browser verification and screenshots

## Results (30 October 2026)

All five pages were loaded in headless Chromium (Playwright) at **1440, 1280,
768 and 390px** widths against the local Flask app with default filters.

| Width | Pages returning 200 | Charts rendered | Console errors | Failed requests | Horizontal overflow |
|---|---|---|---|---|---|
| 1440 | 5/5 | all | 0 | 0 | none |
| 1280 | 5/5 | all | 0 | 0 | none |
| 768 | 5/5 | all | 0 | 0 | none |
| 390 | 5/5 | all | 0 | 0 | none |

Screenshots in `docs/images/dashboard-*.png` are genuine 1440 × 1000 captures.
Not yet checked: keyboard focus order and hover/click interactions by hand.

## Responsive checks still required

Run the Flask application, open it in Chrome and use DevTools device emulation
at **1440, 1280, 768 and 390px** widths with browser zoom at 100%.
Check **all five pages at every width**:

| Page | Check |
|---|---|
| Overview | KPI alignment; all three technology bars, count/share labels and axis titles; date/technology filters; technology mix remains overall for the chosen dates. |
| Policy Analysis | Technology selector, uncertainty band, policy lines, comparison table and readable legends. |
| Council Explorer | Region change, case-insensitive council search, council selection, candidate model change, scatter-point navigation and scrolling ranked table. |
| Model Insights | Candidate and region filters affect diagnostic plots; full-sample validation scores stay fixed and labelled. |
| Methodology | Source links, navigation, readable text and wrapping of long links. |

At each width, inspect clipping, overlap, horizontal page overflow, chart resizing,
keyboard focus and button access. Wide data tables may scroll within their own
container. Verify hover and chart clicks with the toolbar hidden. Inspect the
browser console and Network tab for errors and failed requests. Confirm all
navigation links open the expected page.

## Capture genuine previews

Use a consistent **1440 × 1000 CSS-pixel viewport**, 100% browser zoom, default
filters and fully rendered charts. Capture the page viewport with DevTools'
**Capture screenshot** command to exclude browser chrome and personal tabs.
Do not use generated images or recreate the interface in an image editor.

Save PNG files under `docs/images/`:

- `dashboard-overview.png`: Overview KPIs, timeline and technology mix.
- `dashboard-policy.png`: Policy Analysis KPIs and counterfactual chart.
- `dashboard-models.png`: Model Insights validation and held-out diagnostic plots.

Inspect each image for personal information and legible labels. Keep consistent
dimensions, compress losslessly where useful, and add a compact three-column
Markdown preview table to the README after the actual files exist. Never add
links to missing screenshots. Record the tested widths/pages and any fixes here
before changing the README's visual-testing status.
