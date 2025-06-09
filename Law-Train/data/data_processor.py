import os
import json
from pathlib import Path

class LegalDocProcessor:
    def __init__(self, docs_root, output_dir):
        self.docs_root = Path(docs_root)
        self.output_dir = Path(output_dir)
        self.legal_data = []
        self.processed_count = 0  # 添加计数器
        
    def process_md_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # 获取相对路径作为文档的层级结构
            relative_path = file_path.relative_to(self.docs_root)
            category_path = list(relative_path.parent.parts)
            
            return {
                'content': content,
                'hierarchy': category_path,
                'title': file_path.stem,
                'path': str(relative_path)
            }
    def traverse_docs(self):
        print(f"开始遍历文档目录：{self.docs_root}")
        for file_path in self.docs_root.rglob('*.md'):
            if file_path.is_file():
                doc_data = self.process_md_file(file_path)
                self.legal_data.append(doc_data)
                self.processed_count += 1
                if self.processed_count % 10 == 0:  # 每处理10个文件打印一次进度
                    print(f"已处理 {self.processed_count} 个文件...")
    
    def save_processed_data(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存完整数据
        with open(self.output_dir / 'legal_corpus.json', 'w', encoding='utf-8') as f:
            json.dump(self.legal_data, f, ensure_ascii=False, indent=2)
        
        # 生成纯文本语料库
        with open(self.output_dir / 'corpus.txt', 'w', encoding='utf-8') as f:
            for doc in self.legal_data:
                f.write(f"文档：{doc['title']}\n")
                f.write(f"分类：{'/'.join(doc['hierarchy'])}\n")
                f.write(doc['content'])
                f.write('\n' + '='*50 + '\n')

if __name__ == '__main__':
    docs_dir = Path(__file__).parent.parent / 'docs'
    output_dir = Path(__file__).parent / 'processed'
    
    print(f"文档目录：{docs_dir}")
    print(f"输出目录：{output_dir}")
    
    processor = LegalDocProcessor(docs_dir, output_dir)
    processor.traverse_docs()
    processor.save_processed_data()
    print(f"\n处理完成！共处理了 {processor.processed_count} 个法律文档文件。")
    print(f"数据已保存至：{output_dir}")
