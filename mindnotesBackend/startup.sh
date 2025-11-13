#!/bin/sh
# Startup script for Railway/Render deployment

echo "🚀 Starting MindNotes Backend..."

# Navigate to app directory
cd /app

echo "🗄️ Creating database if it doesn't exist..."
PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U $POSTGRES_USER -p $POSTGRES_PORT -tc "SELECT 1 FROM pg_database WHERE datname = '$POSTGRES_DATABASE'" | grep -q 1 || PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U $POSTGRES_USER -p $POSTGRES_PORT -c "CREATE DATABASE $POSTGRES_DATABASE"

echo "📦 Running database migrations..."
python manage.py migrate --noinput

# Skip MongoDB index creation - causes SSL errors
# echo "🗄️ Initializing MongoDB indexes..."
python manage.py init_mongodb

echo "🔧 Collecting static files..."
python manage.py collectstatic --noinput || true

echo "✅ Starting Gunicorn server..."
exec gunicorn mindnotesBackend.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 3 --timeout 120 --log-level info --access-logfile - --error-logfile -
