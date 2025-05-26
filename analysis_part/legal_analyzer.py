import json
from collections import defaultdict
from typing import Dict, List, Tuple, Any
import numpy as np
from pathlib import Path
import re # 新增导入

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
        # 使用更具体的模板key，例如 domain + \"_policy\" 或 domain + \"_agreement\"
        # 这里假设 domain 直接对应 LEGAL_TEMPLATES 中的一级key，如 \"privacy\" 对应 \"privacy_policy\"
        # 如果 domain 是 \"privacy\", template_key 应该是 \"privacy_policy\"
        # 你可能需要一个映射或者更智能的key匹配逻辑
        template_key = domain # 简化处理，实际应用中可能需要更复杂的映射
        if domain == "privacy": # 特殊处理，因为配置文件中是 privacy_policy
            template_key = "privacy_policy"
        elif domain == "contract": # 假设合同对应 service_agreement
            template_key = "service_agreement"
        # else: # 其他 domain 可能需要不同的模板key
            # template_key = domain # 或者抛出错误，如果找不到对应模板

        domain_config = self.config['LEGAL_TEMPLATES'].get(template_key, {})
        required_sections_config = domain_config.get('required_sections', [])
        # required_sections_config 现在是一个对象列表，每个对象包含 name 和 keywords

        reference_laws = self.config['REFERENCE_LAWS'].get(domain, [])
        
        # 使用更智能的分段逻辑
        sections_content = self._intelligent_split_into_sections(text)
        
        found_sections_details = []
        missing_sections_names = []
        compliance_score_total = 0
        max_possible_score = 0

        for req_sec_obj in required_sections_config:
            req_sec_name = req_sec_obj.get("name")
            req_sec_keywords = req_sec_obj.get("keywords", [])
            req_sec_weight = req_sec_obj.get("weight", 1.0) # 获取权重，默认为1
            max_possible_score += req_sec_weight

            found = False
            # 检查文本中是否包含该章节的关键词
            for content_section_name, content_section_text in sections_content.items():
                # 优先匹配章节标题
                if req_sec_name.lower() in content_section_name.lower():
                    found = True
                    break
                # 其次匹配章节内容中的关键词
                if any(keyword.lower() in content_section_text.lower() for keyword in req_sec_keywords):
                    found = True
                    break
            # 也可以直接在整个文本中搜索关键词，作为补充
            if not found and any(keyword.lower() in text.lower() for keyword in req_sec_keywords):
                found = True

            if found:
                found_sections_details.append({"name": req_sec_name, "status": "存在"})
                compliance_score_total += req_sec_weight # 加上权重分
            else:
                missing_sections_names.append(req_sec_name)
                found_sections_details.append({"name": req_sec_name, "status": "缺失或不明显"})

        final_compliance_score = (compliance_score_total / max_possible_score) if max_possible_score > 0 else 0
        
        return {
            'compliance_score': round(final_compliance_score * 100, 2), # 返回百分比
            'found_sections_details': found_sections_details, # 详细的章节检查结果
            'missing_sections': missing_sections_names,
            'applicable_laws': reference_laws,
            'risk_level': self._assess_risk_level(domain, missing_sections_names, final_compliance_score)
        }
    
    def generate_professional_advice(self, analysis_results: Dict, domain: str) -> Dict:
        """生成专业法律建议，增加domain参数以获取领域特定建议"""
        advice = {
            'general_assessment': self._generate_general_assessment(analysis_results),
            'specific_recommendations': self._generate_recommendations(analysis_results, domain),
            'legal_references': self._get_relevant_legal_references(analysis_results),
            'risk_mitigation': self._generate_risk_mitigation_advice(analysis_results)
        }
        return advice
    
    def _split_into_sections(self, text: str) -> List[str]:
        """将法律文本分割为段落 - 保留此方法作为备用或内部使用"""
        # 基于标题和序号进行智能分段
        # TODO: 实现更复杂的分段逻辑
        return [s.strip() for s in text.split('\n\n') if s.strip()]
    
    def _intelligent_split_into_sections(self, text: str) -> Dict[str, str]:
        """更智能地将法律文本分割为章节及其内容"""
        sections = {}
        # 匹配常见的章节标题模式，如 “一、XXX”, “第X条 XXX”, “1. XXX”
        # (\d+|[一二三四五六七八九十百千万]+)[、.]?\s*([^\n]+)
        # (?:^|\n)\s*((?:第[一二三四五六七八九十百千万]+条|[一二三四五六七八九十百千万]+[、．.]|\d+[、．.])\s*[^\n]+)
        # 更通用的标题匹配，允许中英文括号等
        # pattern = re.compile(r\"(?:^|\\n)\\s*((?:第[一二三四五六七八九十百千万]+条|[一二三四五六七八九十百千万]+[、．.]|\\d+[、．.]|[（(][一二三四五六七八九十百千万\\d]+[）)])\\s*[^\\n]+)\", re.MULTILINE)
        pattern = re.compile(r"(?:(?<=\n)|(?<=^))\s*((?:第[一二三四五六七八九十百千万]+条|[一二三四五六七八九十百千万]+[、．.]|\d+[、．.]|[（(][一二三四五六七八九十百千万\d]+[）)]|[A-Za-z]+\.))\s*[^\\n]+", re.MULTILINE)
        
        titles = pattern.findall(text)
        contents = pattern.split(text)
        
        # contents[0] 是第一个标题前的内容（如果有）
        # contents[1] 是第一个标题, contents[2] 是第一个标题后的内容, contents[3] 是第二个标题, ...
        
        current_section_title = "引言或未明确章节"
        if contents:
            if len(contents) == 1: # 没有匹配到标题
                sections[current_section_title] = contents[0].strip()
                return sections
            
            if not pattern.match(contents[0]): # 第一个元素不是标题，则为引言
                 sections[current_section_title] = contents[0].strip()
                 start_index = 1
            else: # 第一个元素就是标题
                 start_index = 0

            for i in range(start_index, len(contents), 2):
                if i + 1 < len(contents):
                    title = contents[i].strip()
                    content = contents[i+1].strip()
                    sections[title] = content
                elif contents[i].strip(): #最后一个元素可能是无标题的结尾
                    sections[f"结尾部分_{i}"] = contents[i].strip()
        
        if not sections and text.strip(): # 如果完全没有分割出章节，则整个文本视为一个章节
            sections["全文"] = text.strip()
            
        return sections

    def _check_completeness(self, sections: List[str]) -> float:
        """检查文本完整性 - 此方法可能需要根据新的章节结构调整或废弃"""
        # 基于模板要求计算完整性得分
        return len(sections) / 10.0  # 简化版实现
    
    def _analyze_hierarchy(self, sections: List[str]) -> Dict:
        """分析条款层级结构"""
        return {
            'main_clauses': len([s for s in sections if self._is_main_clause(s)]),
            'sub_clauses': len([s for s in sections if self._is_sub_clause(s)])
        }
    
    def _assess_risk_level(self, domain: str, missing_sections: List[str], compliance_score: float) -> str:
        """评估风险等级，结合缺失章节数量和合规分数"""
        # 使用配置文件中的风险等级阈值
        risk_thresholds = self.config.get('RISK_LEVELS', {"high": 0.5, "medium": 0.75, "low": 1.0})
        # 注意：这里的阈值逻辑是分数越低风险越高

        if compliance_score < risk_thresholds.get("high", 0.5): # 低于 high 的阈值，则为高风险
            return "高风险"
        elif compliance_score < risk_thresholds.get("medium", 0.75): # 低于 medium 的阈值，则为中风险
            return "中风险"
        else:
            return "低风险"
        
        # 旧的逻辑，可以移除或注释
        # base_risk = self.config[\'LEGAL_TERMS\'].get(domain, {}).get(\'risk_level\', \'low\')
        # if len(missing_sections) > 2 or compliance_score < 0.4:
        #     return \'high\'
        # elif len(missing_sections) > 0 or compliance_score < 0.7:
        #     return \'medium\'
        # return base_risk
    
    def _is_main_clause(self, section: str) -> bool:
        """判断是否为主条款 - 此方法可能需要根据新的章节结构调整或废弃"""
        # TODO: 实现更复杂的判断逻辑
        return section.strip().startswith(('第', '1', '一'))
    
    def _is_sub_clause(self, section: str) -> bool:
        """判断是否为子条款"""
        # TODO: 实现更复杂的判断逻辑
        return any(c in section[:3] for c in ('(', '（', '1.', '1、'))
    def _generate_general_assessment(self, results: Dict) -> str:
        """生成总体评估，基于新的百分比合规分数"""
        compliance_score_percent = results.get('compliance_score', 0) # 已经是百分比
        # 确保 compliance_score_percent 不是 None
        if compliance_score_percent is None:
            compliance_score_percent = 0
        if compliance_score_percent >= 80:
            return "文档整体合规性良好。"
        elif compliance_score_percent >= 60:
            return "文档合规性一般，建议关注缺失或不明确的章节，并进行相应修改。"
        elif compliance_score_percent >= 40:
            return "文档合规性存在较多问题，缺失关键章节或内容不明确，建议进行全面修订。"
        else:
            return "文档合规性存在严重问题，风险较高，强烈建议进行彻底的审查和全面修订。"
    
    def _generate_recommendations(self, results: Dict, domain: str) -> List[str]:
        """生成具体建议，增加domain参数以获取领域特定建议和缺失章节的详细说明"""
        recommendations = []
        missing_sections = results.get('missing_sections', [])
        found_sections_details = results.get('found_sections_details', [])
        risk_level = results.get('risk_level', '低风险')

        if missing_sections:
            recommendations.append(f"**关键章节缺失或不明确**：建议补充或明确以下章节：{', '.join(missing_sections)}。")
            # 可以从 legal_config.json 中获取缺失章节的描述或重要性
            template_key = domain
            if domain == "privacy": template_key = "privacy_policy"
            elif domain == "contract": template_key = "service_agreement"
            
            required_sections_config = self.config['LEGAL_TEMPLATES'].get(template_key, {}).get('required_sections', [])
            for sec_obj in required_sections_config:
                if sec_obj.get("name") in missing_sections and sec_obj.get("description"):
                    recommendations.append(f"  - 关于 '{sec_obj.get('name')}'：{sec_obj.get('description')}")
        
        # 根据风险等级给出通用建议
        if risk_level == '高风险':
            recommendations.append("**高风险提示**：文档存在严重合规问题，可能导致法律风险，请立即组织专业人士进行全面审查和修订。")
        elif risk_level == '中风险':
            recommendations.append("**中风险提示**：文档存在一定的合规问题，建议尽快进行审查和修改，以降低潜在风险。")

        # 针对具体找到的章节，未来可以增加更细致的建议，例如检查其内容是否充分等
        # for detail in found_sections_details:
        #     if detail[\"status\"] == \"存在\":
        #         # recommendations.append(f\"请进一步核查章节 '{detail[\"name\"]}' 的内容是否完整和准确。\")

    def _get_relevant_legal_references(self, analysis_results: Dict) -> List[str]:
        """根据分析结果获取相关的法律参考条文"""
        # TODO: 实现更完善的法律参考获取逻辑
        # 例如，可以基于缺失章节、风险等级或特定关键词从配置文件或数据库中查找
        references = []
        if analysis_results.get('applicable_laws'):
            references.extend(analysis_results['applicable_laws'])
        
        # 可以根据风险等级添加通用法律提示
        risk_level = analysis_results.get('risk_level')
        if risk_level == '高风险':
            references.append("鉴于评估结果为高风险，强烈建议咨询法律专业人士，确保符合所有相关法律法规。")
        elif risk_level == '中风险':
            references.append("建议查阅相关法律条文，确保文档内容合规。")
            
        if not references:
            references.append("暂无具体的法律参考条文可提供，建议进行通用法律咨询。")
            
        return list(set(references)) #去重

    def _generate_risk_mitigation_advice(self, results: Dict) -> List[str]:
        """生成风险缓解建议，基于合规分析结果"""
        advice = []
        risk_level = results.get('risk_level', '低风险')
        missing_sections = results.get('missing_sections', [])
        compliance_score = results.get('compliance_score', 0)

        if risk_level == '高风险':
            advice.append("建议立即进行全面的法律审查，特别关注缺失的关键章节和条款。")
            advice.append("考虑暂停相关业务活动，直到确保所有法律合规要求均已满足。")
        elif risk_level == '中风险':
            advice.append("建议尽快补充缺失的章节，并对照法律要求进行全面检查。")
            advice.append("考虑对现有合同或政策进行修订，以降低潜在的法律风险。")
        else:
            advice.append("保持现有的合规措施，并定期关注相关法律法规的变化。")
        
        # 针对具体缺失的章节，给出更详细的补充建议
        if missing_sections:
            advice.append("以下章节缺失，建议尽快补充：")
            for section in missing_sections:
                advice.append(f"  - {section}")

        return advice