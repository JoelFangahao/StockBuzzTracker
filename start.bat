@echo off
echo Starting StockBuzzTracker...
echo.

echo [1/2] Starting FastAPI backend...
start "StockBackend" cmd /k "cd /d "D:\Quantized Finance\StockBuzzTracker\backend" && "D:\Quantized Finance\StockBuzzTracker\venv\Scripts\python.exe" -m uvicorn main:app --reload"

echo [2/2] Starting frontend server...
start "StockFrontend" cmd /k "cd /d "D:\Quantized Finance\StockBuzzTracker\frontend" && python -m http.server 8080"
start "" http://localhost:8080

echo.
echo All services are starting...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:8080
echo.
echo Close the windows to stop.
pause