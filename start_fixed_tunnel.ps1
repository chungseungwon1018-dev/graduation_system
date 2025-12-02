# Flask 서버와 Cloudflare Named Tunnel을 동시에 실행

Write-Host "=== 졸업학점 관리 시스템 시작 ===" -ForegroundColor Cyan
Write-Host ""

# 가상환경 활성화
Write-Host "가상환경 활성화 중..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Flask 서버 백그라운드 실행
Write-Host "Flask 서버 시작 중..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .\venv\Scripts\Activate.ps1; python main_app.py" -WindowStyle Normal

# Flask 서버 시작 대기
Write-Host "서버 준비 중... (5초 대기)" -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Cloudflare Named Tunnel 실행
Write-Host ""
Write-Host "Cloudflare Tunnel 시작 중..." -ForegroundColor Yellow
Write-Host "고정 URL로 접속 가능합니다" -ForegroundColor Green
Write-Host ""

.\cloudflared.exe tunnel run graduation-system
