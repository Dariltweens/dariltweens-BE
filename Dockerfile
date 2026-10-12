# syntax=docker/dockerfile:1

# Builder stage: compile wheels for all dependencies
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Build deps only needed to compile wheels (psycopg, Pillow, etc.).
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        libjpeg-dev \
        zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip wheel --wheel-dir /wheels -r requirements.txt


# Runtime stage: slim image with only what's needed to run
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DJANGO_SETTINGS_MODULE=config.settings

# Runtime shared libs for psycopg (libpq) and Pillow (jpeg/zlib).
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
        libjpeg62-turbo \
        zlib1g \
    && rm -rf /var/lib/apt/lists/*

# Non-root user to run the app.
RUN groupadd --system app && useradd --system --gid app --home-dir /app app

WORKDIR /app

# Install prebuilt wheels from the builder stage — no compiler in final image.
COPY --from=builder /wheels /wheels
COPY requirements.txt .
RUN pip install --no-index --find-links=/wheels -r requirements.txt \
    && rm -rf /wheels

COPY . .

# Collect static assets. Build-time-only env vars keep settings importable
# (collectstatic never touches the DB); real values come from the environment
# at runtime.
RUN SECRET_KEY=build-time-only DEBUG=False DATABASE_URL=postgres://build:build@localhost/build \
    python manage.py collectstatic --noinput

RUN chown -R app:app /app
USER app

EXPOSE 8000

# Gunicorn serving the WSGI app. Shell form so $PORT (injected by Railway) is
# expanded; falls back to 8000 locally. Override the command for the Celery
# worker:  celery -A config worker -l info
CMD gunicorn config.wsgi:application \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers "${WEB_CONCURRENCY:-3}" \
    --timeout 60 \
    --access-logfile - \
    --error-logfile -
