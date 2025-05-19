from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.index, name='index'),
    path('chat/', views.chat, name='chat'),
    path('chat/<int:id>/', views.chat, name='chat_with_id'),
    path('latest_conversation/', views.latest_conversation, name='latest_conversation'),
    path('new_conversation/', views.new_conversation, name='new_conversation'),
    path('delete_conversation/<int:conversation_id>/', views.delete_conversation, name='delete_conversation'),
    path('rename_conversation/<int:conversation_id>/', views.rename_conversation, name='rename_conversation'),
    path('toggle_star/<int:conversation_id>/', views.toggle_star, name='toggle_star'),
    path('send_message/', views.send_message, name='send_message'),
    path('stream_message/', views.stream_message, name='stream_message'),
    path('update_settings/', views.update_settings, name='update_settings'),
    path('cleanup_settings/', views.cleanup_settings, name='cleanup_settings'),
    
    # PWA 相关路由
    path('manifest.json', views.manifest, name='manifest'),
    path('service-worker.js', views.service_worker, name='service_worker'),
] 