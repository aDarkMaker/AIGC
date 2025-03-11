import requests
from auth_util import gen_sign_headers
import jieba.analyse
from snownlp import SnowNLP

APP_ID = '2025344415'
APP_KEY = 'qleYQdctZHIbopVc'
DOMAIN = 'api-ai.vivo.com.cn'
URI = '/embedding-model-api/predict/batch'
METHOD = 'POST'

def extract_keywords(text, topK=5):
    """使用TF-IDF算法提取关键词"""
    return jieba.analyse.extract_tags(
        text, 
        topK=topK,
        withWeight=False,
        allowPOS=('n', 'vn', 'v', 'ns', 'nr') 
    )

def generate_summary(text, sentences_num=3):
    """使用TextRank算法生成摘要"""
    s = SnowNLP(text)
    return '。'.join([sent for sent in s.summary(sentences_num)])

def process_text(text):
    """综合处理文本并返回结果"""
    keywords = extract_keywords(text)
    
    summary = generate_summary(text)
    
    instruction_text = "为这个句子生成表示以用于检索相关文章：" + text
    
    return {
        "keywords": keywords,
        "summary": summary,
        "instruction_text": instruction_text
    }

def embedding():
    user_input = input("请输入需要分析的文本：").strip()
    
    results = process_text(user_input)
    
    print("\n分析结果：")
    print(f"关键词：{', '.join(results['keywords'])}")
    print(f"主要内容：{results['summary']}")
    
    post_data = {
        "model_name": "bge-base-zh",
        "sentences": [results['instruction_text']]
    }
    headers = gen_sign_headers(APP_ID, APP_KEY, METHOD, URI, {})
    
    url = f'https://{DOMAIN}{URI}'
    response = requests.post(url, json=post_data, headers=headers)
    if response.status_code == 200:
        print("\n向量结果：", response.json())
    else:
        print("\nAPI调用失败：", response.status_code, response.text)

if __name__ == '__main__':
    embedding()