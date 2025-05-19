from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils import timezone
from .models import UserProfile, CreditRecord, SystemConfig

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    为新创建的用户创建用户资料，并赠送初始积分
    """
    if created:
        # 获取新用户初始积分配置
        try:
            initial_credits = int(SystemConfig.objects.get(key='new_user_initial_credits', is_active=True).value)
        except (SystemConfig.DoesNotExist, ValueError):
            initial_credits = 50  # 默认值
        
        # 创建用户资料
        profile = UserProfile.objects.create(
            user=instance,
            credits=initial_credits
        )
        
        # 记录积分赠送
        if initial_credits > 0:
            CreditRecord.objects.create(
                user=instance,
                credit_change=initial_credits,
                record_type='reward',
                description='新用户注册奖励',
                balance=initial_credits
            ) 