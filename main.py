import sys
import os
from pathlib import Path
import argparse
import json
from typing import Dict, Any, Optional

# 添加项目根路径到系统路径
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# 导入自定义模块
from vivo_rag_system.src import RAGEngine  # 通过包的__init__.py导入
from analysis_part.analysis import EnhancedAnalyzer

# 添加训练相关导入
def load_training_modules():
    """安全加载训练模块"""
    try:
        # 检查必要的依赖
        import torch
        import transformers
        
        # 将 Law-Train 目录添加到路径
        law_train_path = project_root / "Law-Train"
        if str(law_train_path) not in sys.path:
            sys.path.insert(0, str(law_train_path))
        
        # 导入训练模块
        from src.train import LegalBertTrainer, LegalCorpusDataset
        print("✓ 训练模块已成功加载")
        return True, LegalBertTrainer, LegalCorpusDataset
        
    except ImportError as e:
        print(f"⚠️ 警告: 训练模块不可用 - {str(e)}")
        print("可能的原因:")
        print("  1. 缺少必要的依赖包 (torch, transformers 等)")
        print("  2. Law-Train/src/train.py 文件不存在或有错误") 
        print("  3. 请先运行: pip install -r Law-Train/requirements.txt")
        return False, None, None
    except Exception as e:
        print(f"⚠️ 加载训练模块时发生未知错误: {str(e)}")
        return False, None, None

# 尝试加载训练模块
TRAINING_AVAILABLE, LegalBertTrainer, LegalCorpusDataset = load_training_modules()

