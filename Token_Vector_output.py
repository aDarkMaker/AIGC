import requests
from auth_util import gen_sign_headers

# 请注意替换APP_ID、APP_KEY
APP_ID = '2025344415'
APP_KEY = 'qleYQdctZHIbopVc'
DOMAIN = 'api-ai.vivo.com.cn'
URI = '/embedding-model-api/predict/batch'
METHOD = 'POST'


def embedding():
    params = {}
    post_data = {
        "model_name": "m3e-base",
        "sentences": ["豫章故郡，洪都新府", "星分翼轸，地接衡庐"]
    }
    headers = gen_sign_headers(APP_ID, APP_KEY, METHOD, URI, params)

    url = 'https://{}{}'.format(DOMAIN, URI)
    response = requests.post(url, json=post_data, headers=headers)
    if response.status_code == 200:
        print(response.json())
    else:
        print(response.status_code, response.text)


if __name__ == '__main__':
    embedding()