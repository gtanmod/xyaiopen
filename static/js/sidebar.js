/**
 * 通用侧边栏交互功能
 * 
 * 主要功能：
 * 1. 响应式折叠/展开侧边栏
 * 2. 移动设备自适应
 * 3. 记住用户偏好设置
 */

document.addEventListener('DOMContentLoaded', function() {
    // 获取相关DOM元素
    const sidebar = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    const toggleSidebarBtn = document.getElementById('toggleSidebarBtn'); 
    const mainContent = document.getElementById('mainContent');
    const sidebarIcon = document.getElementById('sidebarIcon');
    
    // 如果侧边栏元素不存在，则不执行后续代码
    if (!sidebar) return;

    // 从localStorage读取侧边栏状态
    function loadSidebarState() {
        const state = localStorage.getItem('sidebar-state');
        if (state === 'collapsed') {
            sidebar.classList.add('sidebar-collapsed');
            if (mainContent) {
                mainContent.classList.add('main-content-expanded');
            }
            if (sidebarIcon) {
                sidebarIcon.classList.remove('fa-bars');
                sidebarIcon.classList.add('fa-expand');
            }
        }
    }

    // 保存侧边栏状态到localStorage
    function saveSidebarState() {
        if (sidebar.classList.contains('sidebar-collapsed')) {
            localStorage.setItem('sidebar-state', 'collapsed');
        } else {
            localStorage.setItem('sidebar-state', 'expanded');
        }
    }

    // 移动设备上自动折叠侧边栏
    function handleResponsive() {
        if (window.innerWidth < 768) {
            sidebar.classList.add('sidebar-collapsed', 'sidebar-mobile');
            if (mainContent) {
                mainContent.classList.add('main-content-expanded');
            }
        } else {
            sidebar.classList.remove('sidebar-mobile');
            // 加载用户之前的偏好设置
            loadSidebarState();
        }
    }

    // 处理窗口大小变化
    window.addEventListener('resize', handleResponsive);
    
    // 初始化时应用响应式设置
    handleResponsive();

    // 点击遮罩层关闭侧边栏（移动设备）
    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', function() {
            sidebar.classList.add('sidebar-collapsed');
            if (mainContent) {
                mainContent.classList.add('main-content-expanded');
            }
            if (sidebarIcon) {
                sidebarIcon.classList.remove('fa-bars');
                sidebarIcon.classList.add('fa-expand');
            }
            
            saveSidebarState();
        });
    }
    
    // 侧边栏切换功能
    if (toggleSidebarBtn) {
        toggleSidebarBtn.addEventListener('click', function() {
            if (sidebar) {
                sidebar.classList.toggle('sidebar-collapsed');
            }
            if (mainContent) {
                mainContent.classList.toggle('main-content-expanded');
            }
            
            // 更新图标
            if (sidebarIcon) {
                if (sidebar && sidebar.classList.contains('sidebar-collapsed')) {
                    sidebarIcon.classList.remove('fa-bars');
                    sidebarIcon.classList.add('fa-expand');
                } else {
                    sidebarIcon.classList.remove('fa-expand');
                    sidebarIcon.classList.add('fa-bars');
                }
            }
            
            // 保存状态
            saveSidebarState();
        });
    }
    
    // 初始化时检查当前侧边栏状态
    loadSidebarState();
    
    // 处理移动设备上的特殊交互
    if (window.innerWidth < 768) {
        // 移动设备上点击链接后自动关闭侧边栏
        const sidebarLinks = sidebar.querySelectorAll('a.app-item');
        sidebarLinks.forEach(link => {
            link.addEventListener('click', function() {
                sidebar.classList.add('sidebar-collapsed');
                if (mainContent) {
                    mainContent.classList.add('main-content-expanded');
                }
                if (sidebarIcon) {
                    sidebarIcon.classList.remove('fa-bars');
                    sidebarIcon.classList.add('fa-expand');
                }
            });
        });
    }
});