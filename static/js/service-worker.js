// 缓存名称
const CACHE_NAME = 'xiaoyang-system-cache-v2';

// 需要缓存的资源列表
const urlsToCache = [
  '/',
  '/static/css/styles.css',
  '/static/css/community.css',
  '/static/js/community.js',
  '/static/images/assistant-avatar.png',
  '/static/images/chat-welcome.png',
  '/static/images/default-post.svg'
];

// 安装 Service Worker 并缓存资源
self.addEventListener('install', event => {
  console.log('Service Worker 正在安装');
  
  // 跳过等待，直接激活
  self.skipWaiting();
  
  // 不再在安装阶段预缓存资源，避免因资源不可用导致安装失败
  // 将在fetch事件中按需缓存
});

// 激活 Service Worker 并清除旧缓存
self.addEventListener('activate', event => {
  console.log('Service Worker 已激活');
  
  // 立即接管所有页面
  event.waitUntil(clients.claim());
  
  // 清理旧缓存
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            console.log('Service Worker: 删除旧缓存 ' + cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).catch(error => {
      console.error('清理缓存时出错:', error);
    })
  );
});

// 处理网络请求，使用网络优先策略
self.addEventListener('fetch', event => {
  // 对于非GET请求或非本站请求，直接使用默认网络请求处理
  if (event.request.method !== 'GET' || !event.request.url.startsWith(self.location.origin)) {
    return;
  }
  
  event.respondWith(
    // 网络优先策略
    fetch(event.request)
      .then(response => {
        // 如果网络请求成功，尝试更新缓存
        if (response && response.status === 200) {
          try {
            const responseToCache = response.clone();
            caches.open(CACHE_NAME)
              .then(cache => {
                cache.put(event.request, responseToCache);
              })
              .catch(err => {
                console.error('缓存更新失败:', err);
              });
          } catch (error) {
            console.error('克隆响应时出错:', error);
          }
        }
        return response;
      })
      .catch(() => {
        // 网络请求失败，尝试从缓存获取
        return caches.match(event.request)
          .then(cachedResponse => {
            if (cachedResponse) {
              return cachedResponse;
            }
            
            // 如果缓存中没有，并且是需要缓存的URL，尝试离线获取
            const url = new URL(event.request.url);
            if (urlsToCache.includes(url.pathname)) {
              return new Response('Resource not available offline', {
                status: 503,
                statusText: 'Service Unavailable',
                headers: new Headers({
                  'Content-Type': 'text/plain'
                })
              });
            }
            
            // 返回一个简单的离线响应
            return new Response('You are offline', {
              status: 503,
              statusText: 'Service Unavailable',
              headers: new Headers({
                'Content-Type': 'text/plain'
              })
            });
          });
      })
  );
}); 