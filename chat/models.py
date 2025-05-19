from django.db import models
from django.contrib.auth.models import User
from django.db.models import Q
import re
import logging

# 获取chat应用的日志记录器
logger = logging.getLogger('chat')

class Conversation(models.Model):
    """对话模型，用于存储用户的对话历史"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations', verbose_name="用户")
    title = models.CharField(max_length=255, default="新对话", verbose_name="标题")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    model = models.CharField(max_length=50, default="gpt-4o", verbose_name="模型")
    is_active = models.BooleanField(default=True, verbose_name="是否活跃")
    is_starred = models.BooleanField(default=False, verbose_name="是否收藏")
    last_activity = models.DateTimeField(auto_now=True, verbose_name="最后活动时间")

    class Meta:
        ordering = ['-updated_at']
        verbose_name = "对话"
        verbose_name_plural = "对话列表"

    def __str__(self):
        return f"{self.title} - {self.user.username}"

class Message(models.Model):
    """消息模型，用于存储对话中的每条消息"""
    ROLE_CHOICES = [
        ('user', '用户'),
        ('assistant', '助手'),
        ('system', '系统'),
    ]
    
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages', verbose_name="所属对话")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, verbose_name="角色")
    content = models.TextField(verbose_name="内容")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    
    # 添加图片URL字段
    image_url = models.TextField(blank=True, null=True, verbose_name="图片URL")
    has_image = models.BooleanField(default=False, verbose_name="是否包含图片")
    
    # 添加token计数字段
    input_tokens = models.IntegerField(default=0, verbose_name="输入Token数")
    output_tokens = models.IntegerField(default=0, verbose_name="输出Token数")
    
    class Meta:
        ordering = ['created_at']
        verbose_name = "消息"
        verbose_name_plural = "消息列表"

    def __str__(self):
        role_display = dict(self.ROLE_CHOICES).get(self.role, self.role)
        return f"{role_display}: {self.content[:50]}{'...' if len(self.content) > 50 else ''}"
        
    def save(self, *args, **kwargs):
        # 检查内容中是否包含图片链接
        if self.content and '![' in self.content and '](' in self.content:
            try:
                # 图片链接格式：![alt text](url)
                image_urls = []
                parts = self.content.split('![')
                
                for i in range(1, len(parts)):
                    img_part = parts[i]
                    if '](' in img_part and ')' in img_part:
                        img_url = img_part.split('](')[1].split(')')[0].strip()
                        image_urls.append(img_url)
                
                if image_urls:
                    self.has_image = True
                    self.image_url = ','.join(image_urls)
            except Exception as e:
                logger.error(f"保存消息时提取图片URL出错: {e}")
        
        super().save(*args, **kwargs)

class ChatSetting(models.Model):
    """聊天设置模型，用于存储用户的聊天设置"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_settings', verbose_name="用户", unique=True)
    model = models.CharField(max_length=50, default="gpt-4o", verbose_name="模型")
    temperature = models.FloatField(default=0.7, verbose_name="温度")
    max_tokens = models.IntegerField(default=1500, verbose_name="最大令牌数")
    top_p = models.FloatField(default=1.0, verbose_name="Top P值")
    presence_penalty = models.FloatField(default=0.0, verbose_name="存在惩罚")
    frequency_penalty = models.FloatField(default=0.0, verbose_name="频率惩罚")
    system_prompt = models.TextField(blank=True, null=True, verbose_name="系统提示词")
    ai_prompt = models.TextField(blank=True, null=True, default="你是一位专业、有帮助的人工智能助手，始终提供准确、有用的信息。", verbose_name="AI提示词")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    class Meta:
        verbose_name = "聊天设置"
        verbose_name_plural = "聊天设置列表"
        constraints = [
            models.UniqueConstraint(fields=['user'], name='unique_user_setting')
        ]

    def __str__(self):
        return f"{self.user.username}的聊天设置"

