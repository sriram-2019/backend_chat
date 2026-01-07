@echo off
REM Run this script to apply the new migration (Windows)

echo Creating migration...
python manage.py makemigrations

echo Applying migration...
python manage.py migrate

echo Migration complete!
pause

