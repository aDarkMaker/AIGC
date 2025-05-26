document.addEventListener('DOMContentLoaded', () => {
    // 初始化UI元素
    const elements = {
        fileInput: document.getElementById('fileInput'),
        fileName: document.getElementById('fileName'),
        textInput: document.getElementById('textInput'),
        analyzeBtn: document.getElementById('analyzeBtn'),
        analysisType: document.getElementById('analysisType'),
        professionalKnowledgeBase: document.getElementById('professionalKnowledgeBase'), // 新增
        messageContainer: document.getElementById('messageContainer'),
        results: {
            keywords: document.getElementById('keywordsResult'),
            summary: document.getElementById('summaryResult'),
            legal: document.getElementById('legalResult'),
            riskLevel: document.querySelector('.risk-level'),
            riskScore: document.getElementById('riskScore')
        }
    };

    // 文件处理
    elements.fileInput.addEventListener('change', handleFileSelection);

    // 分析按钮处理
    elements.analyzeBtn.addEventListener('click', handleAnalysis);

    // 处理文件选择
    async function handleFileSelection(e) {
        const file = e.target.files[0];
        if (!file) {
            elements.fileName.textContent = '未选择文件';
            return;
        }

        // 验证文件类型
        const validTypes = ['.txt', '.doc', '.docx'];
        const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
        if (!validTypes.includes(fileExtension)) {
            showMessage('请选择有效的文本文件 (.txt, .doc, .docx)', 'error');
            elements.fileInput.value = '';
            elements.fileName.textContent = '未选择文件';
            return;
        }

        elements.fileName.textContent = file.name;

        try {
            const text = await readFile(file);
            elements.textInput.value = text;
        } catch (error) {
            showMessage('读取文件时出错：' + error.message, 'error');
        }
    }

    // 读取文件内容
    function readFile(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = (e) => reject(new Error('文件读取失败'));
            reader.readAsText(file);
        });
    }

    // 处理分析请求
    async function handleAnalysis() {
        const text = elements.textInput.value.trim();
        if (!text) {
            showMessage('请输入要分析的文本！', 'error');
            return;
        }

        showLoading(true);
        resetResults();

        let retryCount = 0;
        const maxRetries = 3;
        const retryDelay = 1000; // 1秒

        while (retryCount < maxRetries) {
            try {
                const response = await fetch('http://127.0.0.1:5000/analyze', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        text: text,
                        domain: elements.analysisType.value,
                        use_professional_kb: elements.professionalKnowledgeBase.checked // 新增
                    })
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || '服务器响应错误');
                }

                const result = await response.json();
                updateResults(result);
                break;

            } catch (error) {
                console.error('分析出错:', error);
                retryCount++;
                
                if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
                    if (retryCount < maxRetries) {
                        showMessage(`服务器连接失败，正在尝试第${retryCount}次重连...`, 'info');
                        await new Promise(resolve => setTimeout(resolve, retryDelay));
                        continue;
                    }
                    showMessage('无法连接到服务器，请确保服务器已启动并运行在正确的端口(5000)上', 'error');
                } else {
                    showMessage(`分析过程出现错误：${error.message}`, 'error');
                }
                resetResults();
            } finally {
                showLoading(false);
            }
        }
    }

    // 更新分析结果显示
    function updateResults(result) {
        try {
            // 更新关键词
            if (result.rag_analysis?.keywords) {
                elements.results.keywords.innerHTML = result.rag_analysis.keywords
                    .map(keyword => `<span class="keyword-tag">${escapeHtml(keyword)}</span>`)
                    .join('');
            }

            // 更新摘要
            if (result.rag_analysis?.summary) {
                elements.results.summary.innerHTML = result.rag_analysis.summary
                    .map(line => `<p>${escapeHtml(line)}</p>`)
                    .join('');
            }

            // 更新法律分析
            if (result.legal_analysis) {
                const compliance = result.legal_analysis.compliance || {};
                const recommendations = result.legal_analysis.recommendations || {};
                
                let legalContent = '<div class="legal-details">';
                
                // 适用法律
                if (compliance.applicable_laws) {
                    legalContent += `
                        <div class="legal-item">
                            <strong>适用法律：</strong>
                            <ul>${compliance.applicable_laws.map(law => 
                                `<li>${escapeHtml(law)}</li>`).join('')}
                            </ul>
                        </div>`;
                }
                
                // 合规评估
                if (compliance.compliance_score !== undefined) {
                    legalContent += `
                        <div class="legal-item">
                            <strong>合规评估：</strong>
                            <p>合规得分：${(compliance.compliance_score * 100).toFixed(1)}%</p>
                            <p>风险等级：${compliance.risk_level || '未知'}</p>
                        </div>`;
                }
                
                // 总体评价和建议
                if (recommendations.general_assessment || recommendations.specific_recommendations) {
                    legalContent += `
                        <div class="legal-item">
                            <strong>专业建议：</strong>
                            ${recommendations.general_assessment ? 
                              `<p class="assessment">${escapeHtml(recommendations.general_assessment)}</p>` : ''}
                            ${recommendations.specific_recommendations ? `
                                <ul class="recommendations">
                                    ${recommendations.specific_recommendations.map(rec => 
                                        `<li>${escapeHtml(rec)}</li>`).join('')}
                                </ul>` : ''}
                        </div>`;
                }
                
                legalContent += '</div>';
                elements.results.legal.innerHTML = legalContent;

                // 更新风险评估
                let riskScoreValue = result.legal_analysis?.compliance?.compliance_score;
                // 将合规分数转换为风险分数 (0-100 范围)
                // 如果 compliance_score 未定义或为 null，则默认为 0，对应风险评分为 100
                let calculatedRiskScore = 100 - (riskScoreValue === undefined || riskScoreValue === null ? 0 : riskScoreValue);
                
                elements.results.riskLevel.style.width = `${calculatedRiskScore}%`;
                // getRiskColor 的参数应该是合规分数 (越高越好)，或者调整 getRiskColor 使其接受风险分数
                // 当前 getRiskColor 接受的是合规分 (100 - calculatedRiskScore)
                elements.results.riskLevel.style.backgroundColor = getRiskColor(100 - calculatedRiskScore); 
                elements.results.riskScore.textContent = `风险评分：${calculatedRiskScore.toFixed(1)}%`;

                // 添加风险等级过渡动画
                elements.results.riskLevel.style.transition = 'width 1s ease-in-out, background-color 1s ease-in-out';
            }
        } catch (error) {
            console.error('更新结果时出错:', error);
            showMessage('显示分析结果时出错，请重试', 'error');
        }
    }

    // 重置结果显示
    function resetResults() {
        elements.results.keywords.innerHTML = '';
        elements.results.summary.innerHTML = '';
        elements.results.legal.innerHTML = '';
        elements.results.riskLevel.style.width = '0%';
        elements.results.riskScore.textContent = '风险评分：-';
    }

    // 显示消息提示
    function showMessage(message, type = 'info') {
        const messageDiv = document.createElement('div');
        messageDiv.className = `${type}-message`;
        messageDiv.textContent = message;
        
        elements.messageContainer.innerHTML = '';
        elements.messageContainer.appendChild(messageDiv);
        
        // 如果不是错误消息，3秒后自动消失
        if (type !== 'error') {
            setTimeout(() => messageDiv.remove(), 3000);
        }
    }

    // 显示/隐藏加载状态
    function showLoading(isLoading) {
        elements.analyzeBtn.disabled = isLoading;
        elements.analyzeBtn.innerHTML = isLoading ? 
            '<span class="loading-spinner"></span>分析中...' : 
            '开始分析';
    }

    // 获取风险等级对应的颜色
    function getRiskColor(score) {
        if (score >= 80) return '#27ae60';  // 绿色 - 低风险
        if (score >= 60) return '#f1c40f';  // 黄色 - 中等风险
        return '#e74c3c';  // 红色 - 高风险
    }

    // HTML转义函数
    function escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
});

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

document.getElementById('fileInput').addEventListener('change', function(e) {
    const fileName = e.target.files[0] ? e.target.files[0].name : '未选择文件';
    document.getElementById('fileName').textContent = fileName;
});