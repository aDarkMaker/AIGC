#!/usr/bin/env python3
"""
LexGuard 法律文本分析系统 - 跨平台一键启动脚本
支持 Windows, macOS, Linux
"""
import os
import sys
import subprocess
import platform
import webbrowser
import time
from pathlib import Path

class LexGuardInstaller:
    def __init__(self):
        self.system = platform.system()
        self.project_root = Path.cwd()
        self.venv_path = self.project_root / "venv"
        
        # 根据系统类型设置路径
        if self.system == "Windows":
            self.python_exe = self.venv_path / "Scripts" / "python.exe"
            self.pip_exe = self.venv_path / "Scripts" / "pip.exe"
            self.activate_script = self.venv_path / "Scripts" / "activate.bat"
        else:
            self.python_exe = self.venv_path / "bin" / "python"
            self.pip_exe = self.venv_path / "bin" / "pip"
            self.activate_script = self.venv_path / "bin" / "activate"

    def print_banner(self):
        """打印启动横幅"""
        print("=" * 50)
        print("   LexGuard 法律文本分析系统 一键启动")
        print("=" * 50)

    def run_command(self, command, description, check=True):
        """运行命令并处理错误"""
        print(f"🔧 {description}...")
        try:
            if isinstance(command, str):
                result = subprocess.run(command, shell=True, check=check, 
                                      capture_output=True, text=True)
            else:
                result = subprocess.run(command, check=check, 
                                      capture_output=True, text=True)
            
            if result.returncode == 0:
                return True
            else:
                print(f"❌ {description}失败: {result.stderr}")
                return False
        except subprocess.CalledProcessError as e:
            print(f"❌ {description}失败: {e.stderr if e.stderr else str(e)}")
            return False
        except Exception as e:
            print(f"❌ {description}失败: {str(e)}")
            return False

    def check_python(self):
        """检查Python版本"""
        try:
            version = sys.version_info
            if version.major >= 3 and version.minor >= 8:
                print(f"✓ Python {version.major}.{version.minor} 已安装")
                return True
            else:
                print(f"❌ Python版本过低: {version.major}.{version.minor}")
                print("请安装 Python 3.8+")
                return False
        except Exception as e:
            print(f"❌ Python检查失败: {str(e)}")
            return False

    def check_required_files(self):
        """检查必要文件"""
        print("🔍 检查系统文件...")
        
        required_paths = [
            "requirements.txt",
            "vivo_rag_system/requirements.txt", 
            "web_interface/requirements.txt",
            "web_interface/server.py"
        ]
        
        optional_paths = [
            ("Law-Train/model/trained_model", "训练好的模型文件"),
            ("vivo_rag_system/data", "知识库数据目录")
        ]
        
        # 检查必需文件
        missing_files = []
        for path in required_paths:
            if not Path(path).exists():
                missing_files.append(path)
        
        if missing_files:
            print("❌ 缺少必要文件:")
            for file in missing_files:
                print(f"   - {file}")
            return False
        
        # 检查可选文件
        for path, description in optional_paths:
            if Path(path).exists():
                print(f"✓ {description} 已存在")
            else:
                print(f"⚠️  {description} 不存在，可能需要后续初始化")
        
        print("✓ 系统文件检查完成")
        return True

    def create_virtual_environment(self):
        """创建虚拟环境"""
        if self.venv_path.exists():
            print("✓ 虚拟环境已存在")
            return True
        
        print("🔧 创建虚拟环境...")
        return self.run_command([sys.executable, "-m", "venv", str(self.venv_path)], 
                               "创建虚拟环境")

    def install_dependencies(self):
        """安装依赖包"""
        # 升级pip
        if not self.run_command([str(self.python_exe), "-m", "pip", "install", "--upgrade", "pip"], 
                                "升级pip"):
            return False
        
        # 安装各模块依赖
        dependencies = [
            ("requirements.txt", "基础依赖"),
            ("vivo_rag_system/requirements.txt", "RAG系统依赖"),
            ("web_interface/requirements.txt", "Web界面依赖")
        ]
        
        for dep_file, description in dependencies:
            if Path(dep_file).exists():
                if not self.run_command([str(self.python_exe), "-m", "pip", "install", 
                                        "-r", dep_file], f"安装{description}"):
                    return False
            else:
                print(f"⚠️  {dep_file} 不存在，跳过")
        
        return True

    def initialize_knowledge_base(self):
        """初始化知识库"""
        vector_store_path = Path("vivo_rag_system/data/vector_store")
        init_script = Path("vivo_rag_system/scripts/init_knowledge.py")
        
        if vector_store_path.exists():
            print("✓ 知识库已初始化")
            return True
        
        if init_script.exists():
            print("🔧 初始化知识库...")
            return self.run_command([str(self.python_exe), str(init_script)], 
                                   "初始化知识库", check=False)
        else:
            print("⚠️  知识库初始化脚本不存在，跳过初始化")
            return True

    def start_web_service(self):
        """启动Web服务"""
        print("🚀 启动Web服务...")
        print("")
        print("=" * 50)
        print(" 🌐 Web服务即将启动")
        print(" 📡 访问地址: http://127.0.0.1:5000")
        print(" 🛑 按 Ctrl+C 停止服务")
        print("=" * 50)
        print("")
        
        # 延迟打开浏览器
        def open_browser():
            time.sleep(2)  # 等待服务器启动
            try:
                webbrowser.open("http://127.0.0.1:5000", new=2)
            except Exception as e:
                print(f"⚠️  自动打开浏览器失败: {e}")
        
        # 在后台线程中打开浏览器
        import threading
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        # 切换到web_interface目录并启动服务
        web_dir = self.project_root / "web_interface"
        if not web_dir.exists():
            print("❌ web_interface 目录不存在")
            return False
        
        os.chdir(web_dir)
        
        try:
            subprocess.run([str(self.python_exe), "server.py"], check=True)
        except KeyboardInterrupt:
            print("\n🛑 服务已停止")
            return True
        except Exception as e:
            print(f"❌ 启动服务失败: {e}")
            return False

    def run(self):
        """主运行流程"""
        self.print_banner()
        
        try:
            # 检查环境
            if not self.check_python():
                input("按回车键退出...")
                return False
            
            if not self.check_required_files():
                input("按回车键退出...")
                return False
            
            # 设置环境
            if not self.create_virtual_environment():
                input("按回车键退出...")
                return False
            
            if not self.install_dependencies():
                input("按回车键退出...")
                return False
            
            # 初始化
            self.initialize_knowledge_base()
            
            # 启动服务
            return self.start_web_service()
            
        except KeyboardInterrupt:
            print("\n👋 用户取消操作")
            return False
        except Exception as e:
            print(f"❌ 发生未知错误: {e}")
            input("按回车键退出...")
            return False

def main():
    """主函数"""
    installer = LexGuardInstaller()
    success = installer.run()
    
    if not success:
        print("❌ 启动失败")
        if platform.system() == "Windows":
            input("按回车键退出...")
    else:
        print("✓ 启动成功")

if __name__ == "__main__":
    main()
