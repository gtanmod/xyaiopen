# Generated by Django 4.2 on 2025-04-30 12:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AIServiceProvider',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='服务商名称')),
                ('api_url', models.URLField(help_text='例如: https://api.openai.com', verbose_name='API基础URL')),
                ('api_key', models.CharField(max_length=255, verbose_name='API密钥')),
                ('auth_method', models.CharField(choices=[('bearer', 'Bearer Token认证'), ('header', '请求头认证'), ('query', '查询参数认证')], default='bearer', help_text='指定API密钥如何提交到服务商', max_length=20, verbose_name='认证方式')),
                ('auth_key_name', models.CharField(blank=True, help_text="当使用header或query认证时，指定键名，例如'X-API-Key'", max_length=50, null=True, verbose_name='认证键名')),
                ('is_default', models.BooleanField(default=False, verbose_name='是否默认')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否可用')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
            ],
            options={
                'verbose_name': 'AI服务商',
                'verbose_name_plural': 'AI服务商',
                'ordering': ['-is_default', 'name'],
            },
        ),
    ]
