from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sys
from pathlib import Path
import traceback
import json
import os

# 添加项目根目录到系统路径
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))

from main import IntegratedAnalysisSystem

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)  # 启用跨域请求支持

# 初始化分析系统
try:
    analysis_system = IntegratedAnalysisSystem()
except Exception as e:
    print(f"初始化分析系统失败: {str(e)}")
    sys.exit(1)

@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('favicon.ico')

@app.route('/')
def home():
    return app.send_static_file('index.html')

@app.route('/analyze', methods=['POST', 'OPTIONS'])
def analyze():
    if request.method == 'OPTIONS':
        # 处理预检请求
        response = app.make_default_options_response()
        response.headers['Access-Control-Allow-Methods'] = 'POST'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
        
    try:
        # 验证请求数据
        data = request.get_json()
        if not data:
            return jsonify({
                'error': '无效的请求数据',
                'detail': '请求体必须是JSON格式'
            }), 400
            
        if 'text' not in data:
            return jsonify({
                'error': '缺少必要参数',
                'detail': '请提供要分析的文本(text字段)'
            }), 400
            
        text = data['text'].strip()
        if not text:
            return jsonify({
                'error': '无效的输入',
                'detail': '文本内容不能为空'
            }), 400

        # 获取分析领域，默认为privacy
        domain = data.get('domain', 'privacy')
        use_professional_kb = data.get('use_professional_kb', False) # 新增

        if domain not in ['privacy', 'intellectual_property', 'contract']:
            return jsonify({
                'error': '无效的分析领域',
                'detail': '支持的领域: privacy, intellectual_property, contract'
            }), 400
        
        # 执行分析
        try:
            # 根据是否启用专业知识库，调用不同的分析方法或传递参数
            results = analysis_system.analyze_document(text, domain, use_professional_kb=use_professional_kb)
            
            # 验证结果格式
            if not isinstance(results, dict):
                raise ValueError('分析结果格式无效')
                
            # 确保结果包含必要的字段
            required_fields = {
                'rag_analysis': ['keywords', 'summary'],
                'legal_analysis': ['compliance', 'recommendations']
            }
            
            for section, fields in required_fields.items():
                if section not in results:
                    results[section] = {}
                for field in fields:
                    if field not in results[section]:
                        results[section][field] = None
            
            return jsonify(results)
            
        except Exception as analysis_error:
            # 记录详细错误信息
            error_detail = traceback.format_exc()
            print(f"分析过程错误: {error_detail}")
            
            return jsonify({
                'error': '分析处理失败',
                'detail': {
                    'message': str(analysis_error),
                    'type': type(analysis_error).__name__
                }
            }), 500
        
    except json.JSONDecodeError:
        return jsonify({
            'error': 'JSON解析错误',
            'detail': '请求数据必须是有效的JSON格式'
        }), 400
        
    except Exception as e:
        # 记录未预期的错误
        error_detail = traceback.format_exc()
        print(f"未预期的错误: {error_detail}")
        
        return jsonify({
            'error': '服务器内部错误',
            'detail': {
                'message': str(e),
                'type': type(e).__name__
            }
        }), 500

@app.errorhandler(404)
def not_found(e):
    return jsonify({
        'error': '资源不存在',
        'detail': '请求的页面或资源未找到'
    }), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({
        'error': '方法不允许',
        'detail': '不支持该HTTP请求方法'
    }), 405

@app.errorhandler(500)
def internal_server_error(e):
    return jsonify({
        'error': '服务器内部错误',
        'detail': '服务器处理请求时发生错误'
    }), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)