@echo off
echo MissingLink Backend Setup
echo ========================

echo.
echo Python virtual environment olusturuluyor...
python -m venv venv

echo.
echo Virtual environment aktive ediliyor...
call venv\Scripts\activate.bat

echo.
echo Gerekli paketler yukleniyor...
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo Setup tamamlandi!
echo.
echo Uygulamayi baslatmak icin:
echo   venv\Scripts\activate
echo   python -m uvicorn app.main:app --reload
echo.
pause
