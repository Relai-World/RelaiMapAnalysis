# Start the FastAPI backend server
Write-Host "🚀 Starting FastAPI backend server..." -ForegroundColor Green
Write-Host "📍 Server will run at: http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "📖 API docs available at: http://127.0.0.1:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

uvicorn api:app --reload --host 127.0.0.1 --port 8000
