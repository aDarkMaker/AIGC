import requests
import yaml
from ..utils.auth_util import gen_sign_headers
import json
from pathlib import Path

class VivoLLMAPI:
    """vivo大语言模型API封装"""
    
    def __init__(self):
        # 获取vivo_rag_system包的根目录
        package_root = Path(__file__).parent.parent.parent
        config_path = package_root / "config" / "settings.yaml"
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
            
        self.api_config = self.config.get('api_config', {})
        self.base_url = f"https://{self.api_config['domain']}"
        self.app_id = self.api_config['app_id']
        self.app_key = self.api_config['app_key']

        # 加载配置时添加默认值处理
        self.domain = self.api_config.get('domain', 'api-ai.vivo.com.cn')
        self.uri = self.api_config.get('llm_uri', '/llm-api/v1/chat/completions')
        
        model_config = self.config.get('model_config', {})
        self.model_name = model_config.get('llm_model', 'vivo-llm-chat')
        
        # 参数验证
        if not all([self.app_id, self.app_key]):
            raise ValueError("缺少app_id或app_key配置")
            
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
                "role": "user",                "content": f"""请对以下法律文本摘要进行专业性和严谨性的优化，要求：
                1. 使用准确的法律术语和规范的法律表达方式
                2. 保持客观、严谨的语气，避免口语化表达
                3. 增强句子间的逻辑连贯性，使用恰当的关联词
                4. 确保每个句子都有完整的标点符号（句号、问号、感叹号、分号、冒号等）
                5. 规范使用法律文书中的标点符号，特别是句号的使用
                6. 调整语序和用词，使表述更加清晰、准确
                7. 保持法律文本的庄重性和权威性
                
                原文摘要：
                {summary_text}
                
                请直接返回优化后的文本，无需其他解释。"""
            }
        ]

        # 生成签名头
        headers = gen_sign_headers(
            self.app_id,
            self.app_key,
            'POST',
            self.uri,
            query={}
        )

        try:
            # 发送请求
            response = requests.post(
                f"https://{self.domain}{self.uri}",
                json={
                    "model": self.model_name,
                    "messages": messages,
                    "temperature": 0.3,  # 使用较低的温度以确保输出的一致性和专业性
                    "max_tokens": 2000
                },
                headers=headers,
                timeout=30  # 增加超时时间，因为摘要优化可能需要更长时间
            )
            
            # 解析响应
            response.raise_for_status()
            response_data = response.json()
            
            # 调试日志
            print(f"[LLM API Response] Status: {response.status_code}")
            
            # 提取生成的文本
            if response_data.get('choices') and len(response_data['choices']) > 0:
                optimized_text = response_data['choices'][0].get('message', {}).get('content', '')
                if optimized_text:
                    return optimized_text
                    
            raise ValueError("API响应中没有找到生成的文本")

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"API请求失败: {str(e)}")
        except json.JSONDecodeError:
            raise RuntimeError(f"响应解析失败: {response.text}")
        except Exception as e:
            raise RuntimeError(f"摘要优化失败: {str(e)}")
    
    def __init__(self):
        # 获取vivo_rag_system包的根目录
        package_root = Path(__file__).parent.parent.parent
        config_path = package_root / "config" / "settings.yaml"
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
            
        self.api_config = self.config.get('api_config', {})
        self.base_url = f"https://{self.api_config['domain']}"
        self.app_id = self.api_config['app_id']
        self.app_key = self.api_config['app_key']

        # 加载配置时添加默认值处理
        self.domain = self.api_config.get('domain', 'api-ai.vivo.com.cn')
        self.uri = self.api_config.get('llm_uri', '/llm-api/v1/chat/completions')
        
        model_config = self.config.get('model_config', {})
        self.model_name = model_config.get('llm_model', 'vivo-llm-chat')
        
        # 参数验证
        if not all([self.app_id, self.app_key]):
            raise ValueError("缺少app_id或app_key配置")
            
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

        # 生成签名头
        headers = gen_sign_headers(
            self.app_id,
            self.app_key,
            'POST',
            self.uri,
            query={}
        )

        try:
            # 发送请求
            response = requests.post(
                f"https://{self.domain}{self.uri}",
                json={
                    "model": self.model_name,
                    "messages": messages,
                    "temperature": 0.3,  # 使用较低的温度以确保输出的一致性和专业性
                    "max_tokens": 2000
                },
                headers=headers,
                timeout=30  # 增加超时时间，因为摘要优化可能需要更长时间
            )
            
            # 解析响应
            response.raise_for_status()
            response_data = response.json()
            
            # 调试日志
            print(f"[LLM API Response] Status: {response.status_code}")
            
            # 提取生成的文本            
            if response_data.get('choices') and len(response_data['choices']) > 0:
                optimized_text = response_data['choices'][0].get('message', {}).get('content', '')
                if optimized_text:
                    return optimized_text
                    
            raise ValueError("API响应中没有找到生成的文本")

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"API请求失败: {str(e)}")
        except json.JSONDecodeError:
            raise RuntimeError(f"响应解析失败: {response.text}")
        except Exception as e:
            raise RuntimeError(f"摘要优化失败: {str(e)}")
                    
            raise ValueError("API响应中没有找到生成的文本")

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"API请求失败: {str(e)}")
        except json.JSONDecodeError:
            raise RuntimeError(f"响应解析失败: {response.text}")
        except Exception as e:
            raise RuntimeError(f"摘要优化失败: {str(e)}")
