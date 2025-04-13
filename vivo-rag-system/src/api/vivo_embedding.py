import requests
import yaml
from ..utils.auth_util import gen_sign_headers
import os
import json

class VivoEmbeddingAPI:
    def __init__(self, config_path="./config/settings.yaml"):
        with open(config_path) as f:
            config = yaml.safe_load(f)
            api_config = config['api_config']
            model_config = config['model_config']

        # 加载配置时添加默认值处理
        self.app_id = api_config.get('app_id') or os.getenv("VIVO_APP_ID")
        self.app_key = api_config.get('app_key') or os.getenv("VIVO_APP_KEY")
        self.domain = api_config.get('domain', 'api-ai.vivo.com.cn')
        self.uri = api_config.get('embedding_uri', '/embedding-model-api/predict/batch')
        self.model_name = model_config.get('embedding_model', 'm3e-base')

        # 参数验证
        if not all([self.app_id, self.app_key]):
            raise ValueError("缺少app_id或app_key配置")

    def get_embeddings(self, texts):
        """批量获取嵌入向量（带完整错误处理）"""
        if not isinstance(texts, list) or len(texts) == 0:
            raise ValueError("texts必须是非空列表")

        # 生成签名头
        headers = gen_sign_headers(
            self.app_id,
            self.app_key,
            'POST',
            self.uri,
            query={}  # 传递空字典作为查询参数
        )

        try:
            # 发送请求
            response = requests.post(
                f"https://{self.domain}{self.uri}",
                json={
                    "model_name": self.model_name,
                    "sentences": texts
                },
                headers=headers,
                timeout=10
            )
            
            # 解析响应
            response.raise_for_status()
            response_data = response.json()

            # 调试日志
            print(f"[API Response] {response_data}")

            # 安全访问data字段
            embeddings = response_data.get('data')
            if not embeddings:
                raise ValueError("响应中缺少嵌入数据")
                
            return embeddings

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"API请求失败: {str(e)}")
        except json.JSONDecodeError:
            raise RuntimeError(f"响应解析失败: {response.text}")