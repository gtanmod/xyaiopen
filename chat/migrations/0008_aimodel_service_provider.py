from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0007_aimodel_alter_chatsetting_created_at_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='aimodel',
            name='service_provider',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ai_models', to='chat.aiserviceprovider', verbose_name='服务商'),
        ),
    ] 