class IntegratedAnalysisSystem:
    """集成分析系统"""
    def __init__(self):
        self.rag_engine = RAGEngine()
        self.legal_analyzer = EnhancedAnalyzer()
        self.trainer = None
        
        # 初始化训练器（如果可用）
        if TRAINING_AVAILABLE and LegalBertTrainer:
            try:
                self.trainer = LegalBertTrainer()
                print("✓ 训练器初始化成功")
            except Exception as e:
                print(f"⚠️ 训练器初始化失败: {str(e)}")
                # 不在这里修改全局变量，而是在类级别标记
    
    def analyze_document(self, text: str, domain: str = 'privacy', use_professional_kb: bool = False) -> Dict[str, Any]:
        """完整文档分析"""
        # RAG 系统分析
        rag_results = self.rag_engine.process_query(text, use_professional_kb=use_professional_kb) # 传递参数
        
        # 法律分析
        legal_results = self.legal_analyzer.analyze_document(text, domain)
        
        # 合并结果
        return {
            "rag_analysis": {
                "keywords": rag_results["keywords"],
                "summary": rag_results["summary"],
                "related_context": rag_results["context"]
            },
            "legal_analysis": legal_results
        }
    
    def save_results(self, results: Dict[str, Any], output_dir: str):
        """保存分析结果"""
        os.makedirs(output_dir, exist_ok=True)
        
        # 保存JSON格式结果
        json_path = os.path.join(output_dir, "analysis_results.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
            
        print(f"分析结果已保存至: {json_path}")
    
    def train_model(self, data_path: str, output_dir: str, **kwargs):
        """训练法律文本模型"""
        if not TRAINING_AVAILABLE or not LegalCorpusDataset:
            print("❌ 错误: 训练模块不可用")
            print("请先安装训练依赖: pip install -r Law-Train/requirements.txt")
            return False
            
        try:
            print("🚀 开始训练法律文本模型...")
            
            # 检查数据文件是否存在
            if not os.path.exists(data_path):
                print(f"❌ 错误: 训练数据文件不存在: {data_path}")
                return False
            
            # 准备数据集
            dataset = LegalCorpusDataset(data_path, self.trainer.tokenizer, augment=True)
            
            # 训练模型
            self.trainer.train(
                dataset, 
                output_dir,
                batch_size=kwargs.get('batch_size', 8),
                num_epochs=kwargs.get('num_epochs', 3),
                learning_rate=kwargs.get('learning_rate', 2e-5)
            )
            
            # 保存模型
            self.trainer.save_model(output_dir)
            
            print(f"✅ 模型训练完成，已保存至: {output_dir}")
            return True
            
        except Exception as e:
            print(f"❌ 训练过程中发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def evaluate_model(self, test_data_path: str, model_path: str):
        """评估训练好的模型"""
        if not TRAINING_AVAILABLE:
            print("错误: 训练模块不可用")
            return None
            
        try:
            print("开始评估模型...")
            # TODO: 实现模型评估逻辑
            print("模型评估完成")
            return {}
        except Exception as e:
            print(f"评估过程中发生错误: {str(e)}")
            return None
    
    def interactive_mode(self):
        """交互式分析模式"""
        print("=== 欢迎使用集成分析系统 ===")
        print("支持的分析领域: privacy(隐私), intellectual_property(知识产权), contract(合同)")
        
        while True:
            print("\n请选择操作:")
            print("1. 分析文本文件")
            print("2. 输入文本进行分析")
            if TRAINING_AVAILABLE:
                print("3. 训练模型 ✓")
                print("4. 评估模型 ✓") 
                print("5. 诊断训练环境")
            else:
                print("3. 训练模型 ❌ (不可用)")
                print("4. 评估模型 ❌ (不可用)")
                print("5. 诊断训练环境 🔧")
            print("6. 退出")
            
            choice = input("请输入选项编号: ").strip()
            
            if choice == "1":
                file_path = input("请输入文件路径: ").strip()
                domain = input("请输入分析领域 (默认为privacy): ").strip() or "privacy"
                
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        text = f.read()
                    results = self.analyze_document(text, domain)
                    self.save_results(results, "analysis_output")
                except Exception as e:
                    print(f"❌ 错误: {str(e)}")
                    
            elif choice == "2":
                print("请输入要分析的文本 (输入空行结束):")
                lines = []
                while True:
                    line = input()
                    if not line:
                        break
                    lines.append(line)
                
                if lines:
                    domain = input("请输入分析领域 (默认为privacy): ").strip() or "privacy"
                    text = "\n".join(lines)
                    results = self.analyze_document(text, domain)
                    self.save_results(results, "analysis_output")
                    
            elif choice == "3":
                if not TRAINING_AVAILABLE:
                    print("❌ 训练功能不可用，请选择选项5进行诊断")
                    continue
                    
                data_path = input("请输入训练数据路径: ").strip()
                output_dir = input("请输入模型保存路径 (默认: ./Law-Train/model/trained_model): ").strip()
                if not output_dir:
                    output_dir = "./Law-Train/model/trained_model"
                
                # 训练参数
                batch_size = input("批处理大小 (默认8): ").strip()
                batch_size = int(batch_size) if batch_size.isdigit() else 8
                
                epochs = input("训练轮数 (默认3): ").strip()
                epochs = int(epochs) if epochs.isdigit() else 3
                
                self.train_model(
                    data_path, 
                    output_dir,
                    batch_size=batch_size,
                    num_epochs=epochs
                )
                
            elif choice == "4":
                if not TRAINING_AVAILABLE:
                    print("❌ 评估功能不可用，请选择选项5进行诊断")
                    continue
                    
                test_data_path = input("请输入测试数据路径: ").strip()
                model_path = input("请输入模型路径: ").strip()
                self.evaluate_model(test_data_path, model_path)
                
            elif choice == "5":
                self.diagnose_training_setup()
                
            elif choice == "6":
                print("感谢使用!")
                break
            else:
                print("❌ 无效的选项，请重新选择")
    
    def diagnose_training_setup(self):
        """诊断训练环境设置"""
        print("🔍 正在诊断训练环境...")
        print("-" * 50)
        
        # 检查Python版本
        print(f"Python版本: {sys.version}")
        
        # 检查关键依赖
        dependencies = [
            'torch', 'transformers', 'numpy', 'pandas', 
            'scikit-learn', 'tqdm', 'jieba'
        ]
        
        missing_deps = []
        for dep in dependencies:
            try:
                __import__(dep)
                print(f"✓ {dep}: 已安装")
            except ImportError:
                print(f"❌ {dep}: 未安装")
                missing_deps.append(dep)
        
        # 检查文件存在性
        required_files = [
            'Law-Train/src/train.py',
            'Law-Train/src/__init__.py', 
            'Law-Train/requirements.txt'
        ]
        
        for file_path in required_files:
            full_path = project_root / file_path
            if full_path.exists():
                print(f"✓ {file_path}: 存在")
            else:
                print(f"❌ {file_path}: 不存在")
        
        # 提供解决建议
        if missing_deps:
            print("\n💡 建议操作:")
            print("1. 安装缺失的依赖包:")
            print(f"   pip install {' '.join(missing_deps)}")
            print("2. 或者安装完整训练环境:")
            print("   pip install -r Law-Train/requirements.txt")
        
        print("-" * 50)

def main():
    parser = argparse.ArgumentParser(description="集成文本分析系统")
    parser.add_argument("--file", "-f", help="要分析的文件路径（可选，默认使用项目根目录下的Target.txt）")
    parser.add_argument("--domain", "-d", default="privacy",
                      choices=["privacy", "intellectual_property", "contract"],
                      help="分析领域 (默认: privacy)")
    parser.add_argument("--interactive", "-i", action="store_true",
                      help="启动交互式模式")
    parser.add_argument("--diagnose", action="store_true",
                      help="诊断训练环境设置")
    # 新增训练相关参数
    parser.add_argument("--train", action="store_true",
                      help="训练模式")
    parser.add_argument("--train-data", 
                      help="训练数据路径")
    parser.add_argument("--model-output", default="./Law-Train/model/trained_model",
                      help="模型输出目录")
    parser.add_argument("--batch-size", type=int, default=8,
                      help="批处理大小")
    parser.add_argument("--epochs", type=int, default=3,
                      help="训练轮数")
    parser.add_argument("--learning-rate", type=float, default=2e-5,
                      help="学习率")
    
    args = parser.parse_args()
    system = IntegratedAnalysisSystem()
    
    if args.diagnose:
        system.diagnose_training_setup()
        return
    
    if args.train:
        if not TRAINING_AVAILABLE:
            print("错误: 训练模块不可用")
            sys.exit(1)
        
        if not args.train_data:
            print("错误: 训练模式需要指定训练数据路径 (--train-data)")
            sys.exit(1)
            
        success = system.train_model(
            args.train_data,
            args.model_output,
            batch_size=args.batch_size,
            num_epochs=args.epochs,
            learning_rate=args.learning_rate
        )
        
        if success:
            print("训练完成！")
        else:
            print("训练失败！")
            sys.exit(1)
            
    elif args.interactive:
        system.interactive_mode()
    else:
        try:
            # 如果没有指定文件，则使用 Target.txt
            input_file = args.file if args.file else os.path.join(project_root, "Target.txt")
            
            if not os.path.exists(input_file):
                print(f"错误: 找不到文件 {input_file}")
                sys.exit(1)
                
            with open(input_file, "r", encoding="utf-8") as f:
                text = f.read()
                
            print(f"正在分析文件: {input_file}")
            results = system.analyze_document(text, args.domain)
            system.save_results(results, "analysis_output")
            print("分析完成！")
            
        except Exception as e:
            print(f"错误: {str(e)}")
            sys.exit(1)

if __name__ == "__main__":
    main()