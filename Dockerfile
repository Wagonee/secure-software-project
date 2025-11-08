# syntax=docker/dockerfile:1.7-labs
FROM python:3.11-slim@sha256:e4676722fba839e2e5cdb844a52262b43e90e56dbd55b7ad953ee3615ad7534f AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./

RUN --mount=type=cache,target=/root/.cache/pip \
    pip wheel --no-cache-dir --wheel-dir=/wheels -r requirements.txt

FROM python:3.11-slim@sha256:e4676722fba839e2e5cdb844a52262b43e90e56dbd55b7ad953ee3615ad7534f AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN groupadd -r app && useradd -r -g app -u 1000 app

COPY --from=builder /wheels /wheels

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir /wheels/* && \
    rm -rf /wheels

COPY --chown=app:app . .

RUN chmod -R 755 /app && \
    chown -R app:app /app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()" || exit 1

USER app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
