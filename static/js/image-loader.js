/**
 * 图片加载器
 * 版本: 3.0.0
 * 功能: 页面加载和内容变化时自动处理图片
 */

console.log('图片加载器已初始化，版本3.0.0');

// 初始化函数
(function() {
    console.log('正在设置图片加载器...');
    
    // 页面加载完成后处理图片
    document.addEventListener('DOMContentLoaded', function() {
        setTimeout(function() {
            processImagesInPage();
            setupImageObserver();
            setupAttachmentHandlers();
        }, 500);
    });
})();

// 处理页面中的所有图片
function processImagesInPage() {
    console.log('开始处理页面中的所有图片...');
    
    try {
        // 处理sediment协议图片
        if (typeof window.processSedimentImagesInPage === 'function') {
            window.processSedimentImagesInPage();
        } else {
            console.log('processSedimentImagesInPage函数不存在，无法处理sediment图片');
        }
        
        // 处理特殊格式的图片链接，如![sediment://file_xxx](https://example.com/image.png)
        processSedimentMarkdownPairs();
    } catch (err) {
        console.error('处理页面图片时出错:', err);
    }
}

// 设置图片观察器，监听DOM变化
function setupImageObserver() {
    console.log('设置图片观察器...');
    
    try {
        // 创建一个MutationObserver监听DOM变化
        const observer = new MutationObserver(function(mutations) {
            let shouldProcessImages = false;
            
            for (const mutation of mutations) {
                // 检查是否有新增节点
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    shouldProcessImages = true;
                    break;
                }
            }
            
            if (shouldProcessImages) {
                console.log('检测到DOM变化，准备处理图片...');
                processImagesInPage();
            }
        });
        
        // 配置观察器
        const config = { 
            childList: true, 
            subtree: true 
        };
        
        // 开始观察
        observer.observe(document.body, config);
        console.log('图片观察器已启动');
    } catch (err) {
        console.error('设置图片观察器时出错:', err);
    }
}

// 处理Markdown格式的sediment协议和https链接对
function processSedimentMarkdownPairs() {
    console.log('开始处理Markdown格式的sediment链接对...');
    
    try {
        // 查找所有消息内容
        const messageContents = document.querySelectorAll('.message-content');
        
        messageContents.forEach(content => {
            // 检查内容是否包含sediment协议
            if (!content.textContent.includes('sediment://')) return;
            
            const html = content.innerHTML;
            // 查找格式为![sediment://file_xxx](https://example.com/image.png)的内容
            const regex = /!\[(.*?)\]\((sediment:\/\/[^\)]+)\)/g;
            
            let match;
            let hasMatches = false;
            
            // 使用exec方法逐个查找匹配项
            while ((match = regex.exec(html)) !== null) {
                hasMatches = true;
                const sedimentUrl = match[2];
                
                console.log('找到sediment和https链接对:', sedimentUrl);
                
                // 将sedimentUrl和httpsUrl关联起来，方便后续查找
                if (typeof window.sedimentUrlMap === 'undefined') {
                    window.sedimentUrlMap = {};
                }
                window.sedimentUrlMap[sedimentUrl] = match[0];
            }
            
            // 如果找到匹配项，触发一次sediment图片处理
            if (hasMatches && typeof window.processSedimentImagesInPage === 'function') {
                console.log('触发sediment图片处理...');
                setTimeout(window.processSedimentImagesInPage, 100);
            }
        });
    } catch (err) {
        console.error('处理Markdown格式的sediment链接对时出错:', err);
    }
}

