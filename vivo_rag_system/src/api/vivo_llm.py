import requests
import yaml
import uuid
from ..utils.auth_util import gen_sign_headers
import json
from pathlib import Path
from typing import List, Dict, Optional

class VivoLLMAPI:
    """vivo大语言模型API封装"""
    
    def __init__(self):
        # 获取vivo_rag_system包的根目录
        package_root = Path(__file__).parent.parent.parent
        config_path = package_root / "config" / "settings.yaml"
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
            
        self.api_config = self.config.get('api_config', {})
        self.domain = self.api_config.get('domain', 'api-ai.vivo.com.cn')
        self.uri = self.api_config.get('llm_uri', '/vivogpt/completions')
        self.app_id = self.api_config['app_id']
        self.app_key = self.api_config['app_key']

        model_config = self.config.get('model_config', {})
        self.model_name = model_config.get('llm_model', 'vivo-BlueLM-TB-Pro')
        
        # 参数验证
        if not all([self.app_id, self.app_key]):
            raise ValueError("缺少app_id或app_key配置")
            
    def _make_api_request(self, messages: List[dict], temperature: float = 0.9, max_tokens: int = 2048) -> str:
        """发送API请求并处理响应
        
        Args:
            messages: 消息列表
            temperature: 采样温度参数
            max_tokens: 最大生成token数
            
        Returns:
            生成的文本响应
            
        Raises:
            RuntimeError: API调用失败时抛出
        """
        # 生成请求参数
        params = {
            'requestId': str(uuid.uuid4())
        }
        
        data = {
            'messages': messages,
            'model': self.model_name,
            'sessionId': str(uuid.uuid4()),
            'extra': {
                'temperature': temperature,
                'max_new_tokens': max_tokens
            }
        }
        
        # 生成签名头
        headers = gen_sign_headers(
            self.app_id,
            self.app_key,
            'POST',
            self.uri,
            query=params
        )
        headers['Content-Type'] = 'application/json'

        try:
            # 发送请求
            response = requests.post(
                f"https://{self.domain}{self.uri}",
                json=data,
                headers=headers,
                params=params,
                timeout=30
            )
            
            # 解析响应
            response.raise_for_status()
            response_data = response.json()
            
            # 调试日志
            print(f"[LLM API Response] Status: {response.status_code}, Code: {response_data.get('code')}")
            
            if response_data.get('code') == 0 and response_data.get('data'):
                return response_data['data']['content']
            elif response_data.get('code') == 1007:
                raise RuntimeError("内容审核未通过")
            else:
                raise RuntimeError(f"API调用失败: {response_data.get('msg', '未知错误')}")

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"API请求失败: {str(e)}")
        except json.JSONDecodeError:
            raise RuntimeError(f"响应解析失败: {response.text}")
        except Exception as e:
            raise RuntimeError(f"API调用失败: {str(e)}")
            
    def optimize_summary(self, summary_text: str) -> str:
        """优化摘要的语言表达
        
        Args:
            summary_text: 需要优化的摘要文本
            
        Returns:
            优化后的摘要文本
            
        Raises:
            RuntimeError: API调用失败时抛出
        """
        messages = [
            {
                "role": "system",
                "content": "你是一个专业的法律文本优化助手，专门负责改进法律文档摘要的语言表达，使其更加专业、严谨。"
            },
            {
                "role": "user",
                "content": f"""请对以下法律文本摘要进行专业性和严谨性的优化，要求：
                1. 确保使用准确的法律术语和表达方式
                2. 保持客观、严谨的语气
                3. 增强句子间的逻辑连贯性
                4. 规范化标点符号的使用，保证标点符号完整
                5. 去除口语化或不严谨的表达
                
                原文摘要：
                {summary_text}
                
                请直接返回优化后的文本，无需其他解释。"""
            }
        ]

        return self._make_api_request(messages, temperature=0.3, max_tokens=2000)
    
    def chat_completion(self, messages: List[dict], temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """通用的聊天补全接口
        
        Args:
            messages: 消息列表，每个消息是包含 role 和 content 的字典
            temperature: 温度参数，控制输出的随机性，范围 0-1
            max_tokens: 最大生成的token数量
            
        Returns:
            生成的文本响应
            
        Raises:
            RuntimeError: API调用失败时抛出
        """
        return self._make_api_request(messages, temperature=temperature, max_tokens=max_tokens)
