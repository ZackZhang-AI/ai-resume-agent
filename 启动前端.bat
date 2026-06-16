@echo off
chcp 65001 > nul
title 简历优化助手

echo.
echo ============================================
echo         简历优化助手 - 启动中
echo ============================================
echo.

cd /d "%~dp0"

echo [1/2] 检查依赖...
pip show fastapi > nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 依赖未安装，正在安装...
    pip install -r requirements.txt
)

echo [2/2] 启动服务器并打开浏览器...
start "" "http://localhost:8000"
python api_server.py

pause
