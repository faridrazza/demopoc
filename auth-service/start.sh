#!/bin/sh
set -e

echo "Waiting for database to be ready..."
until PGPASSWORD=auth_pass psql -h auth-db -U auth_user -d auth_db -c '\q' 2>/dev/null; do
  echo "Database is unavailable - sleeping"
  sleep 2
done

echo "Database is up - running migrations"
alembic upgrade head

echo "Starting application"
exec uvicorn app.main:app --host 0.0.0.0 --port 8001
