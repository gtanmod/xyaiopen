from django.db import migrations
from django.conf import settings

def create_default_service_provider(apps, schema_editor):
    AIServiceProvider = apps.get_model('chat', 'AIServiceProvider')
    
    # 检查是否已经存在默认服务商
    if not AIServiceProvider.objects.filter(is_default=True).exists():
        # 创建默认服务商
        AIServiceProvider.objects.create(
            name="默认OpenAI兼容服务",
            api_url=getattr(settings, 'API_BASE_URL', 'https://api.gpt.ge'),
            api_key=getattr(settings, 'API_TOKEN', ''),
            auth_method='bearer',
            is_default=True,
            is_active=True
        )

class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0005_aiserviceprovider'),
    ]

    operations = [
        migrations.RunPython(create_default_service_provider),
    ] 