// 设置附件处理函数
function setupAttachmentHandlers() {
    try {
        // 初始化所有附件对象
        if (typeof window.pendingImageAttachment === 'undefined') {
            window.pendingImageAttachment = [];
        }
        
        // 添加发送消息前的处理函数
        document.addEventListener('beforeSendMessage', function(e) {
            const detail = e.detail || {};
            const request = detail.request;
            
            // 检查是否有待发送的图片附件
            if (window.pendingImageAttachment && window.pendingImageAttachment.length > 0) {
                console.log(`检测到${window.pendingImageAttachment.length}个待发送的图片附件`);                
                
                // 选择模型
                const selectedModel = document.getElementById('quickModelSelect') ? 
                                      document.getElementById('quickModelSelect').value : 
                                      'gpt-4o-all';
                
                // 所有模型都支持图片分析，不再检查模型特性
                
                if (request) {
                    console.log('原始请求格式:', JSON.stringify(request, null, 2));
                    
                    // 在所有模型上统一处理图片
                    console.log('处理图片附件，准备添加到消息中');
                    
                    // 根据请求结构适配不同的处理方式
                    if (request.message) {
                        // 简单message格式
                        const contentArray = [];
                        
                        // 添加文本内容
                        if (typeof request.message === 'string') {
                            contentArray.push({
                                type: 'text',
                                text: request.message
                            });
                        }
                        
                        // 添加图片附件
                        for (const attachment of window.pendingImageAttachment) {
                            if (attachment.type === 'image') {
                                contentArray.push({
                                    type: 'image_url',
                                    image_url: {
                                        url: attachment.data,
                                        detail: 'auto'
                                    }
                                });
                                console.log('添加图片URL到消息:', attachment.data);
                            }
                        }
                        
                        // 更新请求格式
                        request.message = {
                            role: 'user',
                            content: contentArray
                        };
                        
                        console.log('更新后的请求格式 (message):', JSON.stringify(request.message, null, 2));
                    } else if (request.messages && Array.isArray(request.messages)) {
                        // messages数组格式
                        const lastIndex = request.messages.length - 1;
                        if (lastIndex >= 0) {
                            const lastMessage = request.messages[lastIndex];
                            
                            // 如果最后一条消息是用户的
                            if (lastMessage && lastMessage.role === 'user') {
                                // 准备内容数组
                                const contentArray = [];
                                
                                // 添加文本内容
                                if (lastMessage.content) {
                                    contentArray.push({
                                        type: 'text',
                                        text: lastMessage.content
                                    });
                                }
                                
                                // 添加图片附件
                                for (const attachment of window.pendingImageAttachment) {
                                    if (attachment.type === 'image') {
                                        contentArray.push({
                                            type: 'image_url',
                                            image_url: {
                                                url: attachment.data,
                                                detail: 'auto'
                                            }
                                        });
                                        console.log('添加图片URL到消息:', attachment.data);
                                    }
                                }
                                
                                // 合并内容数组
                                lastMessage.content = contentArray;
                                console.log('更新后的请求格式 (messages):', JSON.stringify(lastMessage.content, null, 2));
                            }
                        }
                    } else {
                        // 如果是其他格式，创建一个兼容格式
                        request.content = request.content || [];
                        if (!Array.isArray(request.content)) {
                            request.content = [{ type: 'text', text: String(request.content) }];
                        }
                        
                        // 添加图片附件
                        for (const attachment of window.pendingImageAttachment) {
                            if (attachment.type === 'image') {
                                request.content.push({
                                    type: 'image_url',
                                    image_url: {
                                        url: attachment.data,
                                        detail: 'auto'
                                    }
                                });
                                console.log('添加图片URL到其他格式消息:', attachment.data);
                            }
                        }
                        
                        console.log('更新后的请求格式 (其他):', JSON.stringify(request.content, null, 2));
                    }
                } else {
                    console.warn('未找到请求对象，无法添加图片附件');
                }
                
                // 清理待发送的附件
                window.pendingImageAttachment = [];
            }
        });
        
        console.log('附件处理函数设置完成');
    } catch (err) {
        console.error('设置附件处理函数时出错:', err);
    }
}

// 导出函数供其他脚本使用
window.processImagesInPage = processImagesInPage;
window.setupImageObserver = setupImageObserver; 