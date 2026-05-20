# start_dev.ps1 — Start backend + dashboard together
# Usage: .\start_dev.ps1

$Root = $PSScriptRoot

Write-Host "`n[PR Governance Agent] Starting dev environment...`n" -ForegroundColor Cyan

# Start FastAPI backend in a new window
Start-Process powershell -ArgumentList `
  "-NoExit", `
  "-Command", `
  "cd '$Root\dashboard\server'; Write-Host '[Backend] Starting FastAPI on :8000' -ForegroundColor Yellow; uvicorn server:app --reload --port 8000" `
  -WindowStyle Normal

Start-Sleep -Seconds 2

# Start Vite dev server in a new window
Start-Process powershell -ArgumentList `
  "-NoExit", `
  "-Command", `
  "cd '$Root\dashboard'; Write-Host '[Frontend] Starting Vite on :5173' -ForegroundColor Yellow; npm run dev" `
  -WindowStyle Normal

Write-Host "[PR Governance Agent] Two windows opened:" -ForegroundColor Green
Write-Host "  Backend  -> http://localhost:8000" -ForegroundColor White
Write-Host "  Frontend -> http://localhost:5173" -ForegroundColor White
Write-Host "`nOpen http://localhost:5173 in your browser.`n" -ForegroundColor Cyan
