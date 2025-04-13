import os
import json
import numpy as np
import pandas as pd
import jieba as jb
from collections import defaultdict

# init-config-temp
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')
with open(CONFIG_PATH, 'r', encoding='utf-8') as config_file:
    config = json.load(config_file)

KEYWORDS = config["KEYWORDS"]
CONFIDENCE_WEIGHTS = config["CONFIDENCE_WEIGHTS"]
THRESHOLD = config["THRESHOLD"]

def Preprocessing(input_path):
    """文本预处理与格式转换"""
    with open(input_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # 使用jieba进行分词处理
    tokens = jb.lcut(text, cut_all=False)
    
    # 过滤掉空格
    tokens = [token for token in tokens if token.strip()]
    
    # 保存预处理结果
    preprocessed_path = os.path.join('data', 'preprocessed.txt')
    with open(preprocessed_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(tokens))
    
    return tokens

def analyze_tokens(tokens):
    """执行词条分析与分类"""
    keyword_counts = defaultdict(int)
    classified = []
    
    for token in tokens:
        if token in KEYWORDS:
            category = 'keyword'
            keyword_counts[token] += 1
        else:
            category = 'non-keyword'
        classified.append({'token': token, 'category': category})
    
    return classified, dict(keyword_counts)

def confidence_voting(keyword_counts):
    """置信度投票机制"""
    total_weight = 0
    total_keywords = sum(keyword_counts.values())
    
    for kw, count in keyword_counts.items():
        total_weight += CONFIDENCE_WEIGHTS.get(kw, 0.5) * count
    
    avg_confidence = total_weight / total_keywords if total_keywords > 0 else 0
    return avg_confidence, total_keywords

def calculate_privacy_score(confidence, count):
    """计算隐私条款分数"""
    return float(confidence * np.log1p(count)) 

def generate_advice(score):
    """生成指导建议"""
    if score >= THRESHOLD:
        return "高风险：文本包含大量隐私条款要素，建议法务审查"
    else:
        return "低风险：文本隐私条款要素符合常规要求"

def save_results(results, json_path, csv_path):
    """保存结果文件"""
    # 保存JSON格式
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # 转换为CSV格式
    csv_data = {
        'privacy_score': results['privacy_score'],
        'risk_level': 'high' if results['privacy_score'] >= THRESHOLD else 'low',
        'keywords_count': results['total_keywords'],
        'confidence': f"{results['average_confidence']:.2%}",
        'advice': results['advice']
    }
    # 添加关键词统计
    for kw in KEYWORDS:
        csv_data[f'count_{kw}'] = results['keyword_counts'].get(kw, 0)
    
    pd.DataFrame([csv_data]).to_csv(csv_path, index=False, encoding='utf-8-sig')

def process_pipeline(input_path):
    """完整处理流程"""
    os.makedirs('data', exist_ok=True)
    
    # 预处理阶段
    tokens = Preprocessing(input_path)
    
    # 分析阶段
    classified, keyword_counts = analyze_tokens(tokens)
    avg_confidence, total_keywords = confidence_voting(keyword_counts)
    
    # 计算与决策
    privacy_score = calculate_privacy_score(avg_confidence, total_keywords)
    advice = generate_advice(privacy_score)
    
    # 构建结果
    results = {
        'metadata': {
            'source_file': os.path.basename(input_path),
            'token_count': len(tokens)
        },
        'keyword_analysis': {
            'total_keywords': total_keywords,
            'keyword_distribution': keyword_counts,
            'average_confidence': float(avg_confidence),  # 转换numpy类型
        },
        'privacy_score': round(privacy_score, 2),
        'risk_assessment': {
            'threshold': THRESHOLD,
            'is_high_risk': bool(privacy_score >= THRESHOLD),  # 转换为Python bool
            'advice': advice
        },
        'token_details': classified,
        'keyword_counts': keyword_counts,
        'average_confidence': float(avg_confidence),  # 转换numpy类型
        'total_keywords': total_keywords,
        'advice': advice
    }
    
    # 保存输出
    save_results(
        results,
        os.path.join('data', 'analysis_report.json'),
        os.path.join('data', 'summary_report.csv')
    )
    return results

if __name__ == "__main__":
    # 示例用法
    input_file = "sample_privacy.txt"  # 输入文本路径
    process_pipeline(input_file)
    print("analysis completed and results saved.")