from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0014_merge_20250512_1130'),
    ]

    operations = [
        migrations.AddField(
            model_name='aimodel',
            name='supports_reasoning',
            field=models.BooleanField(default=False, verbose_name='支持推理过程'),
        ),
    ] 