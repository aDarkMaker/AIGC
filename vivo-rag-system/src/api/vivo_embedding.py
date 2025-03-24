import requests
import yaml
from datetime import datetime
import hashlib
import hmac
import base64
from ..utils.auth_util import gen_sign_headers  # 假设这是正确实现的签名方法
import os
import json
import logging

class VivoEmbeddingAPI:
    def __init__(self, config_path="./config/settings.yaml"):
        with open(config_path) as f:
            config = yaml.safe_load(f)
            api_config = config['api_config']
            model_config = config['model_config']

        # 加载配置时添加默认值处理
        self.app_id = api_config.get('app_id') or os.getenv("VIVO_APP_ID")
        self.app_key = api_config.get('app_key') or os.getenv("VIVO_APP_KEY")
        self.domain = api_config.get('domain', 'api.vivo.ai')  # 默认值
        self.uri = api_config.get('embedding_uri', '/v1/embeddings')
        self.model_name = model_config.get('embedding_model', 'text-embedding-3-small')

        # 参数验证
        if not all([self.app_id, self.app_key]):
            raise ValueError("缺少app_id或app_key配置")

    def get_embeddings(self, texts):
        """批量获取嵌入向量（带完整错误处理）"""
        if not isinstance(texts, list) or len(texts) == 0:
            raise ValueError("texts必须是非空列表")

        # 生成签名头
        request_body = {
                        "model_name": self.model_name,
                        "sentences": texts
                    }
        body_bytes = hashlib.sha256(json.dumps(request_body).encode()).digest()

        body_hash = base64.b64encode(body_bytes).decode('utf-8')
        
        headers = gen_sign_headers(
                        self.app_id,
                        self.app_key,
                        'POST',
                        self.uri,
                        query={},  # 假设没有 URL 查询参数
                        body_hash=body_hash  # 关键：传递请求体哈希
                    )

        try:
            # 发送请求
            response = requests.post(
                f"https://{self.domain}{self.uri}",
                json=request_body,
                headers=headers,
                timeout=10
            )
            
            # 解析响应
            response.raise_for_status()
            response_data = response.json()

            # 调试日志
            print(f"[API Response] {response_data}")

            # 业务状态码检查（假设API返回结构）
            if response_data.get('code') != 0:
                raise ValueError(f"业务错误: {response_data.get('msg')}")

            # 安全访问data字段
            embeddings = response_data.get('data')
            if not embeddings:
                raise ValueError("响应中缺少嵌入数据")
                
            return embeddings

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"API请求失败: {str(e)}")
        except json.JSONDecodeError:
            raise RuntimeError(f"响应解析失败: {response.text}")