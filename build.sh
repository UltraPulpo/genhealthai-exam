#!/usr/bin/env bash
# Render build script
set -o errexit

cd backend
pip install --upgrade pip
pip install -r requirements.txt

cd ../frontend
npm ci
npm run build

# Copy frontend build into Flask static folder
rm -rf ../backend/app/static
cp -r build/ ../backend/app/static/
