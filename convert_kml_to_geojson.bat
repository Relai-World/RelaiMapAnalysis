@echo off
REM Convert KML to GeoJSON using ogr2ogr

echo Converting KML to GeoJSON...

set INPUT_KML=frontend\data\e56d21e8-0c44-4c35-9e5d-c732f6f59c97.kml
set OUTPUT_GEOJSON=frontend\data\converted_from_kml.geojson

REM Check if ogr2ogr is available
where ogr2ogr >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ogr2ogr not found. Please install GDAL/OSGeo4W
    echo Download from: https://trac.osgeo.org/osgeo4w/
    exit /b 1
)

REM Convert KML to GeoJSON
ogr2ogr -f GeoJSON "%OUTPUT_GEOJSON%" "%INPUT_KML%"

if %ERRORLEVEL% EQU 0 (
    echo Conversion successful!
    echo Output: %OUTPUT_GEOJSON%
    dir "%OUTPUT_GEOJSON%"
) else (
    echo Conversion failed
    exit /b 1
)
