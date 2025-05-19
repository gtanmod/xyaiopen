from django.db import migrations

def fill_service_provider(apps, schema_editor):
    """
    为AIModel记录关联默认的AIServiceProvider
    """
    AIModel = apps.get_model('chat', 'AIModel')
    AIServiceProvider = apps.get_model('chat', 'AIServiceProvider')
    
    # 获取默认服务提供商
    default_provider = AIServiceProvider.objects.filter(is_default=True).first()
    if not default_provider and AIServiceProvider.objects.exists():
        default_provider = AIServiceProvider.objects.first()
    
    # 如果没有服务商，创建一个默认的
    if not default_provider:
        default_provider = AIServiceProvider.objects.create(
            name="默认OpenAI兼容服务",
            api_url="https://api.gpt.ge",
            api_key="",
            auth_method="bearer",
            is_default=True,
            is_active=True
        )
    
    # 为所有模型设置默认服务商
    AIModel.objects.filter(service_provider__isnull=True).update(service_provider=default_provider)

class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0008_aimodel_service_provider'),
    ]

    operations = [
        migrations.RunPython(fill_service_provider),
    ] 