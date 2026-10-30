FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=10000
WORKDIR /app
COPY requirements-dashboard.txt requirements-deploy.txt ./
RUN pip install --no-cache-dir -r requirements-deploy.txt \
    && useradd --create-home appuser
COPY dashboard/ ./dashboard/
COPY data/processed/ ./data/processed/
COPY outputs/ ./outputs/
USER appuser
EXPOSE 10000
CMD ["sh", "-c", "exec waitress-serve --call --host=0.0.0.0 --port=${PORT:-10000} --threads=4 --no-expose-tracebacks dashboard.app:create_app"]
