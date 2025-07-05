#!/bin/bash
# LexGuard 法律文本分析系统 一键启动脚本

echo "========================================="
echo "   LexGuard 法律文本分析系统 一键启动"
echo "========================================="

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未检测到 Python3，请先安装 Python 3.8+"
    echo "Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
    echo "CentOS/RHEL: sudo yum install python3 python3-pip"
    echo "macOS: brew install python3"
    exit 1
fi

echo "✓ Python3 已安装"

# 检查 pip 是否安装
if ! command -v pip3 &> /dev/null; then
    echo "❌ 错误: 未检测到 pip3"
    echo "请安装 pip3: sudo apt install python3-pip"
    exit 1
fi

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo "🔧 创建虚拟环境..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ 创建虚拟环境失败"
        echo "请确保已安装 python3-venv: sudo apt install python3-venv"
        exit 1
    fi
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 升级 pip
echo "🔧 升级 pip..."
python -m pip install --upgrade pip

# 安装依赖
echo "📦 安装基础依赖..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ 安装基础依赖失败"
    echo "请检查网络连接或尝试使用国内镜像源"
    exit 1
fi

echo "📦 安装 RAG 系统依赖..."
pip install -r vivo_rag_system/requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ 安装 RAG 依赖失败"
    exit 1
fi

echo "📦 安装 Web 界面依赖..."
pip install -r web_interface/requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ 安装 Web 依赖失败"
    exit 1
fi

# 检查关键文件
echo "🔍 检查系统文件..."

if [ ! -d "Law-Train/model/trained_model" ]; then
    echo "❌ 未找到训练好的模型文件"
    echo "请确保压缩包包含完整的模型文件"
    exit 1
fi

if [ ! -d "vivo_rag_system/data" ]; then
    echo "❌ 未找到知识库数据"
    echo "请确保压缩包包含完整的知识库数据"
    exit 1
fi

echo "✓ 系统文件检查完成"

# 初始化知识库（如果需要）
if [ ! -d "vivo_rag_system/data/vector_store" ]; then
    echo "🔧 初始化知识库..."
    python vivo_rag_system/scripts/init_knowledge.py
    if [ $? -ne 0 ]; then
        echo "❌ 知识库初始化失败"
        exit 1
    fi
fi

# 启动 Web 服务
echo "🚀 启动 Web 服务..."
echo ""
echo "========================================="
echo " 🌐 Web 服务即将启动"
echo " 📡 访问地址: http://127.0.0.1:5000"
echo " 🛑 按 Ctrl+C 停止服务"
echo "========================================="
echo ""

cd web_interface

# 尝试自动打开浏览器
if command -v open &> /dev/null; then
    # macOS
    open "http://127.0.0.1:5000" 2>/dev/null &
elif command -v xdg-open &> /dev/null; then
    # Linux
    xdg-open "http://127.0.0.1:5000" 2>/dev/null &
elif command -v firefox &> /dev/null; then
    # 备用方案 - Firefox
    firefox "http://127.0.0.1:5000" 2>/dev/null &
elif command -v google-chrome &> /dev/null; then
    # 备用方案 - Chrome
    google-chrome "http://127.0.0.1:5000" 2>/dev/null &
fi

# 启动服务器
python server.py
