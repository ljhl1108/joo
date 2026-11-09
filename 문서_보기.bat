@echo off
chcp 65001 >nul
title OnionCat 문서 보기
python "%~dp0Design\docs_viewer.py"
if errorlevel 1 pause
