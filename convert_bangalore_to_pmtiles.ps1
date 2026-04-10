# ============================================================
# Convert Bangalore GeoJSON files to PMTiles (PowerShell)
# ============================================================

Write-Host "🚀 Starting Bangalore GeoJSON → PMTiles conversion..." -ForegroundColor Cyan
Write-Host ""

# Check if running in WSL is available
$wslAvailable = Get-Command wsl -ErrorAction SilentlyContinue

if ($wslAvailable) {
    Write-Host "✓ WSL detected. Using WSL for conversion..." -ForegroundColor Green
    Write-Host ""
    
    # Run the bash script via WSL
    wsl bash convert_bangalore_to_pmtiles.sh
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ Conversion completed successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "📊 Generated files:" -ForegroundColor Yellow
        Get-ChildItem -Path "maptiles\bangalore_*.pmtiles" -ErrorAction SilentlyContinue | ForEach-Object {
            $size = [math]::Round($_.Length / 1MB, 2)
            Write-Host "  ✓ $($_.Name) - ${size} MB" -ForegroundColor Green
        }
    } else {
        Write-Host ""
        Write-Host "❌ Conversion failed. Check the error messages above." -ForegroundColor Red
    }
} else {
    Write-Host "❌ WSL not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install tippecanoe using one of these methods:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Option 1: Install WSL (Recommended)" -ForegroundColor Cyan
    Write-Host "  1. Open PowerShell as Administrator"
    Write-Host "  2. Run: wsl --install"
    Write-Host "  3. Restart your computer"
    Write-Host "  4. Open Ubuntu from Start Menu"
    Write-Host "  5. Run: sudo apt-get update && sudo apt-get install tippecanoe"
    Write-Host "  6. Run this script again"
    Write-Host ""
    Write-Host "Option 2: Use Docker" -ForegroundColor Cyan
    Write-Host "  docker run -v ${PWD}:/data felt/tippecanoe ..."
    Write-Host ""
    Write-Host "Option 3: Use Online Converter" -ForegroundColor Cyan
    Write-Host "  Visit: https://felt.com/ or https://mapshaper.org/"
    Write-Host ""
}

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
