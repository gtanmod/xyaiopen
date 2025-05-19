// PWA 安装程序代码
let deferredPrompt;
const installPromotion = document.createElement('div');

// 样式设置
installPromotion.className = 'pwa-install-prompt';
installPromotion.innerHTML = `
  <div class="pwa-prompt-container">
    <div class="pwa-prompt-content">
      <img src="/static/images/logo.png" alt="小羊系统" class="pwa-logo">
      <div class="pwa-prompt-text">
        <h4>添加小羊系统到主屏幕</h4>
        <p>获得更好的体验，离线使用</p>
      </div>
      <button id="pwa-install-btn" class="btn btn-primary">安装应用</button>
      <button id="pwa-close-btn" class="btn btn-outline-secondary">稍后再说</button>
    </div>
  </div>
`;

// 移动设备检测
function isMobileDevice() {
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
}

// 设置移动设备上侧边栏默认收起
function collapseSidebarOnMobile() {
  if (isMobileDevice() || window.innerWidth <= 768) {
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.querySelector('.main-content');
    const sidebarIcon = document.getElementById('sidebarIcon');
    
    if (sidebar && !sidebar.classList.contains('sidebar-collapsed')) {
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
}

// 监听 beforeinstallprompt 事件
window.addEventListener('beforeinstallprompt', (e) => {
  // 如果不是移动设备，则不显示安装提示
  if (!isMobileDevice()) {
    return;
  }
  
  // 阻止 Chrome 67+ 自动显示安装提示
  e.preventDefault();
  // 保存事件以便稍后触发
  deferredPrompt = e;
  
  // 检查是否已经通过 PWA 打开
  if (window.matchMedia('(display-mode: standalone)').matches || 
      window.navigator.standalone === true) {
    return; // 已经作为 PWA 安装，不需要提示
  }
  
  // 显示自定义安装提示
  document.body.appendChild(installPromotion);
  
  // 绑定安装按钮事件
  document.getElementById('pwa-install-btn').addEventListener('click', () => {
    // 隐藏安装提示
    installPromotion.style.display = 'none';
    // 显示安装提示
    deferredPrompt.prompt();
    // 等待用户响应
    deferredPrompt.userChoice.then((choiceResult) => {
      if (choiceResult.outcome === 'accepted') {
        console.log('用户接受 PWA 安装');
      } else {
        console.log('用户拒绝 PWA 安装');
      }
      // 清除保存的提示
      deferredPrompt = null;
    });
  });
  
  // 绑定关闭按钮事件
  document.getElementById('pwa-close-btn').addEventListener('click', () => {
    installPromotion.style.display = 'none';
  });
});

// 检测是否为从主屏幕启动的 PWA
document.addEventListener('DOMContentLoaded', () => {
  // 如果是以 standalone 模式运行，添加一个类到 body 上以应用特殊样式
  if (window.matchMedia('(display-mode: standalone)').matches || 
      window.navigator.standalone === true) {
    document.body.classList.add('pwa-standalone-mode');
  }
  
  // 在移动设备上默认收起侧边栏
  collapseSidebarOnMobile();
  
  // 同时处理窗口大小变化
  window.addEventListener('resize', collapseSidebarOnMobile);
});

// 监听显示模式变化
window.matchMedia('(display-mode: standalone)').addEventListener('change', (e) => {
  if (e.matches) {
    document.body.classList.add('pwa-standalone-mode');
    // 当切换到 standalone 模式时，再次检查并设置侧边栏状态
    collapseSidebarOnMobile();
  } else {
    document.body.classList.remove('pwa-standalone-mode');
  }
}); 