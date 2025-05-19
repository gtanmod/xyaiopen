from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0009_fill_service_provider'),
    ]

    operations = [
        migrations.AlterField(
            model_name='aimodel',
            name='api_provider',
            field=models.CharField(default='openai', max_length=50, verbose_name='API提供商'),
        ),
    ] 