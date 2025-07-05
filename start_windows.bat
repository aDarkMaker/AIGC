@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

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

:: 升级 pip 和安装构建工具
echo 🔧 升级 pip 和安装构建工具...
python -m pip install --upgrade pip setuptools wheel
if %errorlevel% neq 0 (
    echo ⚠️ 升级工具失败，尝试继续...
)

:: 尝试安装 Microsoft Visual C++ 构建工具（如果需要）
echo 📦 检查并安装构建依赖...
pip install --upgrade pip setuptools wheel
pip install --only-binary=all numpy pandas scikit-learn

:: 安装基础依赖（使用预编译包）
echo 📦 安装基础依赖（使用预编译包）...
pip install --only-binary=all --upgrade -r requirements.txt
if %errorlevel% neq 0 (
    echo ⚠️ 部分基础依赖安装失败，尝试备用方案...
    pip install --upgrade jieba snownlp pyyaml numpy pandas tqdm requests python-dotenv
)

:: 安装 Web 界面依赖（优先预编译包）
echo 📦 安装 Web 界面依赖...
pip install --only-binary=all flask flask-cors werkzeug jinja2
if %errorlevel% neq 0 (
    echo ⚠️ 部分 Web 依赖安装失败，尝试单独安装...
    pip install flask flask-cors
)

:: 尝试安装 RAG 系统依赖（可选）
echo 📦 尝试安装 RAG 系统依赖...
if exist "vivo_rag_system\requirements.txt" (
    pip install --only-binary=all -r vivo_rag_system\requirements.txt
    if %errorlevel% neq 0 (
        echo ⚠️ RAG 依赖安装失败，将使用简化模式...
        echo 系统将在简化模式下运行，部分功能可能不可用
        pip install chromadb sentence-transformers --only-binary=all
        if %errorlevel% neq 0 (
            echo ⚠️ 简化依赖也安装失败，将跳过 RAG 功能
        )
    )
)

:: 检查关键文件
echo 🔍 检查系统文件...

if not exist "web_interface\server.py" (
    echo ❌ 未找到 Web 服务文件
    echo 请确保压缩包解压完整
    pause
    exit /b 1
)

if not exist "analysis_part\analysis.py" (
    echo ❌ 未找到分析模块文件
    echo 请确保压缩包解压完整
    pause
    exit /b 1
)

echo ✓ 基础文件检查完成

:: 创建启动脚本来处理可能的导入错误
echo 🔧 创建错误处理启动器...

echo import sys > temp_start.py
echo import os >> temp_start.py
echo sys.path.insert(0, os.path.abspath('.')) >> temp_start.py
echo. >> temp_start.py
echo try: >> temp_start.py
echo     os.chdir('web_interface') >> temp_start.py
echo     import server >> temp_start.py
echo     server.app.run(host='127.0.0.1', port=5000, debug=False) >> temp_start.py
echo except ImportError as e: >> temp_start.py
echo     print(f"导入错误: {e}") >> temp_start.py
echo     print("正在尝试简化模式...") >> temp_start.py
echo     try: >> temp_start.py
echo         from flask import Flask, render_template_string >> temp_start.py
echo         app = Flask(__name__) >> temp_start.py
echo         @app.route('/') >> temp_start.py
echo         def index(): >> temp_start.py
echo             return '''<!DOCTYPE html^> >> temp_start.py
echo ^<html^>^<head^>^<title^>LexGuard^</title^>^</head^> >> temp_start.py
echo ^<body^>^<h1^>LexGuard 系统^</h1^> >> temp_start.py
echo ^<p^>系统正在简化模式下运行^</p^> >> temp_start.py
echo ^<p^>部分依赖安装失败，请检查网络连接或手动安装依赖^</p^> >> temp_start.py
echo ^</body^>^</html^>''' >> temp_start.py
echo         app.run(host='127.0.0.1', port=5000) >> temp_start.py
echo     except Exception as e2: >> temp_start.py
echo         print(f"启动失败: {e2}") >> temp_start.py
echo         input("按回车键查看解决方案...") >> temp_start.py
echo except Exception as e: >> temp_start.py
echo     print(f"系统错误: {e}") >> temp_start.py
echo     input("按回车键退出...") >> temp_start.py

:: 启动服务
echo 🚀 启动服务...
echo.
echo =========================================
echo  🌐 Web 服务即将启动
echo  📡 访问地址: http://127.0.0.1:5000
echo  🛑 按 Ctrl+C 停止服务
echo =========================================
echo  
echo  如果启动失败，请查看错误信息
echo  或尝试手动安装依赖：
echo  pip install flask flask-cors
echo =========================================
echo.

:: 尝试打开浏览器
timeout /t 3 /nobreak > nul
start "" "http://127.0.0.1:5000" 2>nul

:: 启动服务
python temp_start.py

:: 清理临时文件
if exist "temp_start.py" del "temp_start.py"

echo.
echo 🔧 故障排除建议：
echo 1. 确保网络连接正常
echo 2. 尝试运行：pip install --upgrade pip setuptools wheel
echo 3. 安装 Visual Studio Build Tools（可选）
echo 4. 手动安装核心依赖：pip install flask flask-cors jieba
echo.
pause