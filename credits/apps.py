from django.apps import AppConfig


class CreditsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'credits'

    def ready(self):
        # 导入信号处理器
        import credits.signals
