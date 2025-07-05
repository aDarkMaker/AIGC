import os
import json
import numpy as np
import pandas as pd
import jieba as jb
from collections import defaultdict
from .legal_analyzer import LegalAnalyzer
import re
from typing import Dict, List, Tuple, Optional

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

class DocumentScoringSystem:
    """重构的文档打分系统"""
    
    def __init__(self):
        self.scoring_weights = {
            'content_quality': 0.25,      # 内容质量
            'legal_compliance': 0.30,     # 法律合规性  
            'completeness': 0.25,         # 完整性
            'clarity': 0.20               # 清晰度
        }
        
        # 严格的评分标准
        self.scoring_criteria = {
            'excellent': (0.9, 1.0),      # 90-100%
            'good': (0.75, 0.89),         # 75-89%
            'fair': (0.6, 0.74),          # 60-74%
            'poor': (0.4, 0.59),          # 40-59%
            'very_poor': (0.0, 0.39)      # 0-39%
        }
        
    def calculate_content_quality_score(self, text: str, tokens: List[str]) -> Dict[str, float]:
        """计算内容质量分数"""
        if len(text) < 50:
            return {'score': 0.1, 'reason': '文档过短，内容不足'}
        
        # 关键要素检查
        essential_elements = {
            'purpose_statement': ['目的', '宗旨', '用途', '说明'],
            'scope_definition': ['范围', '适用', '涵盖', '包括'],
            'detailed_provisions': ['条款', '规定', '要求', '标准'],
            'responsibilities': ['责任', '义务', '职责', '承担']
        }
        
        found_elements = 0
        total_elements = len(essential_elements)
        
        for element_type, keywords in essential_elements.items():
            if any(keyword in text for keyword in keywords):
                found_elements += 1
        
        # 内容丰富度评分
        content_richness = found_elements / total_elements
        
        # 文本长度合理性
        length_score = self._calculate_length_score(len(text))
        
        # 专业术语密度
        professional_terms = self._count_professional_terms(tokens)
        term_density = min(professional_terms / len(tokens), 0.1) * 10 if tokens else 0
        
        final_score = (content_richness * 0.5 + length_score * 0.3 + term_density * 0.2)
        
        return {
            'score': round(final_score, 3),
            'content_richness': content_richness,
            'length_score': length_score,
            'term_density': term_density,
            'found_elements': found_elements,
            'total_elements': total_elements
        }
    
    def calculate_legal_compliance_score(self, text: str, domain: str) -> Dict[str, float]:
        """计算法律合规性分数"""
        compliance_requirements = {
            'privacy': {
                'mandatory': ['个人信息', '隐私政策', '数据处理', '用户同意'],
                'recommended': ['数据安全', '第三方共享', '用户权利', '联系方式'],
                'penalties': ['泄露', '滥用', '未授权']
            },
            'contract': {
                'mandatory': ['甲方', '乙方', '合同期限', '违约责任'],
                'recommended': ['争议解决', '法律适用', '合同变更', '终止条件'],
                'penalties': ['违约', '赔偿', '解除']
            },
            'intellectual_property': {
                'mandatory': ['知识产权', '版权', '专利', '商标'],
                'recommended': ['授权许可', '侵权责任', '保护措施', '使用限制'],
                'penalties': ['侵权', '盗用', '抄袭']
            }
        }
        
        if domain not in compliance_requirements:
            return {'score': 0.5, 'reason': f'未知领域: {domain}'}
        
        requirements = compliance_requirements[domain]
        
        # 强制要求检查
        mandatory_found = sum(1 for req in requirements['mandatory'] if req in text)
        mandatory_score = mandatory_found / len(requirements['mandatory'])
        
        # 推荐要求检查  
        recommended_found = sum(1 for req in requirements['recommended'] if req in text)
        recommended_score = recommended_found / len(requirements['recommended'])
        
        # 风险条款检查（扣分项）
        penalty_found = sum(1 for penalty in requirements['penalties'] if penalty in text)
        penalty_deduction = min(penalty_found * 0.1, 0.3)  # 最多扣30%
        
        # 综合合规分数
        base_score = mandatory_score * 0.7 + recommended_score * 0.3
        final_score = max(0, base_score - penalty_deduction)
        
        return {
            'score': round(final_score, 3),
            'mandatory_score': mandatory_score,
            'recommended_score': recommended_score,
            'penalty_deduction': penalty_deduction,
            'mandatory_found': mandatory_found,
            'recommended_found': recommended_found,
            'penalty_found': penalty_found
        }
    
    def calculate_completeness_score(self, text: str, domain: str) -> Dict[str, float]:
        """计算完整性分数"""
        # 基于文档结构的完整性评估
        structure_elements = {
            'title': ['标题', '名称', '政策', '协议', '合同'],
            'introduction': ['前言', '引言', '说明', '概述'],
            'main_content': ['条款', '内容', '规定', '要求'],
            'conclusion': ['结论', '生效', '联系', '附则']
        }
        
        found_structures = 0
        for structure_type, keywords in structure_elements.items():
            if any(keyword in text for keyword in keywords):
                found_structures += 1
        
        structure_score = found_structures / len(structure_elements)
        
        # 内容深度评估
        depth_indicators = ['详细', '具体', '明确', '包括但不限于', '例如']
        depth_count = sum(1 for indicator in depth_indicators if indicator in text)
        depth_score = min(depth_count / 3, 1.0)  # 最多3个深度指标得满分
        
        # 覆盖面评估（基于文档长度和复杂度）
        coverage_score = self._calculate_coverage_score(text)
        
        final_score = structure_score * 0.4 + depth_score * 0.3 + coverage_score * 0.3
        
        return {
            'score': round(final_score, 3),
            'structure_score': structure_score,
            'depth_score': depth_score,
            'coverage_score': coverage_score,
            'found_structures': found_structures
        }
    
    def calculate_clarity_score(self, text: str, tokens: List[str]) -> Dict[str, float]:
        """计算清晰度分数"""
        if not tokens:
            return {'score': 0.0, 'reason': '无有效文本'}
        
        # 句子长度合理性
        sentences = re.split(r'[。！？；]', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return {'score': 0.0, 'reason': '无有效句子'}
        
        avg_sentence_length = len(tokens) / len(sentences)
        # 理想句长15-25字
        length_clarity = 1.0 - abs(avg_sentence_length - 20) / 20
        length_clarity = max(0, min(1, length_clarity))
        
        # 词汇复杂度
        unique_tokens = set(tokens)
        vocabulary_complexity = len(unique_tokens) / len(tokens)
        # 适中的词汇复杂度更好
        complexity_clarity = 1.0 - abs(vocabulary_complexity - 0.6) / 0.6
        complexity_clarity = max(0, min(1, complexity_clarity))
        
        # 连接词使用情况
        connectors = ['但是', '然而', '因此', '所以', '而且', '并且', '或者', '以及']
        connector_count = sum(1 for token in tokens if token in connectors)
        connector_score = min(connector_count / len(sentences), 0.3) / 0.3
        
        final_score = length_clarity * 0.4 + complexity_clarity * 0.4 + connector_score * 0.2
        
        return {
            'score': round(final_score, 3),
            'length_clarity': length_clarity,
            'complexity_clarity': complexity_clarity,
            'connector_score': connector_score,
            'avg_sentence_length': avg_sentence_length,
            'vocabulary_complexity': vocabulary_complexity
        }
    
    def _calculate_length_score(self, text_length: int) -> float:
        """根据文本长度计算分数"""
        if text_length < 100:
            return 0.2  # 太短
        elif text_length < 500:
            return 0.6  # 较短
        elif text_length < 2000:
            return 1.0  # 适中
        elif text_length < 5000:
            return 0.8  # 较长
        else:
            return 0.6  # 太长
    
    def _count_professional_terms(self, tokens: List[str]) -> int:
        """统计专业术语数量"""
        professional_terms = set()
        # 加载法律专业术语
        for domain, terms in legal_config['LEGAL_TERMS'].items():
            professional_terms.update(terms.get('keywords', []))
        
        return sum(1 for token in tokens if token in professional_terms)
    
    def _calculate_coverage_score(self, text: str) -> float:
        """计算覆盖面分数"""
        # 基于关键主题的覆盖程度
        key_topics = ['权利', '义务', '责任', '程序', '标准', '要求', '禁止', '允许']
        covered_topics = sum(1 for topic in key_topics if topic in text)
        return covered_topics / len(key_topics)
    
    def generate_comprehensive_score(self, text: str, domain: str, tokens: List[str]) -> Dict:
        """生成综合评分"""
        # 计算各维度分数
        content_quality = self.calculate_content_quality_score(text, tokens)
        legal_compliance = self.calculate_legal_compliance_score(text, domain)
        completeness = self.calculate_completeness_score(text, domain)
        clarity = self.calculate_clarity_score(text, tokens)
        
        # 计算加权总分
        total_score = (
            content_quality['score'] * self.scoring_weights['content_quality'] +
            legal_compliance['score'] * self.scoring_weights['legal_compliance'] +
            completeness['score'] * self.scoring_weights['completeness'] +
            clarity['score'] * self.scoring_weights['clarity']
        )
        
        # 确定评级
        grade = self._get_grade(total_score)
        
        return {
            'total_score': round(total_score, 3),
            'percentage': round(total_score * 100, 1),
            'grade': grade,
            'detailed_scores': {
                'content_quality': content_quality,
                'legal_compliance': legal_compliance,
                'completeness': completeness,
                'clarity': clarity
            },
            'scoring_weights': self.scoring_weights,
            'recommendations': self._generate_recommendations(content_quality, legal_compliance, completeness, clarity)
        }
    
    def _get_grade(self, score: float) -> str:
        """根据分数获取等级"""
        for grade, (min_score, max_score) in self.scoring_criteria.items():
            if min_score <= score <= max_score:
                return grade
        return 'very_poor'
    
    def _generate_recommendations(self, content, compliance, completeness, clarity) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        if content['score'] < 0.6:
            recommendations.append("建议丰富文档内容，增加更多必要的条款和说明")
        
        if compliance['score'] < 0.7:
            recommendations.append("建议加强法律合规性，补充必要的法律条款")
        
        if completeness['score'] < 0.6:
            recommendations.append("建议完善文档结构，确保包含所有必要部分")
        
        if clarity['score'] < 0.6:
            recommendations.append("建议提高文档清晰度，优化语言表达")
        
        if not recommendations:
            recommendations.append("文档质量良好，建议定期审查更新")
        
        return recommendations
        
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
        
        # 多维度分析
        multi_analysis = self.multi_dimensional_analysis(text, domain)
        
        # 合并分析结果
        results = {
            'metadata': {
                'source_text_length': len(text),
                'token_count': len(tokens),
                'structure_info': legal_structure,
                'analysis_domain': domain,
                'analysis_timestamp': pd.Timestamp.now().isoformat()
            },
            'keyword_analysis': {
                'total_keywords': total_keywords,
                'keyword_distribution': keyword_counts,
                'average_confidence': float(avg_confidence)
            },
            'text_analysis': multi_analysis['text_analysis'],
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
        # 从 legal_compliance 中提取正确的字段名
        professional_advice_input = {
            'compliance_score': legal_compliance.get('compliance_score'),
            'missing_sections': legal_compliance.get('missing_sections'),
            'found_sections_details': legal_compliance.get('found_sections_details'), 
            'applicable_laws': legal_compliance.get('applicable_laws'),
            'risk_level': legal_compliance.get('risk_level')
        }
        advice_details = self.legal_analyzer.generate_professional_advice(professional_advice_input, domain)
        results['recommendations'] = advice_details
        
        return results
        
    def _calculate_analysis_quality(self, keyword_count: int, complexity_score: float, compliance_score: float) -> float:
        """计算分析质量分数"""
        # 权重分配
        keyword_weight = 0.3
        complexity_weight = 0.3
        compliance_weight = 0.4
        
        # 标准化各项分数
        keyword_score = min(keyword_count / 20, 1.0)  # 假设20个关键词为满分
        
        quality_score = (
            keyword_score * keyword_weight +
            complexity_score * complexity_weight +
            compliance_score * compliance_weight
        )
        
        return round(quality_score, 3)

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
    
    def enhanced_text_preprocessing(self, text: str) -> Dict[str, any]:
        """增强版文本预处理"""
        # 文本清洗
        cleaned_text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9，。！？；：""''（）【】《》、]', '', text)
        
        # 分句
        sentences = re.split(r'[。！？；]', cleaned_text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # 分词
        tokens = list(jb.cut(cleaned_text))
        
        return {
            'original_text': text,
            'cleaned_text': cleaned_text,
            'sentences': sentences,
            'tokens': tokens,
            'sentence_count': len(sentences),
            'token_count': len(tokens)
        }
        
    def _is_legal_term(self, token: str) -> bool:
        """判断是否为法律术语"""
        for domain_terms in self.professional_terms.values():
            if any(term in token for term in domain_terms):
                return True
        return token in KEYWORDS or any(
            token in term_info.get('keywords', [])
            for domain in legal_config['LEGAL_TERMS'].values()
            for term_info in [domain]
        )
        
    def multi_dimensional_analysis(self, text: str, domain: str) -> Dict:
        """多维度分析"""
        # 预处理
        preprocessed = self.enhanced_text_preprocessing(text)
        
        # 复杂度分析
        complexity = self.calculate_text_complexity(preprocessed)
        
        # 情感分析
        sentiment = self.analyze_sentiment(text)
        
        # 风险评估
        risk_assessment = self.comprehensive_risk_assessment(text, domain)
        
        return {
            'text_analysis': {
                'length_analysis': {
                    'character_count': len(text),
                    'word_count': len(preprocessed['tokens']),
                    'sentence_count': preprocessed['sentence_count']
                },
                'complexity': complexity,
                'sentiment': sentiment
            },
            'risk_assessment': risk_assessment
        }
    
    def comprehensive_risk_assessment(self, text: str, domain: str) -> Dict:
        """综合风险评估"""
        risk_indicators = {
            'privacy': ['泄露', '滥用', '未授权', '第三方', '商业目的'],
            'contract': ['违约', '终止', '解除', '赔偿', '责任'],
            'intellectual_property': ['侵权', '盗用', '抄袭', '仿制', '山寨']
        }
        
        domain_indicators = risk_indicators.get(domain, [])
        tokens = list(jb.cut(text))
        
        risk_score = 0.0
        found_risks = []
        
        for indicator in domain_indicators:
            if indicator in text:
                risk_score += 0.2
                found_risks.append(indicator)
                
        # 标准化风险分数
        risk_score = min(risk_score, 1.0)
        
        risk_level = 'low'
        if risk_score >= 0.7:
            risk_level = 'high'
        elif risk_score >= 0.4:
            risk_level = 'medium'
            
        return {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'risk_indicators': found_risks,
            'recommendation': self._get_risk_recommendation(risk_level)
        }
        
    def _get_risk_recommendation(self, risk_level: str) -> str:
        """根据风险等级提供建议"""
        recommendations = {
            'low': '文档风险较低，建议定期审查和更新。',
            'medium': '文档存在中等风险，建议尽快完善相关条款。',
            'high': '文档存在高风险，强烈建议立即修改和完善。'
        }
        return recommendations.get(risk_level, '')

    def calculate_text_complexity(self, preprocessed_data: Dict) -> Dict[str, float]:
        """计算文本复杂度"""
        tokens = preprocessed_data.get('tokens', [])
        sentences = preprocessed_data.get('sentences', [])
        
        if not tokens or not sentences:
            return {
                'complexity_score': 0.0,
                'lexical_diversity': 0.0,
                'avg_sentence_length': 0.0,
                'complexity_level': 'unknown'
            }
        
        # 词汇多样性（类型-标记比）
        unique_tokens = set(tokens)
        lexical_diversity = len(unique_tokens) / len(tokens) if tokens else 0
        
        # 平均句长
        avg_sentence_length = len(tokens) / len(sentences) if sentences else 0
        
        # 复杂词汇比例（长度大于4的词）
        complex_words = [token for token in tokens if len(token) > 4]
        complex_word_ratio = len(complex_words) / len(tokens) if tokens else 0
        
        # 综合复杂度分数
        complexity_score = (
            lexical_diversity * 0.4 +
            min(avg_sentence_length / 20, 1.0) * 0.3 +  # 标准化句长
            complex_word_ratio * 0.3
        )
        
        # 确定复杂度等级
        if complexity_score >= 0.8:
            complexity_level = 'very_high'
        elif complexity_score >= 0.6:
            complexity_level = 'high'
        elif complexity_score >= 0.4:
            complexity_level = 'medium'
        elif complexity_score >= 0.2:
            complexity_level = 'low'
        else:
            complexity_level = 'very_low'
        
        return {
            'complexity_score': round(complexity_score, 3),
            'lexical_diversity': round(lexical_diversity, 3),
            'avg_sentence_length': round(avg_sentence_length, 2),
            'complex_word_ratio': round(complex_word_ratio, 3),
            'complexity_level': complexity_level
        }
    
    def analyze_sentiment(self, text: str) -> Dict[str, any]:
        """基础情感分析"""
        # 简单的情感词典方法
        positive_words = ['好', '优秀', '完善', '保护', '安全', '合法', '规范', '专业', '可靠']
        negative_words = ['差', '不足', '缺失', '风险', '违法', '不当', '问题', '错误', '危险']
        neutral_words = ['规定', '条款', '说明', '内容', '信息', '数据', '处理', '使用']
        
        tokens = list(jb.cut(text))
        
        positive_count = sum(1 for token in tokens if token in positive_words)
        negative_count = sum(1 for token in tokens if token in negative_words)
        neutral_count = sum(1 for token in tokens if token in neutral_words)
        
        total_sentiment_words = positive_count + negative_count + neutral_count
        
        if total_sentiment_words == 0:
            sentiment_score = 0.5  # 中性
            sentiment_label = 'neutral'
        else:
            # 计算情感分数 (0-1, 0.5为中性)
            sentiment_score = (positive_count - negative_count + total_sentiment_words) / (2 * total_sentiment_words)
            
            if sentiment_score >= 0.6:
                sentiment_label = 'positive'
            elif sentiment_score <= 0.4:
                sentiment_label = 'negative'
            else:
                sentiment_label = 'neutral'
        
        return {
            'sentiment_score': round(sentiment_score, 3),
            'sentiment_label': sentiment_label,
            'positive_words_count': positive_count,
            'negative_words_count': negative_count,
            'neutral_words_count': neutral_count,
            'confidence': min(total_sentiment_words / len(tokens), 1.0) if tokens else 0
        }

class EnhancedAnalyzer:
    """重构的增强分析器 - 使用严格的评分系统"""
    
    def __init__(self):
        self.legal_analyzer = LegalAnalyzer()
        self.scoring_system = DocumentScoringSystem()
        self.load_professional_terms()
        
    def load_professional_terms(self):
        """加载专业术语词典"""
        self.professional_terms = {
            'privacy': ['个人信息', '隐私政策', '数据处理', '信息收集', '第三方共享'],
            'intellectual_property': ['知识产权', '专利', '商标', '著作权', '版权'],
            'contract': ['合同条款', '违约责任', '履行义务', '权利义务', '合同解除']
        }
        
    def analyze_document(self, text: str, domain: str = 'privacy') -> dict:
        """重构的文档分析 - 使用严格评分"""
        # 基础预处理
        tokens = self.preprocess_text(text)
        
        # 使用新的评分系统
        comprehensive_score = self.scoring_system.generate_comprehensive_score(text, domain, tokens)
        
        # 法律专业分析
        legal_structure = self.legal_analyzer.analyze_legal_structure(text)
        legal_compliance = self.legal_analyzer.evaluate_legal_compliance(text, domain)
        
        # 风险评估
        risk_assessment = self.comprehensive_risk_assessment(text, domain)
        
        # 构建结果
        results = {
            'metadata': {
                'source_text_length': len(text),
                'token_count': len(tokens),
                'structure_info': legal_structure,
                'analysis_domain': domain,
                'analysis_timestamp': pd.Timestamp.now().isoformat()
            },
            'scoring_results': {
                'overall_score': comprehensive_score['total_score'],
                'percentage_score': comprehensive_score['percentage'],
                'grade': comprehensive_score['grade'],
                'detailed_breakdown': comprehensive_score['detailed_scores'],
                'scoring_methodology': comprehensive_score['scoring_weights']
            },
            'text_analysis': {
                'complexity': self.calculate_text_complexity({'tokens': tokens, 'sentences': self._split_sentences(text)}),
                'sentiment': self.analyze_sentiment(text),
                'professional_terms_count': self._count_professional_terms(tokens)
            },
            'legal_analysis': {
                'compliance': legal_compliance,
                'structure_analysis': legal_structure,
                'risk_assessment': risk_assessment
            },
            'recommendations': {
                'improvement_suggestions': comprehensive_score['recommendations'],
                'priority_actions': self._generate_priority_actions(comprehensive_score),
                'compliance_gaps': self._identify_compliance_gaps(legal_compliance, domain)
            },
            'quality_indicators': {
                'is_high_quality': comprehensive_score['total_score'] >= 0.8,
                'needs_improvement': comprehensive_score['total_score'] < 0.6,
                'critical_issues': comprehensive_score['total_score'] < 0.4,
                'overall_assessment': self._generate_overall_assessment(comprehensive_score['total_score'])
            }
        }
        
        return results
    
    def _split_sentences(self, text: str) -> List[str]:
        """简单的句子分割"""
        import re
        # 基于句号、感叹号、问号分割句子
        sentences = re.split(r'[。！？\n]+', text)
        # 过滤空句子并去除首尾空格
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences
    
    def _count_professional_terms(self, tokens: List[str]) -> int:
        """统计专业术语"""
        count = 0
        all_terms = set()
        for domain_terms in self.professional_terms.values():
            all_terms.update(domain_terms)
        
        for token in tokens:
            if token in all_terms:
                count += 1
        return count
    
    def _generate_priority_actions(self, score_data: Dict) -> List[str]:
        """生成优先改进行动"""
        actions = []
        detailed = score_data['detailed_scores']
        
        # 按分数排序，优先改进分数最低的方面
        scores = [
            ('内容质量', detailed['content_quality']['score']),
            ('法律合规', detailed['legal_compliance']['score']), 
            ('完整性', detailed['completeness']['score']),
            ('清晰度', detailed['clarity']['score'])
        ]
        
        scores.sort(key=lambda x: x[1])  # 按分数升序排序
        
        for aspect, score in scores[:2]:  # 取分数最低的两个方面
            if score < 0.6:
                actions.append(f"优先改进{aspect}(当前分数: {score:.2f})")
        
        return actions if actions else ["继续保持文档质量"]
    
    def _identify_compliance_gaps(self, compliance_data: Dict, domain: str) -> List[str]:
        """识别合规缺口"""
        gaps = []
        
        compliance_score = compliance_data.get('compliance_score', 0)
        if compliance_score < 0.7:
            gaps.append(f"{domain}领域合规性不足，需要补充相关条款")
        
        missing_sections = compliance_data.get('missing_sections', [])
        if missing_sections:
            gaps.extend([f"缺失必要部分: {section}" for section in missing_sections])
        
        return gaps if gaps else ["合规性良好"]
    
    def _generate_overall_assessment(self, total_score: float) -> str:
        """生成总体评估"""
        if total_score >= 0.9:
            return "优秀 - 文档质量很高，符合行业标准"
        elif total_score >= 0.75:
            return "良好 - 文档质量较高，有小幅改进空间"
        elif total_score >= 0.6:
            return "合格 - 文档基本可用，建议进行改进"
        elif total_score >= 0.4:
            return "需要改进 - 文档存在明显不足，建议重新审查"
        else:
            return "不合格 - 文档质量较差，需要重新制定"
    
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
    
    def enhanced_text_preprocessing(self, text: str) -> Dict[str, any]:
        """增强版文本预处理"""
        # 文本清洗
        cleaned_text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9，。！？；：""''（）【】《》、]', '', text)
        
        # 分句
        sentences = re.split(r'[。！？；]', cleaned_text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # 分词
        tokens = list(jb.cut(cleaned_text))
        
        return {
            'original_text': text,
            'cleaned_text': cleaned_text,
            'sentences': sentences,
            'tokens': tokens,
            'sentence_count': len(sentences),
            'token_count': len(tokens)
        }
        
    def _is_legal_term(self, token: str) -> bool:
        """判断是否为法律术语"""
        for domain_terms in self.professional_terms.values():
            if any(term in token for term in domain_terms):
                return True
        return token in KEYWORDS or any(
            token in term_info.get('keywords', [])
            for domain in legal_config['LEGAL_TERMS'].values()
            for term_info in [domain]
        )
        
    def multi_dimensional_analysis(self, text: str, domain: str) -> Dict:
        """多维度分析"""
        # 预处理
        preprocessed = self.enhanced_text_preprocessing(text)
        
        # 复杂度分析
        complexity = self.calculate_text_complexity(preprocessed)
        
        # 情感分析
        sentiment = self.analyze_sentiment(text)
        
        # 风险评估
        risk_assessment = self.comprehensive_risk_assessment(text, domain)
        
        return {
            'text_analysis': {
                'length_analysis': {
                    'character_count': len(text),
                    'word_count': len(preprocessed['tokens']),
                    'sentence_count': preprocessed['sentence_count']
                },
                'complexity': complexity,
                'sentiment': sentiment
            },
            'risk_assessment': risk_assessment
        }
    
    def comprehensive_risk_assessment(self, text: str, domain: str) -> Dict:
        """综合风险评估"""
        risk_indicators = {
            'privacy': ['泄露', '滥用', '未授权', '第三方', '商业目的'],
            'contract': ['违约', '终止', '解除', '赔偿', '责任'],
            'intellectual_property': ['侵权', '盗用', '抄袭', '仿制', '山寨']
        }
        
        domain_indicators = risk_indicators.get(domain, [])
        tokens = list(jb.cut(text))
        
        risk_score = 0.0
        found_risks = []
        
        for indicator in domain_indicators:
            if indicator in text:
                risk_score += 0.2
                found_risks.append(indicator)
                
        # 标准化风险分数
        risk_score = min(risk_score, 1.0)
        
        risk_level = 'low'
        if risk_score >= 0.7:
            risk_level = 'high'
        elif risk_score >= 0.4:
            risk_level = 'medium'
            
        return {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'risk_indicators': found_risks,
            'recommendation': self._get_risk_recommendation(risk_level)
        }
        
    def _get_risk_recommendation(self, risk_level: str) -> str:
        """根据风险等级提供建议"""
        recommendations = {
            'low': '文档风险较低，建议定期审查和更新。',
            'medium': '文档存在中等风险，建议尽快完善相关条款。',
            'high': '文档存在高风险，强烈建议立即修改和完善。'
        }
        return recommendations.get(risk_level, '')

    def calculate_text_complexity(self, preprocessed_data: Dict) -> Dict[str, float]:
        """计算文本复杂度"""
        tokens = preprocessed_data.get('tokens', [])
        sentences = preprocessed_data.get('sentences', [])
        
        if not tokens or not sentences:
            return {
                'complexity_score': 0.0,
                'lexical_diversity': 0.0,
                'avg_sentence_length': 0.0,
                'complexity_level': 'unknown'
            }
        
        # 词汇多样性（类型-标记比）
        unique_tokens = set(tokens)
        lexical_diversity = len(unique_tokens) / len(tokens) if tokens else 0
        
        # 平均句长
        avg_sentence_length = len(tokens) / len(sentences) if sentences else 0
        
        # 复杂词汇比例（长度大于4的词）
        complex_words = [token for token in tokens if len(token) > 4]
        complex_word_ratio = len(complex_words) / len(tokens) if tokens else 0
        
        # 综合复杂度分数
        complexity_score = (
            lexical_diversity * 0.4 +
            min(avg_sentence_length / 20, 1.0) * 0.3 +  # 标准化句长
            complex_word_ratio * 0.3
        )
        
        # 确定复杂度等级
        if complexity_score >= 0.8:
            complexity_level = 'very_high'
        elif complexity_score >= 0.6:
            complexity_level = 'high'
        elif complexity_score >= 0.4:
            complexity_level = 'medium'
        elif complexity_score >= 0.2:
            complexity_level = 'low'
        else:
            complexity_level = 'very_low'
        
        return {
            'complexity_score': round(complexity_score, 3),
            'lexical_diversity': round(lexical_diversity, 3),
            'avg_sentence_length': round(avg_sentence_length, 2),
            'complex_word_ratio': round(complex_word_ratio, 3),
            'complexity_level': complexity_level
        }
    
    def analyze_sentiment(self, text: str) -> Dict[str, any]:
        """基础情感分析"""
        # 简单的情感词典方法
        positive_words = ['好', '优秀', '完善', '保护', '安全', '合法', '规范', '专业', '可靠']
        negative_words = ['差', '不足', '缺失', '风险', '违法', '不当', '问题', '错误', '危险']
        neutral_words = ['规定', '条款', '说明', '内容', '信息', '数据', '处理', '使用']
        
        tokens = list(jb.cut(text))
        
        positive_count = sum(1 for token in tokens if token in positive_words)
        negative_count = sum(1 for token in tokens if token in negative_words)
        neutral_count = sum(1 for token in tokens if token in neutral_words)
        
        total_sentiment_words = positive_count + negative_count + neutral_count
        
        if total_sentiment_words == 0:
            sentiment_score = 0.5  # 中性
            sentiment_label = 'neutral'
        else:
            # 计算情感分数 (0-1, 0.5为中性)
            sentiment_score = (positive_count - negative_count + total_sentiment_words) / (2 * total_sentiment_words)
            
            if sentiment_score >= 0.6:
                sentiment_label = 'positive'
            elif sentiment_score <= 0.4:
                sentiment_label = 'negative'
            else:
                sentiment_label = 'neutral'
        
        return {
            'sentiment_score': round(sentiment_score, 3),
            'sentiment_label': sentiment_label,
            'positive_words_count': positive_count,
            'negative_words_count': negative_count,
            'neutral_words_count': neutral_count,
            'confidence': min(total_sentiment_words / len(tokens), 1.0) if tokens else 0
        }

def process_pipeline(domain: str = 'privacy') -> dict:
    """增强版处理流程"""
    # 使用项目根目录下的固定文件
    input_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Target.txt')
    output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Analysis.txt')
    
    with open(input_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    analyzer = EnhancedAnalyzer()
    results = analyzer.analyze_document(text, domain)
    
    # 保存详细分析结果到 Analysis.txt
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    return results

if __name__ == "__main__":
    results = process_pipeline()
    print("Analysis completed and results saved to Analysis.txt")