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

class IntegratedAnalysisSystem:
    """集成分析系统"""
    def __init__(self):
        self.rag_engine = RAGEngine()
        self.legal_analyzer = EnhancedAnalyzer()
        
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
    
    def interactive_mode(self):
        """交互式分析模式"""
        print("=== 欢迎使用集成分析系统 ===")
        print("支持的分析领域: privacy(隐私), intellectual_property(知识产权), contract(合同)")
        
        while True:
            print("\n请选择操作:")
            print("1. 分析文本文件")
            print("2. 输入文本进行分析")
            print("3. 退出")
            
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
                    print(f"错误: {str(e)}")
                    
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
                print("感谢使用!")
                break
            else:
                print("无效的选项，请重新选择")

def main():
    parser = argparse.ArgumentParser(description="集成文本分析系统")
    parser.add_argument("--file", "-f", help="要分析的文件路径（可选，默认使用项目根目录下的Target.txt）")
    parser.add_argument("--domain", "-d", default="privacy",
                      choices=["privacy", "intellectual_property", "contract"],
                      help="分析领域 (默认: privacy)")
    parser.add_argument("--interactive", "-i", action="store_true",
                      help="启动交互式模式")
    
    args = parser.parse_args()
    system = IntegratedAnalysisSystem()
    
    if args.interactive:
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