class ServiceProvider(models.Model):
    """服务提供商模型，存储不同API服务的配置"""
    name = models.CharField(max_length=50, unique=True, verbose_name="服务商名称")
    api_base = models.CharField(max_length=255, verbose_name="API基础URL")
    api_key = models.CharField(max_length=255, verbose_name="API密钥")
    is_active = models.BooleanField(default=True, verbose_name="是否激活")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    def __str__(self):
        return self.name

class GlobalSetting(models.Model):
    """全局设置模型，用于存储应用的全局配置，包括全局系统提示词"""
    system_prompt = models.TextField(blank=True, null=True, verbose_name="全局系统提示词", 
                                    help_text="设置所有用户共用的系统提示词，这将覆盖用户级别的系统提示词设置")
    default_ai_prompt = models.TextField(blank=True, null=True, verbose_name="默认AI提示词",
                                        help_text="设置新用户的默认AI提示词")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    class Meta:
        verbose_name = "全局设置"
        verbose_name_plural = "全局设置"
    
    def __str__(self):
        return "系统全局设置"
    
    def save(self, *args, **kwargs):
        # 确保只有一个实例
        if not self.pk and GlobalSetting.objects.exists():
            # 如果已存在记录且当前是新记录，则更新现有记录
            existing = GlobalSetting.objects.first()
            existing.system_prompt = self.system_prompt
            existing.default_ai_prompt = self.default_ai_prompt
            existing.save()
            return existing
        return super().save(*args, **kwargs)
    
    @classmethod
    def get_instance(cls):
        """获取全局设置的单例实例，如果不存在则创建一个默认实例"""
        instance, created = cls.objects.get_or_create(
            defaults={
                'system_prompt': '你是一个有用的助手，始终提供准确、有帮助的回答。',
                'default_ai_prompt': '你是一位专业、有帮助的人工智能助手，始终提供准确、有用的信息。'
            }
        )
        return instance

class AIModel(models.Model):
    """AI模型信息，存储不同模型的配置和功能"""
    model_id = models.CharField(max_length=50, unique=True, verbose_name="模型ID")
    display_name = models.CharField(max_length=100, verbose_name="显示名称")
    description = models.TextField(blank=True, null=True, verbose_name="模型描述")
    provider = models.ForeignKey(ServiceProvider, on_delete=models.CASCADE, related_name='models', verbose_name="服务提供商")
    api_endpoint = models.CharField(max_length=255, blank=True, null=True, verbose_name="API请求端点", 
                                   help_text="您可以设置完整的API端点URL，这将覆盖服务商默认的端点配置。格式如：https://api.example.com/v1/chat/completions。留空则使用服务商配置的接口地址。")
    supports_stream = models.BooleanField(default=True, verbose_name="支持流式响应")
    supports_image_analysis = models.BooleanField(default=False, verbose_name="支持图像分析")
    supports_file_analysis = models.BooleanField(default=False, verbose_name="支持文件分析")
    supports_image_generation = models.BooleanField(default=False, verbose_name="支持图像生成")
    supports_web_search = models.BooleanField(default=False, verbose_name="支持网络搜索")
    supports_audio = models.BooleanField(default=False, verbose_name="支持音频处理")
    supports_reasoning = models.BooleanField(default=False, verbose_name="支持推理过程")
    max_context_length = models.IntegerField(default=8000, verbose_name="最大上下文长度")
    is_active = models.BooleanField(default=True, verbose_name="是否激活")
    sort_order = models.IntegerField(default=0, verbose_name="排序顺序")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    class Meta:
        ordering = ['sort_order', 'model_id']
        verbose_name = "AI模型"
        verbose_name_plural = "AI模型列表"
    
    def __str__(self):
        return f"{self.display_name} ({self.model_id})"
        
    def get_features(self):
        """返回模型支持的功能列表"""
        features = []
        if self.supports_stream:
            features.append('stream')
        if self.supports_image_analysis:
            features.append('image_analysis')
        if self.supports_file_analysis:
            features.append('file_analysis')
        if self.supports_image_generation:
            features.append('image_generation')
        if self.supports_web_search:
            features.append('web_search')
        if self.supports_audio:
            features.append('audio')
        if self.supports_reasoning:
            features.append('reasoning')
        return features
