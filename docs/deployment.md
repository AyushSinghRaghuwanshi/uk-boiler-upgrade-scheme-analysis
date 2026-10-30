# Deploy BUS Insights

Deployment is prepared for **Render Free** using the existing Flask application,
a Python 3.12 container and Waitress as the production WSGI server. No public
service has been created or verified yet. Account access is required to continue.

## Hosting choice

Checked on 30 October 2026 against the providers' official documentation:

| Provider | Free option and relevant limits | Fit |
|---|---|---|
| [Render](https://render.com/docs/free) | Free web service; sleeps after 15 idle minutes; waking takes about a minute. 750 shared instance hours per workspace/month. Bandwidth and build allowances also apply. HTTPS is managed. | Selected: GitHub integration, automatic builds and declarative configuration. Suitable for a demonstration with cold starts. |
| [PythonAnywhere](https://help.pythonanywhere.com/pages/FreeAccountsFeatures/) | One free web app with one worker, 512 MiB disk, 100 CPU seconds and one-month expiry. | Flask-compatible alternative, with more manual setup and renewal. |

Render lists current plan information on its [pricing page](https://render.com/pricing).
Without a payment method, exhausting applicable free allowances suspends services
or builds rather than purchasing extra usage. Paid always-on hosting is optional
and has not been selected. Recheck prices and limits before provisioning.

## Steps requiring account access

1. Sign in to [Render](https://dashboard.render.com/). Create an account if needed.
2. Connect GitHub and authorise access to **only this repository**:
   `AyushSinghRaghuwanshi/uk-boiler-upgrade-scheme-analysis`.
3. Choose **New → Blueprint**, select the repository and branch `main`.
4. Review `render.yaml`: one web service, Docker runtime, **Free** instance,
   `/health` health check. No database, persistent disk, custom domain or secrets
   are required. If the name is unavailable, choose another service name.
5. Confirm the displayed cost is zero before creating the service. Stop if Render
   requests payment details or a paid plan; do not accept charges automatically.
6. Wait for a successful build and health check. Copy the actual HTTPS URL shown
   by Render, then complete the checks below before adding it to the README.

This is the remaining authorisation boundary. GitHub pushes alone do not create
a hosted dashboard. No deployment URL is supplied until a service exists.

## Runtime contents and configuration

The Docker build context is an allowlist in `.dockerignore`: Flask source,
templates, static assets, two requirements files and eleven small CSV exports.
It excludes raw downloads, notebooks, analysis dependencies, credentials, local
environments, temporary files and documentation images. No models are trained
at build time or on requests. Data is read-only and bundled with the image, so
ephemeral storage is sufficient. A data update requires regenerated exports and
a new build.

`PORT` is supplied by the host; the default is `10000`. Waitress binds to
`0.0.0.0`, with four threads and tracebacks disabled. Flask debug mode is off.
Render terminates HTTPS; the application uses relative internal URLs and needs
no forwarded-header trust configuration. No application secrets are needed.

If Docker is installed, a local container check is:

```sh
docker build -t bus-insights .
docker run --rm -p 5001:10000 bus-insights
```

Then visit `http://127.0.0.1:5001/health` and the five pages. Docker was unavailable
on the development machine, so the image build has not been executed locally.
The allowlisted CSV bundle and Waitress application are tested separately.

A production-server smoke test without Docker, from the project root:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-deploy.txt
.\.venv\Scripts\waitress-serve.exe --call --host=127.0.0.1 --port=5001 --no-expose-tracebacks dashboard.app:create_app
```

## Verify the public service

- Open `/`, `/policy`, `/councils`, `/models`, `/methodology` and `/health` over HTTPS.
- Confirm all chart assets load and the browser console and service logs are clear.
- Change national dates and technology; confirm KPIs and the overall technology mix.
- Change region, search/select a council and change prediction model; check values.
- Hover charts, click a council scatter point, navigate pages and resize the window.
- Test 1440, 1280, 768 and 390px widths using [the browser checklist](browser-testing.md).
- Confirm a cold start behaves as documented. Add the **verified** service URL near
  the top of the README only after these checks pass.

Provider references: [Docker deployment](https://render.com/docs/docker),
[Blueprint configuration](https://render.com/docs/blueprint-spec),
[Waitress runner](https://docs.pylonsproject.org/projects/waitress/en/stable/runner.html).
