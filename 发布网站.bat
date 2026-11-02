@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo === 发布网站到 GitHub Pages ===
python -X utf8 publish.py
pause
