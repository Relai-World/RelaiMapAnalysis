@echo off
REM ============================================================
REM Convert Bangalore GeoJSON files to PMTiles (Windows)
REM ============================================================

echo Starting Bangalore GeoJSON to PMTiles conversion...
echo.

REM Check if tippecanoe is available (via WSL or Docker)
where wsl >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo Using WSL for conversion...
    wsl bash convert_bangalore_to_pmtiles.sh
    exit /b
)

echo.
echo ERROR: tippecanoe not found!
echo.
echo Please install tippecanoe using one of these methods:
echo   1. Install WSL and run: sudo apt-get install tippecanoe
echo   2. Use Docker: docker run -v %cd%:/data felt/tippecanoe
echo   3. Use the online converter at: https://felt.com/
echo.
pause
