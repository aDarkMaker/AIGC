document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('fileInput');
    const fileName = document.getElementById('fileName');
    const textInput = document.getElementById('textInput');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const analysisType = document.getElementById('analysisType');

    // 文件选择处理
    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            fileName.textContent = file.name;
            const reader = new FileReader();
            reader.onload = (e) => {
                textInput.value = e.target.result;
            };
            reader.readAsText(file);
        } else {
            fileName.textContent = '未选择文件';
        }
    });

    // 分析按钮处理
    analyzeBtn.addEventListener('click', async () => {
        if (!textInput.value.trim()) {
            showError('请输入要分析的文本！');
            return;
        }

        showLoading(true);

        try {
            const response = await fetch('/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text: textInput.value,
                    domain: analysisType.value
                })
            });

            if (!response.ok) {
                throw new Error(response.statusText || '服务器响应错误');
            }

            const result = await response.json();
            updateResults(result);
            showSuccess('分析完成！');
        } catch (error) {
            console.error('分析出错:', error);
            showError('分析过程出现错误，请稍后重试。错误详情：' + error.message);
        } finally {
            showLoading(false);
        }
    });

    // 更新分析结果显示
    function updateResults(result) {
        // 更新关键词
        const keywordsResult = document.getElementById('keywordsResult');
        keywordsResult.innerHTML = result.rag_analysis.keywords
            .map(keyword => `<span class="keyword-tag">${keyword}</span>`)
            .join('');

        // 更新摘要
        const summaryResult = document.getElementById('summaryResult');
        summaryResult.innerHTML = result.rag_analysis.summary
            .map(line => `<p>${line}</p>`)
            .join('');

        // 更新法律分析
        const legalResult = document.getElementById('legalResult');
        const legalAnalysis = result.legal_analysis;
        legalResult.innerHTML = `
            <div class="legal-item">
                <strong>适用法律：</strong>
                <ul>${legalAnalysis.compliance.applicable_laws.map(law => `<li>${law}</li>`).join('')}</ul>
            </div>
            <div class="legal-item">
                <strong>合规性评估：</strong>
                <p>评分：${(legalAnalysis.compliance.compliance_score * 100).toFixed(1)}%</p>
            </div>
            <div class="legal-item">
                <strong>总体评价：</strong>
                <p>${legalAnalysis.recommendations.general_assessment}</p>
            </div>
        `;

        // 更新风险评估
        const riskLevel = document.querySelector('.risk-level');
        const riskScore = document.getElementById('riskScore');
        const riskPercentage = legalAnalysis.compliance.compliance_score * 100;
        riskLevel.style.width = `${riskPercentage}%`;
        riskLevel.style.backgroundColor = getRiskColor(riskPercentage);
        riskScore.textContent = `风险评分：${riskPercentage.toFixed(1)}%`;
    }

    // 根据风险程度返回对应的颜色
    function getRiskColor(score) {
        if (score >= 80) return '#27ae60';  // 绿色 - 低风险
        if (score >= 60) return '#f1c40f';  // 黄色 - 中等风险
        return '#e74c3c';  // 红色 - 高风险
    }
});

// 添加错误提示和加载状态管理
function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    
    const container = document.querySelector('.input-section');
    // 移除已有的错误提示
    const existingError = container.querySelector('.error-message');
    if (existingError) {
        existingError.remove();
    }
    
    container.insertBefore(errorDiv, container.querySelector('button'));
    
    // 3秒后自动消失
    setTimeout(() => errorDiv.remove(), 3000);
}

function showSuccess(message) {
    const successDiv = document.createElement('div');
    successDiv.className = 'success-message';
    successDiv.textContent = message;
    
    const container = document.querySelector('.input-section');
    container.insertBefore(successDiv, container.querySelector('button'));
    
    setTimeout(() => successDiv.remove(), 3000);
}

function showLoading(isLoading) {
    const analyzeBtn = document.getElementById('analyzeBtn');
    if (isLoading) {
        analyzeBtn.disabled = true;
        analyzeBtn.innerHTML = '<span class="loading-spinner"></span> 分析中...';
    } else {
        analyzeBtn.disabled = false;
        analyzeBtn.textContent = '开始分析';
    }
}

// 添加关键词标签样式
const style = document.createElement('style');
style.textContent = `
    .keyword-tag {
        display: inline-block;
        background: #e8f0fe;
        color: #1a73e8;
        padding: 4px 8px;
        border-radius: 12px;
        margin: 4px;
        font-size: 0.9rem;
    }

    .legal-item {
        margin-bottom: 1rem;
    }

    .legal-item ul {
        list-style-type: none;
        padding-left: 1rem;
    }

    .legal-item li {
        margin: 0.5rem 0;
    }

    .error-message {
        background-color: #fee2e2;
        color: #dc2626;
        padding: 12px;
        border-radius: 6px;
        margin-bottom: 12px;
        animation: slideIn 0.3s ease;
    }

    .success-message {
        background-color: #ecfdf5;
        color: #059669;
        padding: 12px;
        border-radius: 6px;
        margin-bottom: 12px;
        animation: slideIn 0.3s ease;
    }

    .loading-spinner {
        display: inline-block;
        width: 16px;
        height: 16px;
        border: 2px solid #ffffff;
        border-radius: 50%;
        border-top-color: transparent;
        margin-right: 8px;
        animation: spin 1s linear infinite;
    }

    @keyframes slideIn {
        from {
            transform: translateY(-10px);
            opacity: 0;
        }
        to {
            transform: translateY(0);
            opacity: 1;
        }
    }

    @keyframes spin {
        to {
            transform: rotate(360deg);
        }
    }
`;
document.head.appendChild(style);