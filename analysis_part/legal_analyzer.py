import json
from collections import defaultdict
from typing import Dict, List, Tuple, Any
import numpy as np
from pathlib import Path
import re
import sys

# 添加项目根路径到系统路径
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))

from vivo_rag_system.src.api.vivo_llm import VivoLLMAPI
from vivo_rag_system.src.core.rag_engine import RAGEngine

class LegalAnalyzer:
    def __init__(self):
        config_path = Path(__file__).parent / 'legal_config.json'
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # 加载法律术语词典
        legal_terms_path = Path(__file__).parent / 'legal_terms.txt'
        self.legal_terms = self._load_legal_terms(legal_terms_path)
        
        self.error_count = defaultdict(int)
        
        # 初始化VIVO LLM API和RAG引擎
        self.llm_api = VivoLLMAPI()
        self.rag_engine = RAGEngine()
        
    def _load_legal_terms(self, path: Path) -> set:
        """加载法律术语词典"""
        terms = set()
        try:
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('//'):
                        # 移除词性标注，只保留术语
                        term = line.split()[0]
                        terms.add(term)
        except Exception as e:
            print(f"Warning: Failed to load legal terms: {e}")
        return terms

    def _extract_legal_terms(self, text: str) -> List[str]:
        """从文本中提取法律术语"""
        legal_terms_found = []
        # 对于词典中的每个术语
        for term in self.legal_terms:
            # 使用正则表达式查找所有匹配项
            matches = re.finditer(re.escape(term), text)
            legal_terms_found.extend(term for _ in matches)
        return legal_terms_found

    def _analyze_term_distribution(self, terms: List[str]) -> Dict[str, int]:
        """分析术语分布情况"""
        distribution = defaultdict(int)
        for term in terms:
            distribution[term] += 1
        return dict(sorted(distribution.items(), key=lambda x: x[1], reverse=True))

    def _safe_analyze(self, method, *args, **kwargs):
        """安全执行分析方法的装饰器实现"""
        try:
            return method(*args, **kwargs)
        except Exception as e:
            error_type = type(e).__name__
            self.error_count[error_type] += 1
            print(f"Warning: {error_type} occurred in {method.__name__}: {str(e)}")
            return None    
        
    def analyze_legal_structure(self, text: str) -> Dict:
        """分析法律文本结构"""
        try:
            sections = self._split_into_sections(text)
            sections_content = self._intelligent_split_into_sections(text)
            
            # 对每个章节使用LLM进行评估
            llm_scores = {}
            for title, content in sections_content.items():
                llm_scores[title] = self._safe_analyze(
                    self._llm_quality_assessment, 
                    content, 
                    title, 
                    "privacy"  # 默认domain，实际使用时应该传入
                )
            
            structure_analysis = {
                'section_count': len(sections),
                'completeness': self._safe_analyze(self._check_completeness, sections),
                'hierarchy': self._safe_analyze(self._analyze_hierarchy, sections),
                'section_quality': self._safe_analyze(self._analyze_section_quality, sections),
                'term_density': self._safe_analyze(self._analyze_term_density, text),
                'llm_assessment': llm_scores,  # LLM评估结果
                'error_statistics': dict(self.error_count)
            }
            
            # 获取相似案例进行参考
            similar_cases = self._safe_analyze(self._get_similar_cases, text, "privacy")
            if similar_cases:
                structure_analysis['similar_cases'] = similar_cases
            
            return structure_analysis
        except Exception as e:
            print(f"Critical error in analyze_legal_structure: {str(e)}")
            return {
                'error': str(e),
                'error_statistics': dict(self.error_count)
            }
    
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
        pattern = re.compile(r"(?:(?<=\n)|(?<=^))\s*((?:第[一二三四五六七八九十百千万]+条|[一二三四五六七八九十百千万]+[、．.]|\d+[、．.]|[（(][一二三四五六七八九十百千万\d]+[）)]|[A-Za-z]+\.))\s*[^\\n]+", re.MULTILINE)
        
        titles = pattern.findall(text)
        contents = pattern.split(text)
        
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
    
    def _analyze_section_quality(self, sections: List[str]) -> Dict:
        """分析章节质量"""
        quality_scores = {}
        for section in sections:
            # 评估每个章节的质量
            clarity_score = self._assess_clarity(section)
            completeness_score = self._assess_completeness(section)
            consistency_score = self._assess_consistency(section)
            
            quality_scores[section[:30]] = {
                'clarity': clarity_score,
                'completeness': completeness_score,
                'consistency': consistency_score,
                'average': (clarity_score + completeness_score + consistency_score) / 3
            }
        return quality_scores
    
    def _analyze_term_density(self, text: str) -> Dict:
        """分析法律术语密度"""
        total_words = len(text.split())
        legal_terms = self._extract_legal_terms(text)
        density = len(legal_terms) / total_words if total_words > 0 else 0
        
        return {
            'total_words': total_words,
            'legal_terms_count': len(legal_terms),
            'density': density,
            'term_distribution': self._analyze_term_distribution(legal_terms)
        }
    
    def _assess_clarity(self, section: str) -> float:
        """评估文本清晰度"""
        # 1. 句子长度分析
        sentences = re.split(r'[。！？]', section)
        avg_sentence_length = np.mean([len(s) for s in sentences if s])
        
        # 2. 专业术语使用频率
        legal_terms = self._extract_legal_terms(section)
        term_frequency = len(legal_terms) / len(section) if section else 0
        
        # 3. 标点符号使用
        punctuation_ratio = len(re.findall(r'[，。；：！？、]', section)) / len(section) if section else 0
        
        # 计算综合得分 (0-1)
        clarity_score = (
            0.4 * (1 - min(avg_sentence_length / 100, 1)) +  # 较短的句子更清晰
            0.3 * min(term_frequency * 10, 1) +  # 适度的专业术语
            0.3 * min(punctuation_ratio * 5, 1)  # 适当的标点使用
        )
        
        return min(max(clarity_score, 0), 1)  # 确保分数在0-1之间
        
    def _assess_completeness(self, section: str) -> float:
        """评估章节的完整性"""
        # 实现完整性评估逻辑
        required_elements = ['定义', '范围', '权利', '义务', '责任']
        found_elements = sum(1 for element in required_elements if element in section)
        return found_elements / len(required_elements)
        
    def _assess_consistency(self, section: str) -> float:
        """评估用语一致性"""
        # 实现一致性评估逻辑
        terms = self._extract_legal_terms(section)
        term_counts = defaultdict(int)
        for term in terms:
            term_counts[term] += 1
            
        # 计算术语使用的变异系数
        if term_counts:
            mean = np.mean(list(term_counts.values()))
            std = np.std(list(term_counts.values()))
            cv = std / mean if mean > 0 else 0
            return 1 - min(cv, 1)  # 转换为0-1分数，变异系数越小越好
        return 0

    def _llm_quality_assessment(self, section: str, section_name: str, domain: str) -> Dict:
        """使用LLM评估章节质量
        
        Args:
            section: 章节内容
            section_name: 章节名称
            domain: 领域名称，如 "privacy", "contract" 等
            
        Returns:
            包含评分和建议的字典
        """
        try:
            messages = [
                {
                    "role": "system",
                    "content": f"你是一个专业的{domain}领域法律文本评估专家。请对以下文本进行专业评估，重点关注：专业性、完整性、清晰度、合规性。"
                },
                {
                    "role": "user",
                    "content": f"""请对以下'{section_name}'章节进行评估，并给出具体分数(1-100)和改进建议：

{section}

请按以下JSON格式返回评估结果：
{{
    "clarity_score": 分数,
    "completeness_score": 分数,
    "compliance_score": 分数,
    "suggestions": ["建议1", "建议2", ...]
}}"""
                }
            ]

            response = self.llm_api.chat_completion(messages, temperature=0.3)
            return self._parse_llm_scores(response)

        except Exception as e:
            print(f"LLM评估失败: {str(e)}")
            return {
                "clarity_score": 0,
                "completeness_score": 0,
                "compliance_score": 0,
                "suggestions": [f"评估失败: {str(e)}"]
            }

    def _parse_llm_scores(self, response: str) -> Dict:
        """解析LLM返回的评分结果
        
        Args:
            response: LLM返回的JSON字符串
        
        Returns:
            解析后的评分字典
        """
        try:
            # 尝试直接解析JSON
            scores = json.loads(response)
            return scores
        except json.JSONDecodeError:
            # 如果直接解析失败，尝试从文本中提取分数
            scores = {
                "clarity_score": self._extract_score(response, "clarity"),
                "completeness_score": self._extract_score(response, "completeness"),
                "compliance_score": self._extract_score(response, "compliance"),
                "suggestions": []
            }
            
            # 提取建议
            suggestions = re.findall(r'"([^"]+)"', response)
            if suggestions:
                scores["suggestions"] = suggestions
            
            return scores

    def _extract_score(self, text: str, score_type: str) -> float:
        """从文本中提取特定类型的分数
        
        Args:
            text: 要分析的文本
            score_type: 分数类型 (clarity/completeness/compliance)
            
        Returns:
            提取到的分数，如果未找到则返回0
        """
        try:
            # 查找类似于 "clarity_score": 85 的模式
            pattern = rf'"{score_type}_score":\s*(\d+)'
            match = re.search(pattern, text)
            if match:
                return float(match.group(1))
            return 0
        except Exception:
            return 0

    def _get_similar_cases(self, text: str, domain: str) -> List[Dict]:
        """获取相似案例
        
        Args:
            text: 要分析的文本
            domain: 领域名称
            
        Returns:
            相似案例列表
        """
        try:
            # 使用RAG引擎的process_query方法处理查询
            rag_result = self.rag_engine.process_query(text, use_professional_kb=True)
            
            if not rag_result.get('context'):
                return []
                
            # 将上下文分割成单独的案例
            cases = [case.strip() for case in rag_result['context'].split('相关文档') if case.strip()]
            
            # 构建批量处理的prompt
            case_contents = []
            for case in cases:
                case_content = case
                if '关键词:' in case:
                    case_content = case.split('关键词:')[0].strip()
                case_contents.append(case_content)
            
            # 构建单个批量处理prompt
            batch_prompt = [
                {
                    "role": "system",
                    "content": "你是一个法律案例相关性分析专家。请分析多个案例与目标案例的相关性。"
                },
                {
                    "role": "user",
                    "content": f'''请分析以下多个案例与目标案例的相关性，为每个案例给出0-100的相关度分数和原因。

目标案例：
{text}

待分析案例：
{chr(10).join(f"案例{i+1}：{case_content}" for i, case_content in enumerate(case_contents))}

请用JSON格式返回分析结果，格式如下：
{{
    "analyses": [
        {{
            "case_index": 1,
            "relevance_score": 分数,
            "reasoning": "原因描述"
        }},
        // ... 其他案例的分析结果
    ]
}}'''
                }
            ]
            
            try:
                # 一次性获取所有案例的相关性分析结果
                batch_result = self.llm_api.chat_completion(batch_prompt, temperature=0.3)
                result_data = json.loads(batch_result)
                
                # 处理分析结果
                enriched_cases = []
                for analysis in result_data.get('analyses', []):
                    case_index = analysis.get('case_index', 1) - 1  # 转换为0-based索引
                    if 0 <= case_index < len(case_contents):
                        enriched_cases.append({
                            "content": case_contents[case_index],
                            "relevance_score": analysis.get('relevance_score', 0),
                            "reasoning": analysis.get('reasoning', '未提供分析原因')
                        })
                
            except Exception as e:
                print(f"批量案例相关性分析失败: {str(e)}")
                # 如果批量处理失败，返回空结果
                return []
            
            # 按相关度排序
            return sorted(enriched_cases, key=lambda x: x['relevance_score'], reverse=True)

        except Exception as e:
            print(f"获取相似案例失败: {str(e)}")
            return []