@echo off
chcp 65001 >nul
python "%~dp0build_viewer.py"
if errorlevel 1 pause & exit /b
start "" "%~dp0도감.html"
