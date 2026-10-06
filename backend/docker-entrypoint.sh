#!/bin/sh
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting server..."
# Every request arrives from the frontend container, which passes the visitor's IP in
# X-Forwarded-For; trusting it lets the login rate limit count per visitor. Safe only
# because the backend isn't reachable from outside the compose network.
exec uvicorn app.main:app --host 0.0.0.0 --port 4000 --proxy-headers --forwarded-allow-ips '*'
