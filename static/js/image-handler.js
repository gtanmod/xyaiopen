/**
 * 图片处理器
 * 版本: 4.0.0
 * 功能: 处理页面中的图片，包括sediment协议链接以及支持gpt-4o-all图片分析
 */

console.log('图片处理器已初始化，版本4.0.0');

// 初始化函数
(function() {
    console.log('正在设置图片处理器...');
    
    // 页面加载完成后处理图片
    document.addEventListener('DOMContentLoaded', function() {
        processSedimentImagesInPage();
    });
})();

// 打开图片模态框
function openImageModal(imageUrl) {
    try {
        // 检查是否为sediment协议
        if (imageUrl && imageUrl.startsWith('sediment://')) {
            // 尝试获取真实URL
            const realUrl = findRealImageUrl(imageUrl);
            if (realUrl) {
                imageUrl = realUrl;
            } else {
                console.warn('无法解析sediment链接:', imageUrl);
                return;
            }
        }
        
        // 创建模态框
        const modal = document.createElement('div');
        modal.className = 'image-modal';
        modal.style.position = 'fixed';
        modal.style.top = '0';
        modal.style.left = '0';
        modal.style.width = '100%';
        modal.style.height = '100%';
        modal.style.backgroundColor = 'rgba(0, 0, 0, 0.9)';
        modal.style.display = 'flex';
        modal.style.alignItems = 'center';
        modal.style.justifyContent = 'center';
        modal.style.zIndex = '10000';
        modal.style.cursor = 'zoom-out';
        
        // 创建图片元素
        const image = document.createElement('img');
        image.src = imageUrl;
        image.style.maxWidth = '90%';
        image.style.maxHeight = '90%';
        image.style.objectFit = 'contain';
        image.style.borderRadius = '8px';
        image.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.3)';
        
        // 创建控制按钮容器
        const controlsContainer = document.createElement('div');
        controlsContainer.style.position = 'absolute';
        controlsContainer.style.bottom = '20px';
        controlsContainer.style.left = '50%';
        controlsContainer.style.transform = 'translateX(-50%)';
        controlsContainer.style.display = 'flex';
        controlsContainer.style.gap = '10px';
        
        // 添加分析按钮
        const analyzeButton = document.createElement('button');
        analyzeButton.textContent = '分析图片';
        analyzeButton.style.padding = '8px 16px';
        analyzeButton.style.backgroundColor = '#5652BF';
        analyzeButton.style.color = 'white';
        analyzeButton.style.border = 'none';
        analyzeButton.style.borderRadius = '4px';
        analyzeButton.style.cursor = 'pointer';
        analyzeButton.onclick = function(e) {
            e.stopPropagation();
            analyzeImage(imageUrl);
        };
        
        // 添加复制链接按钮
        const copyButton = document.createElement('button');
        copyButton.textContent = '复制链接';
        copyButton.style.padding = '8px 16px';
        copyButton.style.backgroundColor = '#444';
        copyButton.style.color = 'white';
        copyButton.style.border = 'none';
        copyButton.style.borderRadius = '4px';
        copyButton.style.cursor = 'pointer';
        copyButton.onclick = function(e) {
            e.stopPropagation();
            navigator.clipboard.writeText(imageUrl)
                .then(() => {
                    copyButton.textContent = '已复制';
                    setTimeout(() => {
                        copyButton.textContent = '复制链接';
                    }, 2000);
                })
                .catch(err => {
                    console.error('复制失败:', err);
                    copyButton.textContent = '复制失败';
                    setTimeout(() => {
                        copyButton.textContent = '复制链接';
                    }, 2000);
                });
        };
        
        // 添加按钮到容器
        controlsContainer.appendChild(analyzeButton);
        controlsContainer.appendChild(copyButton);
        
        // 点击关闭
        modal.addEventListener('click', function() {
            document.body.removeChild(modal);
        });
        
        // 阻止图片点击事件冒泡
        image.addEventListener('click', function(e) {
            e.stopPropagation();
        });
        
        // 添加到页面
        modal.appendChild(image);
        modal.appendChild(controlsContainer);
        document.body.appendChild(modal);
    } catch (err) {
        console.error("打开图片模态框时出错:", err);
    }
}

