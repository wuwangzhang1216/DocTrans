@echo off
echo Starting Document Translation Web App...

REM Check if .env file exists in project root
if not exist "..\.env" (
    echo Error: .env file not found in project root!
    echo Please create it from .env.example and add your API keys
    echo Expected location: %CD%\..\.env
    exit /b 1
)

REM Install dependencies if needed
echo Checking dependencies...
cd backend && call npm install && cd ..
cd worker && call npm install && cd ..
cd frontend && call npm install && cd ..

REM Start all services
echo Starting services...
start "Backend Server" cmd /k "cd backend && npm start"
start "Worker Service" cmd /k "cd worker && npm start"
start "Frontend Dev Server" cmd /k "cd frontend && npm run dev"

echo.
echo Services started in separate windows:
echo - Frontend: http://localhost:3000
echo - Backend API: http://localhost:3001
echo.
echo Close the command windows to stop the services
pause