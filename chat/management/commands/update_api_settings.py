# 导入os模块以使用环境变量
import os
from django.core.management.base import BaseCommand
from chat.models import ServiceProvider

class Command(BaseCommand):
    help = '更新所有活跃的ServiceProvider的API设置'

    def handle(self, *args, **options):
        providers = ServiceProvider.objects.filter(is_active=True)
        count = 0
        
        for provider in providers:
            old_base = provider.api_base
            old_key = provider.api_key
            
            provider.api_base = 'https://api.gpt.ge'
            # 使用环境变量代替硬编码的API密钥
            provider.api_key = os.environ.get('API_TOKEN', '')
            provider.save()
            
            count += 1
            self.stdout.write(self.style.SUCCESS(
                f'成功更新服务提供商 "{provider.name}":\n'
                f'API Base: {old_base} -> {provider.api_base}\n'
                f'API Key: {"*" * len(old_key) if old_key else "无"} -> {"*" * 10}...'
            ))
        
        if count == 0:
            self.stdout.write(self.style.WARNING('没有找到活跃的服务提供商'))
        else:
            self.stdout.write(self.style.SUCCESS(f'成功更新 {count} 个服务提供商的API设置')) 