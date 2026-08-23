@echo off
chcp 65001 >nul 2>&1
title 钱眼投资分析系统 - 一键停止

echo ============================================
echo    钱眼投资分析系统 - 停止所有服务
echo ============================================
echo.

REM 按端口停止服务（8000=后端, 3000=管理端, 5173=分析端）
for %%p in (8000 3000 5173) do (
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%%p " ^| findstr LISTENING') do (
        echo    停止端口 %%p 的进程 PID %%a
        taskkill /F /PID %%a >nul 2>&1
    )
)

echo.
echo ============================================
echo    所有服务已停止
echo ============================================
echo.
pause