from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
from pathlib import Path

# 添加项目根目录到系统路径
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))

from main import IntegratedAnalysisSystem

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)  # 启用跨域请求支持

analysis_system = IntegratedAnalysisSystem()

@app.route('/')
def home():
    return app.send_static_file('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': '请提供要分析的文本'}), 400
            
        text = data['text']
        domain = data.get('domain', 'privacy')
        
        # 执行分析
        results = analysis_system.analyze_document(text, domain)
        return jsonify(results)
        
    except Exception as e:
        return jsonify({
            'error': f'分析过程出现错误: {str(e)}',
            'detail': {
                'type': type(e).__name__,
                'message': str(e)
            }
        }), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)