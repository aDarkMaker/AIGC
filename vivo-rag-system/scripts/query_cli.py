import sys
import os
from pathlib import Path

# 将项目根目录加入Python路径
sys.path.append(str(Path(__file__).parent.parent))

from src.core.rag_engine import RAGEngine

def main():
    engine = RAGEngine()
    while True:
        query = input("\n请输入查询内容（输入q退出）: ")
        if query.lower() == 'q':
            break
            
        result = engine.process_query(query)
        
        print("\n=== 分析结果 ===")
        print(f"关键词: {', '.join(result['keywords'])}")
        print(f"\n摘要: {result['summary']}")
        print(f"\n增强上下文:\n{result['context']}")

if __name__ == "__main__":
    main()