@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
echo === 증시키워드 자동 포스팅 시작 ===
python post_stock.py
echo.
pause
