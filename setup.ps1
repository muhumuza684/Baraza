# Baraza setup script for Windows PowerShell
# Run from the project root: .\setup.ps1

Write-Host "== Baraza setup ==" -ForegroundColor Cyan

# --- Backend ---
Write-Host "`nSetting up backend (Python/FastAPI)..." -ForegroundColor Yellow
Push-Location backend

if (-not (Test-Path ".venv")) {
    python -m venv .venv
}
& ".\.venv\Scripts\Activate.ps1"

pip install --upgrade pip | Out-Null
pip install -r requirements.txt

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created backend\.env from .env.example" -ForegroundColor Green
}

Write-Host "Seeding demo data..." -ForegroundColor Yellow
python seed.py

Pop-Location

# --- Frontend ---
Write-Host "`nSetting up frontend (React/Vite)..." -ForegroundColor Yellow
Push-Location frontend
npm install
Pop-Location

Write-Host "`n== Setup complete ==" -ForegroundColor Cyan
Write-Host "To run it (use two terminals):"
Write-Host "  1) Backend:  cd backend; .\.venv\Scripts\Activate.ps1; uvicorn app.main:app --reload"
Write-Host "  2) Frontend: cd frontend; npm run dev"
Write-Host "`nThen open http://localhost:5173"
Write-Host "Demo logins -> student: bright@must.ac.ug / password123   lecturer: lecturer@must.ac.ug / password123"
