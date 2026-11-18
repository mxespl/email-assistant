@echo off
cd /d "%~dp0"
set PYTHONUTF8=1
echo ===== %date% %time% ===== >> run_log.txt
"venv\Scripts\python.exe" daily.py >> run_log.txt 2>&1
start "" "daily_overview.html"