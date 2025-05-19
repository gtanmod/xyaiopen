/**
 * 移动端侧边栏优化脚本
 * 用于改善移动设备上侧边栏的显示和交互体验
 */

document.addEventListener('DOMContentLoaded', function() {
    // 获取侧边栏相关元素
    const sidebar = document.querySelector('.sidebar');
    const toggleBtn = document.getElementById('toggleSidebarBtn');
    const mainContent = document.getElementById('mainContent');
    const body = document.body;
    
    // 检查是否已有遮罩层，获取或创建
    let overlay = document.querySelector('.sidebar-overlay');
    
    // 检测设备屏幕宽度，确定是否是移动设备
    function isMobile() {
        return window.innerWidth <= 768;
    }
    
    // 显示侧边栏
    function showSidebar() {
        sidebar.classList.add('sidebar-active');
        if (overlay) {
            overlay.style.display = 'block';
            overlay.style.opacity = '1';
        }
        body.style.overflow = 'hidden'; // 防止背景滚动
    }
    
    // 隐藏侧边栏
    function hideSidebar() {
        sidebar.classList.remove('sidebar-active');
        if (overlay) {
            overlay.style.opacity = '0';
            setTimeout(() => {
                overlay.style.display = 'none';
            }, 300); // 延迟与动画时间一致
        }
        body.style.overflow = '';
    }
    
    // 切换侧边栏显示状态
    function toggleSidebar() {
        if (sidebar.classList.contains('sidebar-active')) {
            hideSidebar();
        } else {
            showSidebar();
        }
    }
    
    // 侧边栏按钮点击事件
    if (toggleBtn) {
        toggleBtn.addEventListener('click', function(e) {
            e.preventDefault();
            toggleSidebar();
        });
    }
    
    // 点击遮罩层关闭侧边栏
    if (overlay) {
        overlay.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            hideSidebar();
        });
    }
    
    // 窗口大小改变时重置侧边栏状态
    window.addEventListener('resize', function() {
        if (!isMobile() && sidebar && sidebar.classList.contains('sidebar-active')) {
            hideSidebar();
        }
    });
    
    // 添加侧边栏相关的CSS样式
    const styleEl = document.createElement('style');
    styleEl.textContent = `
        @media (max-width: 768px) {
            .sidebar {
                position: fixed;
                left: -280px;
                width: 280px;
                transition: left 0.3s ease;
                z-index: 1050;
                background-color: #f5f5f5;
                height: 100vh;
                overflow-y: auto;
                box-shadow: 2px 0 5px rgba(0,0,0,0.1);
            }
            
            .sidebar.sidebar-active {
                left: 0;
            }
            
            .sidebar-overlay {
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0, 0, 0, 0.5);
                z-index: 1040;
                opacity: 0;
                transition: opacity 0.3s ease;
                pointer-events: auto;
            }
            
            .main-content {
                margin-left: 0 !important;
                width: 100% !important;
            }
            
            .toggle-sidebar {
                display: flex !important;
            }
        }
    `;
    document.head.appendChild(styleEl);
    
    // 在移动设备上初始化侧边栏状态
    if (isMobile() && mainContent) {
        mainContent.style.marginLeft = '0';
        mainContent.style.width = '100%';
    }
    
    console.log('移动端侧边栏优化已加载');
}); 