// 分析图片
function analyzeImage(imageUrl) {
    console.log('===== 开始分析图片 =====');
    console.log('图片URL:', imageUrl);
    
    // 获取当前输入框元素
    const chatInput = document.getElementById('chatInput');
    if (!chatInput) {
        console.error('找不到聊天输入框元素');
        alert('无法找到聊天输入框');
        return;
    }
    
    // 获取当前选择的模型
    const quickModelSelect = document.getElementById('quickModelSelect');
    const selectedModel = quickModelSelect ? quickModelSelect.value : 'gpt-4o-all';
    console.log('当前选择模型:', selectedModel);
    
    // 不再检查模型是否支持图片分析，直接处理
    // 设置提示语
    const promptText = `这是什么图片？`;
    chatInput.value = promptText;
    chatInput.style.height = 'auto';
    chatInput.style.height = chatInput.scrollHeight + 'px';
    
    // 设置全局对象，用于发送消息时附加图片
    if (typeof window.pendingImageAttachment === 'undefined') {
        window.pendingImageAttachment = [];
    }
    
    // 添加到待处理图片附件列表
    window.pendingImageAttachment.push({
        type: 'image',
        name: 'image_analysis.jpg',
        data: imageUrl
    });
    
    // 激活发送按钮
    const sendButton = document.getElementById('sendButton');
    if (sendButton) {
        sendButton.disabled = false;
    }
    
    // 自动获取焦点
    chatInput.focus();
    
    // 触发更新附件预览的函数（如果存在）
    if (typeof updateAttachmentsPreview === 'function') {
        updateAttachmentsPreview();
    } else {
        console.log('updateAttachmentsPreview函数不存在，无法更新附件预览');
    }
    
    console.log('已准备分析图片，已填充输入框并设置附件');
}

