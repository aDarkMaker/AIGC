@echo off
chcp 65001 >nul
echo =========================================
echo    LexGuard 法律文本分析系统 一键启动
echo =========================================

:: 检查 Python 是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: 未检测到 Python，请先安装 Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✓ Python 已安装

:: 创建虚拟环境（如果不存在）
if not exist "venv" (
    echo 🔧 创建虚拟环境...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ❌ 创建虚拟环境失败
        pause
        exit /b 1
    )
)

:: 激活虚拟环境
echo 🔧 激活虚拟环境...
call venv\Scripts\activate.bat

:: 升级 pip
echo 🔧 升级 pip...
python -m pip install --upgrade pip

:: 安装依赖
echo 📦 安装基础依赖...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ 安装基础依赖失败
    pause
    exit /b 1
)

echo 📦 安装 RAG 系统依赖...
pip install -r vivo_rag_system\requirements.txt
if %errorlevel% neq 0 (
    echo ❌ 安装 RAG 依赖失败
    pause
    exit /b 1
)

echo 📦 安装 Web 界面依赖...
pip install -r web_interface\requirements.txt
if %errorlevel% neq 0 (
    echo ❌ 安装 Web 依赖失败
    pause
    exit /b 1
)

:: 检查关键文件
echo 🔍 检查系统文件...

if not exist "Law-Train\model\trained_model" (
    echo ❌ 未找到训练好的模型文件
    echo 请确保压缩包包含完整的模型文件
    pause
    exit /b 1
)

if not exist "vivo_rag_system\data" (
    echo ❌ 未找到知识库数据
    echo 请确保压缩包包含完整的知识库数据
    pause
    exit /b 1
)

echo ✓ 系统文件检查完成

:: 初始化知识库（如果需要）
if not exist "vivo_rag_system\data\vector_store" (
    echo 🔧 初始化知识库...
    python vivo_rag_system\scripts\init_knowledge.py
    if %errorlevel% neq 0 (
        echo ❌ 知识库初始化失败
        pause
        exit /b 1
    )
)

:: 启动 Web 服务
echo 🚀 启动 Web 服务...
echo.
echo =========================================
echo  🌐 Web 服务即将启动
echo  📡 访问地址: http://127.0.0.1:5000
echo  🛑 按 Ctrl+C 停止服务
echo =========================================
echo.

cd web_interface
start "" "http://127.0.0.1:5000"
python server.py

pause
