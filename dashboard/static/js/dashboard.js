/* Charts render locally from the same filtered payload as the page statistics. */
"use strict";

function chartLayout(spec) {
  const small = window.innerWidth < 600;
  const base = {
    autosize: true,
    paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
    font: {family: "Inter, Segoe UI, Arial, sans-serif", color: "#52606D", size: 12},
    margin: {l: 56, r: 18, t: 12, b: 76},
    xaxis: {gridcolor: "#E5EAF0", zeroline: false, automargin: true, tickfont: {size: 12}},
    yaxis: {gridcolor: "#E5EAF0", zerolinecolor: "#DCE8F3", automargin: true, tickfont: {size: 12}},
    legend: {orientation: "h", x: 0, y: small ? -.3 : -.22, font: {size: 12}},
    hoverlabel: {bgcolor: "#fff", font: {color: "#1F2933"}},
    showlegend: true,
  };
  const layout = {...base, ...spec.layout};
  for (const key of ["margin", "xaxis", "yaxis", "legend"]) {
    layout[key] = {...base[key], ...(spec.layout[key] || {})};
  }
  return layout;
}

async function renderCharts() {
  const payload = document.getElementById("chart-data");
  if (!payload) return;
  const specs = JSON.parse(payload.textContent);
  for (const [index, spec] of specs.entries()) {
    const target = document.getElementById(`chart-${index}`);
    try {
      if (!window.Plotly) throw new Error("Chart library unavailable");
      await Plotly.newPlot(target, spec.data, chartLayout(spec), {
        responsive: true, displayModeBar: false, displaylogo: false, showSendToCloud: false,
        modeBarButtonsToRemove: ["select2d", "lasso2d", "sendDataToCloud"],
        toImageButtonOptions: {format: "svg", filename: "bus-insights"},
      });
      if (location.pathname === "/councils") {
        target.on("plotly_click", event => {
          const code = event.points[0].customdata;
          if (!code || typeof code !== "string") return;
          const url = new URL(location.href);
          url.searchParams.set("council", code);
          location.assign(url);
        });
      }
    } catch (error) {
      target.textContent = "This chart could not load. Reload the page or check the local chart asset.";
      target.classList.add("chart-error");
      console.error(error);
    }
  }
}

const region = document.getElementById("region-filter");
const council = document.getElementById("council-filter");
if (region && council) {
  // A region change must not submit a council from the previous region.
  region.addEventListener("change", () => { council.disabled = true; region.form.requestSubmit(); });
}
const search = document.getElementById("council-search");
if (search && council) {
  const original = Array.from(council.options, option => ({value: option.value, text: option.text}));
  search.addEventListener("input", () => {
    const query = search.value.trim().toLocaleLowerCase();
    const matches = original.filter(option => option.text.toLocaleLowerCase().includes(query));
    council.replaceChildren(...matches.map(option => new Option(option.text, option.value)));
    council.disabled = matches.length === 0;
    search.setCustomValidity(matches.length ? "" : "No matching council in this region.");
  });
}
renderCharts();
