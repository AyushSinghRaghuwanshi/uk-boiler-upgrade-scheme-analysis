"""Run with: python -m flask --app dashboard.app run --host 127.0.0.1"""

from pathlib import Path

from flask import Flask, jsonify, render_template, request

from . import views
from .data import DataUnavailable

PAGES = {
    "overview": ("Overview", "A clearer view of the transition.", views.overview),
    "policy": ("Policy Analysis", "What changed when grants changed?", views.policy),
    "councils": (
        "Council Explorer",
        "Every place has a different starting point.",
        views.council,
    ),
    "models": ("Model Insights", "Evidence behind the expectations.", views.models),
    "methodology": ("Methodology", "Clear methods. Honest boundaries.", None),
}


def create_app(config=None):
    app = Flask(__name__)
    app.config.update(DATA_ROOT=Path(__file__).resolve().parents[1])
    if config:
        app.config.update(config)

    @app.template_filter("number")
    def number(value):
        if isinstance(value, (float, int)):
            return (
                f"{value:,.2f}"
                if isinstance(value, float) and value != int(value)
                else f"{value:,.0f}"
            )
        return value

    @app.get("/")
    @app.get("/<page>")
    def page_view(page="overview"):
        if page not in PAGES:
            return (
                render_template(
                    "error.html", message="This page does not exist.", pages=PAGES
                ),
                404,
            )
        title, heading, builder = PAGES[page]
        payload = builder(app.config["DATA_ROOT"], request.args) if builder else {}
        return render_template(
            "methodology.html" if page == "methodology" else "analytics.html",
            page=page,
            title=title,
            heading=heading,
            pages=PAGES,
            **payload,
        )

    @app.get("/api/<page>")
    def api_view(page):
        if page not in PAGES or PAGES[page][2] is None:
            return jsonify(error="Unknown analytics endpoint"), 404
        return jsonify(PAGES[page][2](app.config["DATA_ROOT"], request.args))

    @app.get("/health")
    def health():
        # Read representative exports so a missing checkout is not reported as healthy.
        views.overview(app.config["DATA_ROOT"], {})
        return jsonify(status="ok")

    @app.errorhandler(DataUnavailable)
    def missing_data(error):
        if request.path.startswith("/api/") or request.path == "/health":
            return jsonify(error=str(error)), 503
        return render_template("error.html", message=str(error), pages=PAGES), 503

    @app.errorhandler(ValueError)
    def invalid_filter(error):
        if request.path.startswith("/api/"):
            return jsonify(error=str(error)), 400
        return render_template("error.html", message=str(error), pages=PAGES), 400

    @app.errorhandler(KeyError)
    def invalid_export(error):
        return missing_data(
            DataUnavailable(
                "An analysis export has an incompatible schema. Rerun the notebook to regenerate outputs."
            )
        )

    return app
