# RetailSense Application Launcher
# This script activates the virtual environment and starts the Streamlit dashboard

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  RetailSense - Data Ingestion Module" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
.\venv\Scripts\Activate.ps1

# Set Python path
$env:PYTHONPATH = $PWD

# Start Streamlit
Write-Host "Starting Streamlit dashboard..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Dashboard will open in your browser at http://localhost:8501" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Gray
Write-Host ""

streamlit run app.py
