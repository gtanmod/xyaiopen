from django.db import migrations

def update_service_provider_relation(apps, schema_editor):
    """
    根据AIModel的api_provider值，更新service_provider关联
    """
    AIModel = apps.get_model('chat', 'AIModel')
    AIServiceProvider = apps.get_model('chat', 'AIServiceProvider')
    
    # 获取默认服务提供商
    default_provider = AIServiceProvider.objects.filter(is_default=True).first()
    
    # 创建映射来缓存查找结果
    provider_map = {}
    
    for model in AIModel.objects.all():
        provider_name = model.api_provider
        
        # 如果没有对应的服务商，则使用名称创建
        if provider_name not in provider_map:
            provider = AIServiceProvider.objects.filter(name=provider_name).first()
            
            if not provider:
                # 如果服务商不存在，创建一个新的
                provider = AIServiceProvider.objects.create(
                    name=provider_name,
                    api_url="https://api.gpt.ge",  # 默认URL
                    api_key="",  # 留空
                    auth_method="bearer",
                    is_default=False,
                    is_active=True
                )
            
            provider_map[provider_name] = provider
        
        # 更新模型的服务商关联
        if provider_name in provider_map:
            model.service_provider = provider_map[provider_name]
            model.save(update_fields=['service_provider'])

class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0011_add_missing_api_provider'),
    ]

    operations = [
        migrations.RunPython(update_service_provider_relation),
    ] 