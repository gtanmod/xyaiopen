from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0010_add_api_provider'),
    ]

    operations = [
        migrations.AddField(
            model_name='aimodel',
            name='api_provider',
            field=models.CharField(default='openai', max_length=50, verbose_name='API提供商'),
        ),
    ] 