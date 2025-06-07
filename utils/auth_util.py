"""身份验证工具模块

提供生成API认证头信息的工具类和函数。
"""

import random
import string
import time
import hashlib
import hmac
import base64
import urllib.parse
import logging
from typing import Dict, Optional

# 配置日志记录器
logger = logging.getLogger(__name__)

class AuthenticationError(Exception):
    """认证相关错误"""
    pass

class SignatureGenerator:
    """签名生成器类"""
    
    def __init__(self):
        self.nonce_length = 8
    
    def gen_nonce(self, length: Optional[int] = None) -> str:
        """生成随机nonce值
        
        Args:
            length: nonce长度,默认为8
            
        Returns:
            生成的nonce字符串
        """
        length = length or self.nonce_length
        chars = string.ascii_lowercase + string.digits
        return ''.join(random.choices(chars, k=length))
    
    def gen_canonical_query_string(self, params: Optional[Dict] = None) -> str:
        """生成规范化的查询字符串
        
        Args:
            params: 查询参数字典
            
        Returns:
            规范化的查询字符串
        """
        if not params:
            return ""
        try:
            encoded_params = []
            for key in sorted(params.keys()):
                encoded_key = urllib.parse.quote(str(key), safe='')
                encoded_value = urllib.parse.quote(str(params.get(key, "")), safe='')
                encoded_params.append(f"{encoded_key}={encoded_value}")
            return "&".join(encoded_params)
        except Exception as e:
            logger.error(f"生成规范化查询字符串时出错: {str(e)}")
            raise AuthenticationError(f"生成查询字符串失败: {str(e)}")
    
    def gen_signature(self, app_secret: str, signing_string: str) -> str:
        """生成签名
        
        Args:
            app_secret: 应用密钥
            signing_string: 待签名字符串
            
        Returns:
            生成的签名
        """
        try:
            sign_bytes = hmac.new(
                app_secret.encode('utf-8'),
                signing_string.encode('utf-8'),
                hashlib.sha256
            ).digest()
            return base64.urlsafe_b64encode(sign_bytes).decode('utf-8')
        except Exception as e:
            logger.error(f"生成签名时出错: {str(e)}")
            raise AuthenticationError(f"生成签名失败: {str(e)}")
    
    def gen_sign_headers(
        self, 
        app_id: str, 
        app_key: str, 
        method: str, 
        uri: str, 
        query: Optional[Dict] = None
    ) -> Dict[str, str]:
        """生成认证头信息
        
        Args:
            app_id: 应用ID
            app_key: 应用密钥
            method: HTTP方法
            uri: 请求URI
            query: 查询参数字典
            
        Returns:
            包含认证信息的头部字典
        
        Raises:
            AuthenticationError: 生成认证头信息失败时抛出
        """
        try:
            method = str(method).upper()
            timestamp = str(int(time.time()))
            nonce = self.gen_nonce()
            canonical_query_string = self.gen_canonical_query_string(query)
            
            signed_headers_string = (
                f'x-ai-gateway-app-id:{app_id}\n'
                f'x-ai-gateway-timestamp:{timestamp}\n'
                f'x-ai-gateway-nonce:{nonce}'
            )
            
            signing_string = (
                f"{method}\n{uri}\n{canonical_query_string}\n"
                f"{app_id}\n{timestamp}\n{signed_headers_string}"
            )
            
            logger.debug(f"签名字符串: {repr(signing_string)}")
            
            signature = self.gen_signature(app_key, signing_string)
            return {
                'X-AI-GATEWAY-APP-ID': app_id,
                'X-AI-GATEWAY-TIMESTAMP': timestamp,
                'X-AI-GATEWAY-NONCE': nonce,
                'X-AI-GATEWAY-SIGNED-HEADERS': 'x-ai-gateway-app-id;x-ai-gateway-timestamp;x-ai-gateway-nonce',
                'X-AI-GATEWAY-SIGNATURE': signature
            }
        except Exception as e:
            logger.error(f"生成认证头信息时出错: {str(e)}")
            raise AuthenticationError(f"生成认证头信息失败: {str(e)}")

# 导出SignatureGenerator类的实例
signature_generator = SignatureGenerator()
gen_sign_headers = signature_generator.gen_sign_headers

__all__ = ['gen_sign_headers', 'SignatureGenerator', 'AuthenticationError']
