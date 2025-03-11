import requests
import yaml
from ..utils.auth_util import gen_sign_headers

class VivoEmbeddingAPI:
    def __init__(self, config_path="./config/settings.yaml"):
        with open(config_path) as f:
            config = yaml.safe_load(f)
            api_config = config['api_config']
            model_config = config['model_config']

        self.app_id = api_config['app_id']
        self.app_key = api_config['app_key']
        self.domain = api_config['domain']
        self.uri = api_config['embedding_uri']
        self.model_name = model_config['embedding_model']

    def get_embeddings(self, texts):
        """批量获取嵌入向量"""
        headers = gen_sign_headers(
            self.app_id, 
            self.app_key, 
            'POST', 
            self.uri, 
            {}
        )
        
        response = requests.post(
            f"https://{self.domain}{self.uri}",
            json={
                "model_name": self.model_name,
                "sentences": texts
            },
            headers=headers
        )
        
        if response.status_code == 200:
            return response.json()['data']
        raise Exception(f"API Error: {response.status_code} - {response.text}")