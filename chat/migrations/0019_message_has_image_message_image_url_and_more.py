# Generated by Django 4.2 on 2025-05-15 21:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0018_aimodel_api_endpoint'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='has_image',
            field=models.BooleanField(default=False, verbose_name='是否包含图片'),
        ),
        migrations.AddField(
            model_name='message',
            name='image_url',
            field=models.TextField(blank=True, null=True, verbose_name='图片URL'),
        ),
        migrations.AlterField(
            model_name='aimodel',
            name='api_endpoint',
            field=models.CharField(blank=True, help_text='您可以设置完整的API端点URL，这将覆盖服务商默认的端点配置。格式如：https://api.example.com/v1/chat/completions。留空则使用服务商配置的接口地址。', max_length=255, null=True, verbose_name='API请求端点'),
        ),
    ]
