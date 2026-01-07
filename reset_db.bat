@echo off
echo ========================================
echo Resetting Database - INTELLIQ SHC
echo ========================================
echo.

cd /d %~dp0

echo Step 1: Stopping Django server if running...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *manage.py*" 2>nul
timeout /t 2 /nobreak >nul

echo Step 2: Deleting database file...
if exist db.sqlite3 (
    del /F /Q db.sqlite3
    echo Database file deleted.
) else (
    echo Database file not found.
)

echo Step 3: Deleting old migrations...
cd core\migrations
del /F /Q 0001_initial.py 2>nul
del /F /Q 0002_*.py 2>nul
echo Old migrations deleted.

echo Step 4: Creating fresh migrations...
cd ..\..
python manage.py makemigrations

echo Step 5: Applying migrations...
python manage.py migrate

echo.
echo ========================================
echo Database reset complete!
echo ========================================
echo.
echo You can now start the server with:
echo   python manage.py runserver
echo.
pause

