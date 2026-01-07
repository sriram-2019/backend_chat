@echo off
echo Flushing database...
cd backend
python flush_db.py
echo.
echo Database reset complete!
pause

