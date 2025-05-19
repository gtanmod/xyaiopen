from django.db import models
from django.contrib.auth.models import User
import uuid

class UserProfile(models.Model):
    """用户资料模型，存储用户相关的额外信息"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name="用户")
    credits = models.IntegerField(default=0, verbose_name="积分")
    last_sign_in = models.DateField(null=True, blank=True, verbose_name="上次签到日期")
    continuous_sign_days = models.IntegerField(default=0, verbose_name="连续签到天数")
    total_sign_days = models.IntegerField(default=0, verbose_name="总签到天数")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    class Meta:
        verbose_name = "用户资料"
        verbose_name_plural = "用户资料列表"
    
    def __str__(self):
        return f"{self.user.username}的资料"

class CreditRecord(models.Model):
    """积分记录模型，用于记录积分的变动"""
    TYPE_CHOICES = [
        ('sign_in', '签到'),
        ('charge', '充值'),
        ('usage', '使用'),
        ('admin', '管理员操作'),
        ('reward', '奖励'),
        ('refund', '退款')
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='credit_records', verbose_name="用户")
    credit_change = models.IntegerField(verbose_name="积分变动")
    record_type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name="记录类型")
    description = models.CharField(max_length=255, verbose_name="描述")
    message = models.ForeignKey('chat.Message', null=True, blank=True, on_delete=models.SET_NULL, related_name='credit_records', verbose_name="相关消息")
    balance = models.IntegerField(verbose_name="变动后余额")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "积分记录"
        verbose_name_plural = "积分记录列表"
    
    def __str__(self):
        return f"{self.user.username}: {self.record_type} {self.credit_change:+d} -> {self.balance}"

class ChargeRecord(models.Model):
    """充值记录模型，用于记录用户的充值申请"""
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('paid', '已支付'),
        ('approved', '已通过'),
        ('rejected', '已拒绝'),
        ('canceled', '已取消'),
        ('failed', '支付失败')
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('lantupay', '蓝兔支付')
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='charge_records', verbose_name="用户")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="充值金额")
    credits = models.IntegerField(verbose_name="兑换积分")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="状态")
    transaction_code = models.CharField(max_length=20, unique=True, verbose_name="交易码")
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES, default="lantupay", verbose_name="支付方式")
    payment_url = models.URLField(max_length=500, blank=True, null=True, verbose_name="支付链接")
    payment_data = models.JSONField(blank=True, null=True, verbose_name="支付数据")
    admin_remark = models.TextField(blank=True, null=True, verbose_name="管理员备注")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    processed_at = models.DateTimeField(null=True, blank=True, verbose_name="处理时间")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "充值记录"
        verbose_name_plural = "充值记录列表"
    
    def __str__(self):
        return f"{self.user.username}: {self.amount}元 -> {self.credits}积分 ({self.get_status_display()})"
    
    def save(self, *args, **kwargs):
        # 如果是新记录，生成唯一的交易码
        if not self.transaction_code:
            self.transaction_code = ''.join(str(uuid.uuid4()).split('-'))[0:16].upper()
        super().save(*args, **kwargs)

class TokenPrice(models.Model):
    """Token价格模型，用于配置不同模型的token价格"""
    model = models.ForeignKey('chat.AIModel', on_delete=models.CASCADE, related_name='token_prices', verbose_name="模型")
    input_price = models.FloatField(default=0.0, verbose_name="输入token价格(积分/1000token)")
    output_price = models.FloatField(default=0.0, verbose_name="输出token价格(积分/1000token)")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    class Meta:
        verbose_name = "Token价格"
        verbose_name_plural = "Token价格列表"
        unique_together = ('model',)
    
    def __str__(self):
        return f"{self.model.display_name} - 输入:{self.input_price}/输出:{self.output_price}"

class SystemConfig(models.Model):
    """系统配置模型，用于存储系统级配置"""
    key = models.CharField(max_length=50, unique=True, verbose_name="配置键")
    value = models.TextField(verbose_name="配置值")
    description = models.CharField(max_length=255, blank=True, null=True, verbose_name="描述")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    class Meta:
        verbose_name = "系统配置"
        verbose_name_plural = "系统配置列表"
    
    def __str__(self):
        return f"{self.key}: {self.value[:50]}"

class PaymentConfig(models.Model):
    """支付配置模型，用于存储支付相关的配置"""
    PAYMENT_PROVIDER_CHOICES = [
        ('lantupay', '蓝兔支付')
    ]
    
    provider = models.CharField(max_length=50, choices=PAYMENT_PROVIDER_CHOICES, default='lantupay', unique=True, verbose_name="支付提供商")
    merchant_id = models.CharField(max_length=50, verbose_name="商户号")
    api_key = models.CharField(max_length=100, verbose_name="API密钥")
    api_url = models.URLField(max_length=255, default="https://api.ltzf.cn/api/wxpay/jump_h5", verbose_name="API地址")
    notify_url = models.URLField(max_length=255, verbose_name="支付回调通知地址")
    return_url = models.URLField(max_length=255, verbose_name="支付成功跳转地址")
    quit_url = models.URLField(max_length=255, blank=True, null=True, verbose_name="取消支付跳转地址")
    expire_time = models.CharField(max_length=10, default="5m", verbose_name="订单过期时间")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    class Meta:
        verbose_name = "支付配置"
        verbose_name_plural = "支付配置列表"
    
    def __str__(self):
        return f"{self.get_provider_display()}"
