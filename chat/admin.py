from django.contrib import admin
from .models import Conversation, Message, ChatSetting, AIModel, ServiceProvider, GlobalSetting
import os

class MessageInline(admin.TabularInline):
    model = Message
    extra = 0

@admin.register(GlobalSetting)
class GlobalSettingAdmin(admin.ModelAdmin):
    list_display = ('id', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('系统提示词设置', {
            'fields': ('system_prompt',),
            'description': '<strong>全局系统提示词对所有用户生效，这是所有AI交互的基础设置。</strong><br>'
                         '这里设置的系统提示词会应用于所有用户的对话，并且覆盖用户级别的系统提示词设置。<br>'
                         '例如："你是小羊AI客服助手，始终保持专业、友好的态度，提供准确的信息。"',
            'classes': ('wide',)
        }),
        ('默认AI提示词设置', {
            'fields': ('default_ai_prompt',),
            'description': '这里设置的AI提示词将作为新用户的默认提示词。<br>'
                          '用户可以通过前端界面修改自己的AI提示词设置。',
            'classes': ('wide',)
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def has_add_permission(self, request):
        # 如果已经存在记录，则禁止添加新记录
        return not GlobalSetting.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # 禁止删除唯一的全局设置
        return False

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'title', 'model', 'updated_at')
    list_filter = ('user', 'model')
    search_fields = ('title', 'user__username')
    inlines = [MessageInline]

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'role', 'short_content', 'created_at')
    list_filter = ('role', 'conversation')
    search_fields = ('content', 'conversation__title')
    
    def short_content(self, obj):
        return obj.content[:50] + ('...' if len(obj.content) > 50 else '')
    short_content.short_description = '内容预览'

@admin.register(ChatSetting)
class ChatSettingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'has_system_prompt', 'system_prompt_preview', 'model', 'temperature', 'max_tokens', 'has_ai_prompt', 'updated_at')
    list_filter = ('user', 'model')
    search_fields = ('user__username', 'system_prompt', 'ai_prompt')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('用户信息', {
            'fields': ('user',)
        }),
        ('系统提示词设置', {
            'fields': ('system_prompt',),
            'description': '<strong>系统提示词是一个关键配置，它会影响AI的整体行为和回答方式。</strong><br>'
                          '系统提示词仅在管理后台设置，用户在前端无法直接修改，确保了AI行为的一致性和安全性。<br>'
                          '例如，您可以设置为："你是一名专业客服助手，始终保持专业、有礼貌的态度回答问题。"',
            'classes': ('wide',)
        }),
        ('AI提示词设置', {
            'fields': ('ai_prompt',),
            'description': '用户可以通过前端界面的AI提示词设置来自定义AI的回复风格。<br>'
                          '这里设置的AI提示词将作为用户的默认值，当用户未设置自己的AI提示词时使用。',
            'classes': ('wide',)
        }),
        ('模型配置', {
            'fields': ('model', 'temperature', 'max_tokens', 'top_p', 'presence_penalty', 'frequency_penalty')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def has_system_prompt(self, obj):
        return bool(obj.system_prompt)
    has_system_prompt.boolean = True
    has_system_prompt.short_description = "系统提示词"
    
    def system_prompt_preview(self, obj):
        if obj.system_prompt:
            return obj.system_prompt[:50] + ('...' if len(obj.system_prompt) > 50 else '')
        return "-"
    system_prompt_preview.short_description = "系统提示词预览"
    
    def has_ai_prompt(self, obj):
        return bool(obj.ai_prompt)
    has_ai_prompt.boolean = True
    has_ai_prompt.short_description = "AI提示词"

@admin.register(AIModel)
class AIModelAdmin(admin.ModelAdmin):
    list_display = ('model_id', 'display_name', 'provider', 'is_active', 'sort_order', 'has_custom_endpoint')
    list_filter = ('is_active', 'provider', 'supports_stream', 'supports_image_generation')
    search_fields = ('model_id', 'display_name')
    ordering = ('sort_order', 'model_id')
    readonly_fields = ('effective_api_url',)
    fieldsets = (
        ('基本信息', {
            'fields': ('model_id', 'display_name', 'description', 'is_active', 'sort_order')
        }),
        ('API配置', {
            'fields': ('provider', 'api_endpoint', 'effective_api_url')
        }),
        ('功能支持', {
            'fields': ('supports_stream', 'supports_image_analysis', 'supports_file_analysis', 
                      'supports_image_generation', 'supports_web_search', 'supports_audio', 
                      'supports_reasoning', 'max_context_length')
        })
    )
    
    def has_custom_endpoint(self, obj):
        """显示是否使用自定义端点"""
        return bool(obj.api_endpoint)
    has_custom_endpoint.boolean = True
    has_custom_endpoint.short_description = "自定义端点"
    
    def effective_api_url(self, obj):
        """显示实际会使用的API URL"""
        from chat.services import ChatAPIService
        
        if not obj:
            return "模型未保存，无法显示"
            
        try:
            # 如果模型有自定义端点
            if obj.api_endpoint:
                return f"""
                <strong>使用自定义端点:</strong> {obj.api_endpoint}<br>
                <p class="help" style="color: #3c763d;">自定义端点优先于服务商设置。当前模型将直接使用此URL发送请求。</p>
                """
            
            # 否则使用服务商配置
            if obj.provider:
                # 获取不同类型的端点URL
                provider = obj.provider
                model_type = ChatAPIService.get_model_type(obj.model_id)
                
                base = provider.api_base.rstrip('/')
                if not base.endswith('/v1'):
                    base = f"{base}/v1"
                
                if model_type == 'image':
                    endpoint = f"{base}/images/generations"
                    endpoint_desc = "图像生成"
                elif model_type == 'embedding':
                    endpoint = f"{base}/embeddings"
                    endpoint_desc = "嵌入向量"
                elif model_type == 'audio':
                    endpoint = f"{base}/audio/transcriptions"
                    endpoint_desc = "音频处理"
                else:
                    endpoint = f"{base}/chat/completions"
                    endpoint_desc = "聊天完成"
                    
                return f"""
                <strong>使用服务商"{provider.name}"的API配置:</strong><br>
                <strong>{endpoint_desc}端点:</strong> {endpoint}<br>
                <p class="help">您可以通过设置自定义端点来覆盖此配置。</p>
                """
            return "未配置服务商"
        except Exception as e:
            return f"无法生成URL: {str(e)}"
    effective_api_url.short_description = "实际API URL"
    effective_api_url.allow_tags = True

@admin.register(ServiceProvider)
class ServiceProviderAdmin(admin.ModelAdmin):
    list_display = ('name', 'api_base', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'api_base')
    readonly_fields = ('api_url_example', 'created_at', 'updated_at')
    actions = ['update_api_settings']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'is_active')
        }),
        ('API配置', {
            'fields': ('api_base', 'api_key', 'api_url_example')
        })
    )
    
    def api_url_example(self, obj):
        """显示该服务商的API URL示例"""
        if not obj or not obj.api_base:
            return "未配置API基础URL"
            
        # 构建示例URL
        base = obj.api_base.rstrip('/')
        if not base.endswith('/v1'):
            chat_url = f"{base}/v1/chat/completions"
            image_url = f"{base}/v1/images/generations"
        else:
            chat_url = f"{base}/chat/completions"
            image_url = f"{base}/images/generations"
            
        return f"""
        <strong>聊天API URL示例:</strong> {chat_url}<br>
        <strong>图像API URL示例:</strong> {image_url}<br>
        <p class="help">这是系统使用此服务商时的默认端点URL。您也可以在每个模型中配置自定义端点。</p>
        """
    api_url_example.short_description = "API URL示例"
    api_url_example.allow_tags = True
    
    def update_api_settings(self, request, queryset):
        for provider in queryset:
            provider.api_base = 'https://api.gpt.ge'
            provider.api_key = os.environ.get('API_TOKEN', '')
            provider.save()
        self.message_user(request, f"已成功更新 {queryset.count()} 个服务提供商的API设置")
    update_api_settings.short_description = "更新API设置为最新配置"
