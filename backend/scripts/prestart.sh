#! /usr/bin/env bash

set -e
set -x

echo "🚀 Starting prestart script"
# Let the DB start
# python scripts/backend_pre_start.py

echo "🔄 Running migrations"
# Run migrations
alembic upgrade head

echo "🌱 Seeding data"
# Seed data
python scripts/seed.py

echo "Prestart script completed"