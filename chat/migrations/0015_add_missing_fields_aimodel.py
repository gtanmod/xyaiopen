# -*- coding: utf-8 -*-
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0014_merge_20250512_1130'),
    ]

    operations = [
        # �Զ����ɵ�Ǩ�� - ���ȱʧ�ֶ�
        # ע�⣺�˴�ֻ������ֶΣ���δָ����������
        # �����ʵ������޸��ֶ����ͺͲ���
        migrations.AddField(
            model_name='aimodel',
            name='sort_order',
            field=models.CharField(default='', max_length=255),  # �����ʵ������޸��ֶ�����
            preserve_default=False,
        ),
    ]
