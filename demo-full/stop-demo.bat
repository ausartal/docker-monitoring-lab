@echo off
title Stop Demo Lab
color 0C
echo.
echo  Menghentikan semua service...
docker compose down
echo.
echo  Semua container sudah dihentikan.
echo  Data volume masih tersimpan. Untuk hapus total: docker compose down -v
echo.
pause
