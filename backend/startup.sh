#!/bin/bash
# Azure App Service startup script
cd /home/site/wwwroot

# Run database migrations
python -m flask db upgrade

# Start gunicorn
gunicorn --bind=0.0.0.0:8000 --workers=2 --timeout=120 "app:create_app()"
