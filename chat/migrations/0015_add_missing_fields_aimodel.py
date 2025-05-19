# -*- coding: utf-8 -*-
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0014_merge_20250512_1130'),
    ]

    operations = [
        # 自动生成的迁移 - 添加缺失字段
        # 注意：此处只添加了字段，但未指定具体类型
        # 请根据实际情况修改字段类型和参数
        migrations.AddField(
            model_name='aimodel',
            name='sort_order',
            field=models.CharField(default='', max_length=255),  # 请根据实际情况修改字段类型
            preserve_default=False,
        ),
    ]
