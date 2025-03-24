import random
import string
import time
import hashlib
import hmac
import base64
import urllib.parse

__all__ = ['gen_sign_headers']

def gen_nonce(length=8):
    chars = string.ascii_lowercase + string.digits  # 仅小写字母和数字
    return ''.join(random.choices(chars, k=length))

def gen_canonical_query_string(params):
    if not params:
        return ""
    encoded_params = []
    for key in sorted(params.keys()):
        encoded_key = urllib.parse.quote(str(key), safe='')
        encoded_value = urllib.parse.quote(str(params.get(key, "")), safe='')
        encoded_params.append(f"{encoded_key}={encoded_value}")
    return "&".join(encoded_params)

def gen_signature(app_secret, signing_string):
    sign_bytes = hmac.new(
        app_secret.encode('utf-8'),
        signing_string.encode('utf-8'),
        hashlib.sha256
    ).digest()
    return base64.urlsafe_b64encode(sign_bytes).decode('utf-8')  # 保留等号

def gen_sign_headers(app_id, app_key, method, uri, query):
    method = str(method).upper()
    timestamp = str(int(time.time()))
    nonce = gen_nonce()
    canonical_query_string = gen_canonical_query_string(query)
    
    signed_headers_string = (
        f'x-ai-gateway-app-id:{app_id}\n'
        f'x-ai-gateway-timestamp:{timestamp}\n'
        f'x-ai-gateway-nonce:{nonce}'
    )
    
    signing_string = (
        f"{method}\n{uri}\n{canonical_query_string}\n"
        f"{app_id}\n{timestamp}\n{signed_headers_string}"
    )
    
    # 调试输出
    print("[DEBUG] Signing String (Raw):\n", repr(signing_string))
    
    signature = gen_signature(app_key, signing_string)
    return {
        'X-AI-GATEWAY-APP-ID': app_id,
        'X-AI-GATEWAY-TIMESTAMP': timestamp,
        'X-AI-GATEWAY-NONCE': nonce,
        'X-AI-GATEWAY-SIGNED-HEADERS': 'x-ai-gateway-app-id;x-ai-gateway-timestamp;x-ai-gateway-nonce',
        'X-AI-GATEWAY-SIGNATURE': signature
    }