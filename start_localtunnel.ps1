# Flask 서버와 LocalTunnel을 동시에 실행

Write-Host "=== 졸업학점 관리 시스템 시작 (LocalTunnel) ===" -ForegroundColor Cyan
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

# LocalTunnel 실행
Write-Host ""
Write-Host "LocalTunnel 시작 중..." -ForegroundColor Yellow
Write-Host "고정 URL: https://ocu-graduation.loca.lt" -ForegroundColor Green
Write-Host ""
Write-Host "※ 처음 접속 시 'Continue' 버튼을 클릭하세요" -ForegroundColor Yellow
Write-Host ""

npx localtunnel --port 5000 --subdomain ocu-graduation --print-requests
