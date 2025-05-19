/**
 * 社区功能的JavaScript功能
 * 处理移动端特有交互和响应式布局
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('社区功能JavaScript已加载');
    
    // 移动端侧边栏切换
    const toggleSidebarBtn = document.getElementById('toggleSidebarBtn');
    const sidebar = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    const mainContent = document.getElementById('mainContent');
    
    if (toggleSidebarBtn && sidebar && mainContent) {
        console.log('侧边栏元素已找到');
        
        toggleSidebarBtn.addEventListener('click', function() {
            sidebar.classList.toggle('sidebar-collapsed');
            mainContent.classList.toggle('main-content-expanded');
            
            const sidebarIcon = document.getElementById('sidebarIcon');
            if (sidebarIcon) {
                if (sidebar.classList.contains('sidebar-collapsed')) {
                    sidebarIcon.classList.remove('fa-bars');
                    sidebarIcon.classList.add('fa-expand');
                } else {
                    sidebarIcon.classList.remove('fa-expand');
                    sidebarIcon.classList.add('fa-bars');
                }
            }
        });
    } else {
        console.warn('未找到侧边栏相关元素');
    }
    
    // 移动端点击遮罩层关闭侧边栏
    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', function() {
            if (sidebar) {
                sidebar.classList.add('sidebar-collapsed');
                if (mainContent) {
                    mainContent.classList.add('main-content-expanded');
                }
            }
            
            const sidebarIcon = document.getElementById('sidebarIcon');
            if (sidebarIcon) {
                sidebarIcon.classList.remove('fa-expand');
                sidebarIcon.classList.add('fa-bars');
            }
        });
    }
    
    // 处理帖子点赞按钮的AJAX提交
    const likeButtons = document.querySelectorAll('.post-action-btn[type="submit"]');
    
    likeButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            // 如果是移动设备，使用AJAX提交以获得更好的用户体验
            if (window.innerWidth <= 768) {
                e.preventDefault();
                
                const form = this.closest('form');
                const url = form.action;
                const csrfToken = form.querySelector('input[name="csrfmiddlewaretoken"]').value;
                
                fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken,
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: JSON.stringify({})
                })
                .then(response => response.json())
                .then(data => {
                    console.log('点赞响应:', data);
                    
                    // 更新按钮状态
                    if (data.liked) {
                        this.classList.add('active');
                        this.querySelector('i').classList.remove('far');
                        this.querySelector('i').classList.add('fas');
                    } else {
                        this.classList.remove('active');
                        this.querySelector('i').classList.remove('fas');
                        this.querySelector('i').classList.add('far');
                    }
                    
                    // 更新点赞数
                    this.querySelector('span').textContent = data.like_count;
                })
                .catch(error => {
                    console.error('点赞请求错误:', error);
                    // 出错时刷新页面
                    window.location.reload();
                });
            }
        });
    });
    
    // 移动端优化：在较小屏幕上减少评论框的初始高度
    const adjustCommentInputHeight = function() {
        const commentInput = document.querySelector('.comment-input');
        if (commentInput) {
            if (window.innerWidth <= 480) {
                commentInput.style.minHeight = '80px';
            } else {
                commentInput.style.minHeight = '100px';
            }
        }
    };
    
    // 页面加载和窗口大小改变时调整
    adjustCommentInputHeight();
    window.addEventListener('resize', adjustCommentInputHeight);
    
    // 帖子内容图片处理：添加点击放大功能
    const postContent = document.querySelector('.post-detail-content');
    if (postContent) {
        const images = postContent.querySelectorAll('img');
        
        images.forEach(img => {
            img.style.cursor = 'pointer';
            img.addEventListener('click', function() {
                const modal = document.createElement('div');
                modal.style.position = 'fixed';
                modal.style.top = '0';
                modal.style.left = '0';
                modal.style.width = '100%';
                modal.style.height = '100%';
                modal.style.backgroundColor = 'rgba(0,0,0,0.8)';
                modal.style.display = 'flex';
                modal.style.alignItems = 'center';
                modal.style.justifyContent = 'center';
                modal.style.zIndex = '1000';
                modal.style.padding = '20px';
                modal.style.cursor = 'pointer';
                
                const modalImg = document.createElement('img');
                modalImg.src = img.src;
                modalImg.style.maxWidth = '90%';
                modalImg.style.maxHeight = '90%';
                modalImg.style.objectFit = 'contain';
                
                modal.appendChild(modalImg);
                document.body.appendChild(modal);
                
                modal.addEventListener('click', function() {
                    document.body.removeChild(modal);
                });
            });
        });
    }
    
    // 瀑布流图片加载处理
    function handlePostImages() {
        const postImages = document.querySelectorAll('.post-image');
        
        postImages.forEach(img => {
            // 如果图片加载失败，替换为默认图片
            img.addEventListener('error', function() {
                this.src = '/static/images/default-post.svg';
            });
            
            // 点击图片直接跳转到详情页
            img.addEventListener('click', function() {
                const postLink = this.closest('.post-card').querySelector('.post-title a');
                if (postLink) {
                    window.location.href = postLink.href;
                }
            });
        });
    }
    
    handlePostImages();
    
    // 在移动端上检测滚动以优化UI交互
    let lastScrollTop = 0;
    let isScrollingDown = false;
    
    window.addEventListener('scroll', function() {
        const st = window.pageYOffset || document.documentElement.scrollTop;
        
        // 确定滚动方向
        isScrollingDown = st > lastScrollTop;
        lastScrollTop = st <= 0 ? 0 : st; // iOS弹性滚动的修复
    });
    
    // 点击"评论"按钮滚动到评论区
    const scrollToCommentsBtn = document.querySelector('.scroll-to-comments');
    if (scrollToCommentsBtn) {
        scrollToCommentsBtn.addEventListener('click', function() {
            const commentsSection = document.getElementById('comments');
            if (commentsSection) {
                commentsSection.scrollIntoView({ behavior: 'smooth' });
            }
        });
    }
    
    // 加载时检查URL中是否有锚点，如果有则滚动到相应位置
    if (window.location.hash) {
        const targetElement = document.querySelector(window.location.hash);
        if (targetElement) {
            setTimeout(function() {
                targetElement.scrollIntoView({ behavior: 'smooth' });
            }, 300);
        }
    }
}); 