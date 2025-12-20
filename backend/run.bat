@echo off
echo MissingLink Backend Baslatiliyor...
call venv\Scripts\activate.bat
python -m uvicorn app.main:app --reload
