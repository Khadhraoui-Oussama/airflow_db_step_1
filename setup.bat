@echo off
echo 🏗️ Setting up Municipal Budget ETL Pipeline...
echo.

REM Check Docker
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker not running. Please start Docker Desktop.
    pause
    exit /b 1
)
echo ✅ Docker is running

REM Setup environment
if not exist .env (
    echo 📝 Creating .env from template...
    copy .env.example .env >nul
    echo ✅ Environment file created
) else (
    echo ✅ Environment file exists
)

REM Create directories
echo 📁 Creating directories...
for %%d in (logs data output processed reports scripts config) do (
    if not exist %%d mkdir %%d 2>nul
)

REM Start services
echo 🐳 Starting Docker services...
docker-compose up -d

if errorlevel 1 (
    echo ❌ Failed to start services
    pause
    exit /b 1
)

echo ⏳ Waiting for services to initialize...
timeout /t 30 /nobreak >nul

echo.
echo 🎉 Setup complete!
echo.
echo 📊 Access your services:
echo    Airflow UI:  http://localhost:8090 (airflow/airflow)
echo    pgAdmin:     http://localhost:8081 (admin@admin.com/admin)
echo.
echo 📚 Next steps:
echo    1. Wait 2-3 minutes for full startup
echo    2. Open Airflow UI and enable the ETL DAG
echo    3. Trigger the DAG to process budget data
echo    4. View results in pgAdmin
echo.
echo 🔧 Commands:
echo    Stop:     docker-compose down
echo    Logs:     docker-compose logs -f
echo    Restart:  docker-compose restart
echo.
pause