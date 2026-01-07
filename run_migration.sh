#!/bin/bash
# Run this script to apply the new migration

echo "Creating migration..."
python manage.py makemigrations

echo "Applying migration..."
python manage.py migrate

echo "Migration complete!"

