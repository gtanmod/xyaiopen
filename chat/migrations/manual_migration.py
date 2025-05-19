from django.db import migrations, models
import django.db.models.deletion

def initialize_service_provider(apps, schema_editor):
    ServiceProvider = apps.get_model('chat', 'ServiceProvider')
    service_provider = ServiceProvider.objects.create(
        name='OpenAI',
        api_base='https://api.openai.com/v1',
        api_key='sk-your-api-key',
        is_active=True
    )
    return service_provider.id

def initialize_aimodel_provider(apps, schema_editor):
    ServiceProvider = apps.get_model('chat', 'ServiceProvider')
    AIModel = apps.get_model('chat', 'AIModel')
    
    # 创建默认服务提供商
    provider_id = None
    if not ServiceProvider.objects.exists():
        provider = ServiceProvider.objects.create(
            name='OpenAI',
            api_base='https://api.openai.com/v1',
            api_key='sk-your-api-key',
            is_active=True
        )
        provider_id = provider.id
    else:
        provider = ServiceProvider.objects.first()
        provider_id = provider.id
    
    # 更新所有AIModel记录
    AIModel.objects.update(provider_id=provider_id)

class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0007_aimodel_alter_chatsetting_created_at_and_more'),
    ]

    operations = [
        # 创建ServiceProvider表
        migrations.CreateModel(
            name='ServiceProvider',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True, verbose_name='服务商名称')),
                ('api_base', models.CharField(max_length=255, verbose_name='API基础URL')),
                ('api_key', models.CharField(max_length=255, verbose_name='API密钥')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否激活')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
            ],
        ),
        # 运行初始化服务提供商的函数
        migrations.RunPython(initialize_service_provider),
        # 添加provider字段到AIModel
        migrations.AddField(
            model_name='aimodel',
            name='provider',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='models', to='chat.serviceprovider', verbose_name='服务提供商'),
            preserve_default=False,
        ),
        # 运行更新AIModel的provider字段的函数
        migrations.RunPython(initialize_aimodel_provider),
    ] 