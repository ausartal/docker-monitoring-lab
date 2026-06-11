@echo off
title Docker Monitoring Lab — PENS Demo
color 0A

echo.
echo  ========================================================
echo   DOCKER MONITORING LAB — PENS IT
echo   Modul 1-9 Full Stack Demo
echo  ========================================================
echo.

:: Check Docker
docker info >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Docker Desktop tidak berjalan!
    echo  Silakan buka Docker Desktop terlebih dahulu.
    pause
    exit /b 1
)

echo  [1/4] Membangun images...
docker compose build --parallel
if errorlevel 1 (
    echo  [ERROR] Build gagal. Periksa error di atas.
    pause
    exit /b 1
)

echo.
echo  [2/4] Menjalankan database dulu...
docker compose up -d postgres-main postgres-kc
echo  Menunggu database siap (15 detik)...
timeout /t 15 /nobreak >nul

echo.
echo  [3/4] Menjalankan semua service...
docker compose up -d
if errorlevel 1 (
    echo  [ERROR] Gagal menjalankan service.
    pause
    exit /b 1
)

echo.
echo  [4/4] Menunggu service siap (20 detik)...
timeout /t 20 /nobreak >nul

echo.
echo  ========================================================
echo   SEMUA SERVICE RUNNING!
echo  ========================================================
echo.
echo   DEMO HUB (Landing Page)
echo   http://localhost
echo.
echo   SERVICE LANGSUNG:
echo   Grafana       http://localhost:3000   admin / admin123
echo   Prometheus    http://localhost:9090
echo   pgAdmin       http://localhost:5050   admin@pens.ac.id / admin123
echo   cAdvisor      http://localhost:8081
echo   Keycloak      http://localhost:8180   admin / admin123
echo   Registry UI   http://localhost:8086
echo   Gitea         http://localhost:3001
echo.
echo   API ENDPOINTS:
echo   Health        http://localhost/api/health
echo   Mahasiswa     http://localhost/api/mahasiswa
echo   Stats         http://localhost/api/stats
echo   Log Stats     http://localhost/api/logs/stats
echo   Metrics       http://localhost/api/metrics
echo  ========================================================
echo.

:: Buka browser ke landing page
start "" "http://localhost"

echo  Tekan tombol apa saja untuk melihat status container...
pause >nul
docker compose ps

echo.
echo  Untuk stop semua: jalankan stop-demo.bat
echo.
pause
