import os
import json
import numpy as np
import pandas as pd
import jieba as jb
from collections import defaultdict
from .legal_analyzer import LegalAnalyzer

# 加载配置
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')
LEGAL_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'legal_config.json')

with open(CONFIG_PATH, 'r', encoding='utf-8') as config_file:
    config = json.load(config_file)

with open(LEGAL_CONFIG_PATH, 'r', encoding='utf-8') as legal_config_file:
    legal_config = json.load(legal_config_file)

KEYWORDS = config["KEYWORDS"]
CONFIDENCE_WEIGHTS = config["CONFIDENCE_WEIGHTS"]
THRESHOLD = config["THRESHOLD"]

class EnhancedAnalyzer:
    def __init__(self):
        self.legal_analyzer = LegalAnalyzer()
        
    def analyze_document(self, text: str, domain: str = 'privacy') -> dict:
        """增强版文档分析"""
        # 基础分析
        tokens = self.preprocess_text(text)
        classified, keyword_counts = self.analyze_tokens(tokens)
        avg_confidence, total_keywords = self.confidence_voting(keyword_counts)
        privacy_score = self.calculate_privacy_score(avg_confidence, total_keywords)
        
        # 法律专业分析
        legal_structure = self.legal_analyzer.analyze_legal_structure(text)
        legal_compliance = self.legal_analyzer.evaluate_legal_compliance(text, domain)
        
        # 合并分析结果
        results = {
            'metadata': {
                'source_text_length': len(text),
                'token_count': len(tokens),
                'structure_info': legal_structure
            },
            'keyword_analysis': {
                'total_keywords': total_keywords,
                'keyword_distribution': keyword_counts,
                'average_confidence': float(avg_confidence)
            },
            'legal_analysis': {
                'compliance': legal_compliance,
                'privacy_score': round(privacy_score, 2),
                'risk_assessment': {
                    'threshold': THRESHOLD,
                    'is_high_risk': bool(privacy_score >= THRESHOLD or legal_compliance['risk_level'] == 'high'),
                }
            }
        }
        
        # 生成专业建议
        results['recommendations'] = self.legal_analyzer.generate_professional_advice({
            **results['legal_analysis'],
            **{'keyword_analysis': results['keyword_analysis']}
        })
        
        return results

    def preprocess_text(self, text: str) -> list:
        """预处理文本"""
        jb.load_userdict(os.path.join(os.path.dirname(__file__), 'legal_terms.txt'))
        return list(jb.cut(text))
    
    def analyze_tokens(self, tokens: list) -> tuple:
        """分析tokens"""
        keyword_counts = defaultdict(int)
        classified = []
        
        for token in tokens:
            # 检查基础关键词
            is_basic_keyword = token in KEYWORDS
            # 检查法律专业词汇
            is_legal_term = any(
                token in term_info['keywords']
                for domain in legal_config['LEGAL_TERMS'].values()
                for term_info in [domain]
            )
            
            if is_basic_keyword or is_legal_term:
                category = 'legal_keyword' if is_legal_term else 'keyword'
                keyword_counts[token] += 1
            else:
                category = 'non-keyword'
                
            classified.append({'token': token, 'category': category})
        
        return classified, dict(keyword_counts)
    
    def confidence_voting(self, keyword_counts: dict) -> tuple:
        """增强版置信度投票"""
        total_weight = 0
        total_keywords = sum(keyword_counts.values())
        
        for kw, count in keyword_counts.items():
            # 基础权重
            base_weight = CONFIDENCE_WEIGHTS.get(kw, 0.5)
            
            # 法律术语额外权重
            legal_weight = 1.0
            for domain, terms in legal_config['LEGAL_TERMS'].items():
                if kw in terms['keywords']:
                    legal_weight = terms['weight']
                    break
            
            total_weight += base_weight * legal_weight * count
        
        avg_confidence = total_weight / total_keywords if total_keywords > 0 else 0
        return avg_confidence, total_keywords
    
    def calculate_privacy_score(self, confidence: float, count: int) -> float:
        """计算综合隐私分数"""
        base_score = confidence * np.log1p(count)
        
        # 根据合规要求调整分数
        if count < 3:  # 关键词过少
            base_score *= 0.8
        elif count > 20:  # 关键词充足
            base_score *= 1.2
            
        return min(base_score, 1.0)  # 确保分数不超过1

def process_pipeline(input_path: str, domain: str = 'privacy') -> dict:
    """增强版处理流程"""
    os.makedirs('data', exist_ok=True)
    
    with open(input_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    analyzer = EnhancedAnalyzer()
    results = analyzer.analyze_document(text, domain)
    
    # 保存结果
    output_base = os.path.splitext(os.path.basename(input_path))[0]
    json_path = f'data/{output_base}_analysis.json'
    csv_path = f'data/{output_base}_analysis.csv'
    
    save_results(results, json_path, csv_path)
    return results

def save_results(results: dict, json_path: str, csv_path: str):
    """保存分析结果"""
    # 保存详细JSON报告
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # 保存CSV摘要
    df = pd.DataFrame({
        '指标': ['文本长度', '关键词数量', '平均置信度', '隐私分数', '合规得分', '风险等级'],
        '数值': [
            results['metadata']['source_text_length'],
            results['keyword_analysis']['total_keywords'],
            round(results['keyword_analysis']['average_confidence'], 3),
            results['legal_analysis']['privacy_score'],
            results['legal_analysis']['compliance']['compliance_score'],
            results['legal_analysis']['compliance']['risk_level']
        ]
    })
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')

if __name__ == "__main__":
    input_file = "sample_privacy.txt"
    results = process_pipeline(input_file)
    print("Analysis completed and results saved.")