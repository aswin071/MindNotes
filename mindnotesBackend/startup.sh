#!/bin/sh
# Startup script for Railway/Render deployment

echo "🚀 Starting MindNotes Backend..."

# Navigate to app directory
cd /app

echo "📦 Running database migrations..."
python manage.py migrate --noinput

echo "🗄️ Initializing MongoDB indexes..."
python manage.py init_mongodb

echo "🔧 Collecting static files..."
python manage.py collectstatic --noinput || true

echo "✅ Starting Gunicorn server..."
exec gunicorn mindnotesBackend.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 3 --timeout 120 --log-level info --access-logfile - --error-logfile -