// 处理sediment图片链接
function processSedimentImagesInPage() {
    console.log('开始处理页面中的sediment图片...');
    try {
        // 查找所有带有data-sediment属性的图片
        const sedimentImages = document.querySelectorAll('img[data-sediment]');
        console.log(`找到${sedimentImages.length}个sediment图片`);
        
        sedimentImages.forEach(img => {
            const sedimentUrl = img.getAttribute('data-sediment');
            if (!sedimentUrl) return;
            
            console.log('处理sediment图片:', sedimentUrl);
            
            // 处理加载状态显示
            if (!img.classList.contains('loading-styled')) {
                img.classList.add('loading-styled');
                
                // 设置基本加载样式
                img.style.minHeight = '200px';
                img.style.minWidth = '200px';
                img.style.backgroundColor = '#f8f9fa';
                
                // 添加父容器的加载状态样式
                const container = img.closest('.markdown-image-container');
                if (container) {
                    // 检查是否已有加载指示器
                    if (!container.querySelector('.sediment-loading-indicator')) {
                        const loadingIndicator = document.createElement('div');
                        loadingIndicator.className = 'sediment-loading-indicator';
                        loadingIndicator.style.position = 'absolute';
                        loadingIndicator.style.top = '50%';
                        loadingIndicator.style.left = '50%';
                        loadingIndicator.style.transform = 'translate(-50%, -50%)';
                        loadingIndicator.style.zIndex = '1';
                        loadingIndicator.innerHTML = `
                            <div class="sediment-loading-spinner"></div>
                            <div class="sediment-loading-text">正在加载图片...</div>
                        `;
                        container.appendChild(loadingIndicator);
                    }
                }
            }
            
            // 查找真实URL
            const realUrl = findRealImageUrl(sedimentUrl);
            if (realUrl) {
                console.log('找到真实URL:', realUrl);
                
                // 创建一个新的Image对象来预加载图片
                const preloadImg = new Image();
                preloadImg.onload = function() {
                    // 图片加载成功，更新源
                    img.src = realUrl;
                    img.style.minHeight = '';
                    img.style.minWidth = '';
                    img.style.backgroundColor = '';
                    
                    // 移除加载指示器
                    const container = img.closest('.markdown-image-container');
                    if (container) {
                        const loadingIndicator = container.querySelector('.sediment-loading-indicator');
                        if (loadingIndicator) {
                            container.removeChild(loadingIndicator);
                        }
                    }
                    
                    // 更新点击事件
                    img.onclick = function() {
                        openImageModal(realUrl);
                    };
                };
                
                preloadImg.onerror = function() {
                    // 加载失败，显示错误状态
                    img.src = '/static/images/image-error.svg';
                    img.title = '图片加载失败';
                    img.style.minHeight = '';
                    img.style.minWidth = '';
                    
                    // 更新加载指示器为错误状态
                    const container = img.closest('.markdown-image-container');
                    if (container) {
                        const loadingIndicator = container.querySelector('.sediment-loading-indicator');
                        if (loadingIndicator) {
                            loadingIndicator.innerHTML = `
                                <div style="color: #dc3545;"><i class="fas fa-exclamation-circle"></i></div>
                                <div class="sediment-loading-text" style="color: #dc3545;">图片加载失败</div>
                            `;
                        }
                    }
                };
                
                // 开始加载图片
                preloadImg.src = realUrl;
            } else {
                console.warn('未找到sediment链接对应的真实URL:', sedimentUrl);
                
                // 显示错误状态
                setTimeout(() => {
                    // 如果一段时间后仍未找到真实URL，则显示错误状态
                    if (img.getAttribute('data-sediment') === sedimentUrl) {
                        img.src = '/static/images/image-error.svg';
                        img.title = '无法解析图片链接';
                        img.style.minHeight = '';
                        img.style.minWidth = '';
                        
                        // 更新加载指示器为错误状态
                        const container = img.closest('.markdown-image-container');
                        if (container) {
                            const loadingIndicator = container.querySelector('.sediment-loading-indicator');
                            if (loadingIndicator) {
                                loadingIndicator.innerHTML = `
                                    <div style="color: #dc3545;"><i class="fas fa-exclamation-circle"></i></div>
                                    <div class="sediment-loading-text" style="color: #dc3545;">无法解析图片链接</div>
                                `;
                            }
                        }
                    }
                }, 5000); // 5秒后如果仍未找到，则显示错误
            }
        });
    } catch (err) {
        console.error('处理sediment图片时出错:', err);
    }
}

