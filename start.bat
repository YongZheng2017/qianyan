@echo off
chcp 65001 >nul 2>&1
title 钱眼投资分析系统 - 一键启动
cd /d "%~dp0"

echo ============================================
echo    钱眼投资分析系统 - 一键启动
echo    (后端 + 管理端 + 分析端)
echo ============================================
echo.

REM ---- 检查 Python 虚拟环境 ----
if not exist ".venv\Scripts\python.exe" (
    echo [错误] 未找到 Python 虚拟环境 .venv
    echo 请先执行：
    echo     python -m venv .venv
    echo     .venv\Scripts\pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

REM ---- 检查 .env 配置 ----
if not exist ".env" (
    echo [警告] 未找到 .env 配置文件！
    echo 请复制 .env.example 为 .env 并配置数据库连接信息。
    echo.
    choice /c YN /m "是否仍然继续启动"
    if errorlevel 2 exit /b 1
)

REM ---- 检查并安装前端依赖 ----
if not exist "src\frontend\admin\node_modules" (
    echo [提示] 管理端前端依赖未安装，正在安装...
    pushd "src\frontend\admin"
    call npm install
    popd
)
if not exist "src\frontend\analysis\node_modules" (
    echo [提示] 分析端前端依赖未安装，正在安装...
    pushd "src\frontend\analysis"
    call npm install
    popd
)

echo.
echo [1/3] 启动后端 FastAPI  (http://localhost:8000) ...
start "后端 FastAPI - 8000" cmd /k "cd /d %~dp0 && .venv\Scripts\python.exe -m uvicorn src.backend.main:app --host 0.0.0.0 --port 8000 --reload"

echo [2/3] 启动管理端前端    (http://localhost:3000) ...
start "管理端 Admin - 3000" cmd /k "cd /d %~dp0src\frontend\admin && npm run dev"

echo [3/3] 启动分析端前端    (http://localhost:5173) ...
start "分析端 Analysis - 5173" cmd /k "cd /d %~dp0src\frontend\analysis && npm run dev"

echo.
echo ============================================
echo    全部服务已启动！
echo --------------------------------------------
echo    后端 API 文档:  http://localhost:8000/docs
echo    管理端:         http://localhost:3000
echo    分析端:         http://localhost:5173
echo    默认账号:        admin / 123456
echo ============================================
echo.
echo  请确保 MySQL 服务已启动。
echo  关闭对应窗口可停止单个服务，或运行 stop.bat 一键全部停止。
echo.
pause