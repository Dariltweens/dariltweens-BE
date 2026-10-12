#!/bin/sh
# Runs before the main process starts. Migrations run here (gated by
# RUN_MIGRATIONS) instead of relying on Railway's release-command config,
# which has proven easy to misconfigure/skip per-service in the dashboard.
set -e

if [ "${RUN_MIGRATIONS:-false}" = "true" ]; then
    echo "Running migrations..."
    python manage.py migrate --noinput
fi

exec "$@"
