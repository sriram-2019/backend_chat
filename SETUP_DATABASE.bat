@echo off
echo ========================================
echo Setting up Database - INTELLIQ SHC
echo ========================================
echo.

cd /d %~dp0

echo Creating migrations...
python manage.py makemigrations

echo.
echo Applying migrations...
python manage.py migrate

echo.
echo ========================================
echo Database setup complete!
echo ========================================
echo.
echo Database is now ready. You can:
echo   1. Start server: python manage.py runserver
echo   2. Create superuser: python manage.py createsuperuser
echo.
pause

