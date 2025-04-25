import json
from collections import defaultdict
from typing import Dict, List, Tuple
import numpy as np
from pathlib import Path

class LegalAnalyzer:
    def __init__(self):
        config_path = Path(__file__).parent / 'legal_config.json'
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
    def analyze_legal_structure(self, text: str) -> Dict:
        """分析法律文本结构"""
        sections = self._split_into_sections(text)
        structure_analysis = {
            'section_count': len(sections),
            'completeness': self._check_completeness(sections),
            'hierarchy': self._analyze_hierarchy(sections)
        }
        return structure_analysis
    
    def evaluate_legal_compliance(self, text: str, domain: str) -> Dict:
        """评估法律合规性"""
        required_sections = self.config['LEGAL_TEMPLATES'].get(domain, {}).get('required_sections', [])
        reference_laws = self.config['REFERENCE_LAWS'].get(domain, [])
        
        sections = self._split_into_sections(text)
        missing_sections = [sec for sec in required_sections if not self._contains_section(sections, sec)]
        
        return {
            'compliance_score': self._calculate_compliance_score(sections, required_sections),
            'missing_sections': missing_sections,
            'applicable_laws': reference_laws,
            'risk_level': self._assess_risk_level(domain, missing_sections)
        }
    
    def generate_professional_advice(self, analysis_results: Dict) -> Dict:
        """生成专业法律建议"""
        advice = {
            'general_assessment': self._generate_general_assessment(analysis_results),
            'specific_recommendations': self._generate_recommendations(analysis_results),
            'legal_references': self._get_relevant_legal_references(analysis_results),
            'risk_mitigation': self._generate_risk_mitigation_advice(analysis_results)
        }
        return advice
    
    def _split_into_sections(self, text: str) -> List[str]:
        """将法律文本分割为段落"""
        # 基于标题和序号进行智能分段
        # TODO: 实现更复杂的分段逻辑
        return [s.strip() for s in text.split('\n\n') if s.strip()]
    
    def _check_completeness(self, sections: List[str]) -> float:
        """检查文本完整性"""
        # 基于模板要求计算完整性得分
        return len(sections) / 10.0  # 简化版实现
    
    def _analyze_hierarchy(self, sections: List[str]) -> Dict:
        """分析条款层级结构"""
        return {
            'main_clauses': len([s for s in sections if self._is_main_clause(s)]),
            'sub_clauses': len([s for s in sections if self._is_sub_clause(s)])
        }
    
    def _calculate_compliance_score(self, sections: List[str], required: List[str]) -> float:
        """计算合规得分"""
        if not required:
            return 1.0
        found = sum(1 for req in required if any(req in sec for sec in sections))
        return found / len(required)
    
    def _assess_risk_level(self, domain: str, missing_sections: List[str]) -> str:
        """评估风险等级"""
        base_risk = self.config['LEGAL_TERMS'].get(domain, {}).get('risk_level', 'low')
        if len(missing_sections) > 2:
            return 'high'
        elif len(missing_sections) > 0:
            return 'medium'
        return base_risk
    
    def _is_main_clause(self, section: str) -> bool:
        """判断是否为主条款"""
        # TODO: 实现更复杂的判断逻辑
        return section.strip().startswith(('第', '1', '一'))
    
    def _is_sub_clause(self, section: str) -> bool:
        """判断是否为子条款"""
        # TODO: 实现更复杂的判断逻辑
        return any(c in section[:3] for c in ('(', '（', '1.', '1、'))
    
    def _contains_section(self, sections: List[str], required_section: str) -> bool:
        """检查是否包含必需章节"""
        return any(required_section in section for section in sections)
    
    def _generate_general_assessment(self, results: Dict) -> str:
        """生成总体评估"""
        compliance_score = results.get('compliance_score', 0)
        if compliance_score >= 0.8:
            return "文档整体合规性良好"
        elif compliance_score >= 0.6:
            return "文档合规性一般，需要进行部分修改"
        else:
            return "文档合规性存在明显问题，建议进行全面修订"
    
    def _generate_recommendations(self, results: Dict) -> List[str]:
        """生成具体建议"""
        recommendations = []
        missing_sections = results.get('missing_sections', [])
        if missing_sections:
            recommendations.append(f"建议添加以下必要章节: {', '.join(missing_sections)}")
        return recommendations
    
    def _get_relevant_legal_references(self, results: Dict) -> List[str]:
        """获取相关法律依据"""
        return results.get('applicable_laws', [])
    
    def _generate_risk_mitigation_advice(self, results: Dict) -> List[str]:
        """生成风险缓解建议"""
        risk_level = results.get('risk_level', 'low')
        advice = []
        if risk_level == 'high':
            advice.append("建议立即进行合规性整改")
        elif risk_level == 'medium':
            advice.append("建议在合理期限内完成整改")
        return advice