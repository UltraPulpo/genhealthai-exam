#!/bin/bash
# Render startup script — runs migrations then starts gunicorn
set -e

echo "Running database migrations..."
python -m flask db upgrade 2>&1 || {
    echo "Migration failed, falling back to create_all..."
    python -c "from app import create_app; from app.extensions import db; app = create_app(); app.app_context().push(); db.create_all(); print('Tables created.')"
}

echo "Starting gunicorn..."
exec gunicorn --bind=0.0.0.0:${PORT:-8000} --workers=2 --timeout=120 "app:create_app()"