// 查找sediment协议对应的真实URL
function findRealImageUrl(sedimentUrl) {
    // 检查页面中是否有对应的真实URL
    console.log('尝试查找sediment链接的真实URL:', sedimentUrl);
    
    // 方法0: 检查全局映射表
    if (window.sedimentUrlMap && window.sedimentUrlMap[sedimentUrl]) {
        console.log('从全局映射表中找到真实URL:', window.sedimentUrlMap[sedimentUrl]);
        return window.sedimentUrlMap[sedimentUrl];
    }
    
    // 方法1: 检查图片后的超链接文本
    const sedimentId = sedimentUrl.split('://')[1];
    
    // 查找页面中所有包含此ID的文本节点
    const textNodes = [];
    function findTextNodes(node) {
        if (node.nodeType === Node.TEXT_NODE) {
            if (node.textContent.includes(sedimentId)) {
                textNodes.push(node);
            }
        } else {
            for (let i = 0; i < node.childNodes.length; i++) {
                findTextNodes(node.childNodes[i]);
            }
        }
    }
    
    findTextNodes(document.body);
    console.log(`找到${textNodes.length}个包含ID的文本节点`);
    
    // 在文本节点中查找https链接
    for (const node of textNodes) {
        const text = node.textContent;
        const urlMatch = text.match(/(https:\/\/[^\s"]+)/);
        if (urlMatch && urlMatch[1]) {
            console.log('从文本中找到真实URL:', urlMatch[1]);
            return urlMatch[1];
        }
    }
    
    // 方法2: 检查Markdown语法中的图片链接
    const markdownElements = document.querySelectorAll('.markdown-content, .message-content');
    for (const elem of markdownElements) {
        const html = elem.innerHTML;
        const pattern = new RegExp(`!\\[${sedimentId}\\]\\((https://[^)]+)\\)`, 'i');
        const match = html.match(pattern);
        if (match && match[1]) {
            console.log('从Markdown语法中找到真实URL:', match[1]);
            return match[1];
        }
    }
    
    // 方法3: 查找特定格式的图片链接对
    const messageContents = document.querySelectorAll('.message-content');
    for (const elem of messageContents) {
        const text = elem.textContent;
        if (text.includes(sedimentId)) {
            const httpsMatch = text.match(/https:\/\/filesystem\.site\/cdn\/[^\s)]+/);
            if (httpsMatch) {
                console.log('找到filesystem.site URL:', httpsMatch[0]);
                return httpsMatch[0];
            } else {
                // 扩展搜索其他域名的图片URL
                const otherImageMatch = text.match(/(https:\/\/[^\s)]+\.(jpg|jpeg|png|gif|webp))/i);
                if (otherImageMatch) {
                    console.log('找到其他图片URL:', otherImageMatch[0]);
                    return otherImageMatch[0];
                }
            }
        }
    }
    
    console.log('未找到真实URL');
    return null;
}

// 添加全局属性，使其在聊天页面脚本中可用
function setupImageAnalysisData() {
    // 检查是否存在模型特性数据
    if (typeof modelFeatures === 'undefined') {
        window.modelFeatures = {};
    }
    
    // 获取所有模型列表
    const modelSelects = document.querySelectorAll('#quickModelSelect option, #modelSelect option');
    if (modelSelects && modelSelects.length > 0) {
        console.log(`收集到${modelSelects.length}个模型选项`);
        
        // 遍历所有模型，确保支持图片分析
        modelSelects.forEach(option => {
            const modelId = option.value;
            if (modelId && typeof modelFeatures[modelId] === 'undefined') {
                // 新模型添加默认支持
                modelFeatures[modelId] = {
                    supports_stream: true,
                    supports_image_analysis: true,  // 所有模型都支持图片分析
                    supports_file_analysis: false,
                    supports_web_search: false,
                    max_context_length: 16000
                };
                console.log(`为模型 ${modelId} 添加默认特性支持`);
            } else if (modelId && modelFeatures[modelId]) {
                // 确保现有模型支持图片分析
                modelFeatures[modelId].supports_image_analysis = true;
            }
        });
    }
    
    // 确保常用模型支持图片分析
    const commonModels = ['gpt-4o-all', 'gpt-4o', 'gpt-4-turbo', 'gpt-4', 'gpt-3.5-turbo'];
    commonModels.forEach(modelId => {
        if (typeof modelFeatures[modelId] === 'undefined') {
            modelFeatures[modelId] = {
                supports_stream: true,
                supports_image_analysis: true,
                supports_file_analysis: modelId.includes('gpt-4o'),
                supports_web_search: modelId.includes('gpt-4o'),
                max_context_length: modelId.includes('gpt-4o') ? 128000 : 16000
            };
        } else {
            modelFeatures[modelId].supports_image_analysis = true;
        }
    });
    
    console.log('图片分析数据初始化完成，所有模型均已支持图片分析');
}

// 在页面加载时设置图片分析数据
document.addEventListener('DOMContentLoaded', setupImageAnalysisData);

// 导出函数供其他脚本使用
window.processSedimentImagesInPage = processSedimentImagesInPage;
window.findRealImageUrl = findRealImageUrl;
window.openImageModal = openImageModal;
window.analyzeImage = analyzeImage; 