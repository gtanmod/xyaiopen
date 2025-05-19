from django.contrib import admin
from .models import UserProfile, CreditRecord, ChargeRecord, TokenPrice, SystemConfig, PaymentConfig

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'credits', 'last_sign_in', 'continuous_sign_days', 'total_sign_days', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(CreditRecord)
class CreditRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'record_type', 'credit_change', 'balance', 'description', 'created_at')
    list_filter = ('record_type', 'created_at')
    search_fields = ('user__username', 'description')
    readonly_fields = ('user', 'credit_change', 'record_type', 'description', 'message', 'balance', 'created_at')
    
    def has_add_permission(self, request):
        # 防止直接添加积分记录
        return False
    
    def has_change_permission(self, request, obj=None):
        # 防止修改积分记录
        return False

@admin.register(ChargeRecord)
class ChargeRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'credits', 'status', 'transaction_code', 'payment_method', 'created_at', 'processed_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('user__username', 'transaction_code', 'admin_remark')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'transaction_code', 'payment_url', 'payment_data')
    
    def has_delete_permission(self, request, obj=None):
        # 防止意外删除充值记录
        return False
    
    fieldsets = (
        ('基本信息', {
            'fields': ('user', 'amount', 'credits', 'status', 'transaction_code', 'payment_method')
        }),
        ('支付信息', {
            'fields': ('payment_url', 'payment_data')
        }),
        ('管理信息', {
            'fields': ('admin_remark', 'created_at', 'processed_at')
        }),
    )

@admin.register(TokenPrice)
class TokenPriceAdmin(admin.ModelAdmin):
    list_display = ('model', 'input_price', 'output_price', 'is_active', 'updated_at')
    list_filter = ('is_active', 'model')
    search_fields = ('model__name', 'model__display_name')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(SystemConfig)
class SystemConfigAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'description', 'is_active', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('key', 'value', 'description')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(PaymentConfig)
class PaymentConfigAdmin(admin.ModelAdmin):
    list_display = ('provider', 'merchant_id', 'is_active', 'updated_at')
    list_filter = ('is_active', 'provider')
    search_fields = ('provider', 'merchant_id')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('基本信息', {
            'fields': ('provider', 'merchant_id', 'api_key', 'is_active')
        }),
        ('API配置', {
            'fields': ('api_url', 'notify_url', 'return_url', 'quit_url', 'expire_time')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def has_delete_permission(self, request, obj=None):
        # 限制删除，一般只修改
        return False
