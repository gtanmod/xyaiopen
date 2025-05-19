from django.urls import path
from . import views

app_name = 'credits'

urlpatterns = [
    # 积分中心首页
    path('', views.dashboard, name='dashboard'),
    
    # 签到功能
    path('sign-in/', views.sign_in, name='sign_in'),
    
    # 积分明细
    path('records/', views.credit_records, name='credit_records'),
    
    # 用户充值记录
    path('charge-records/', views.user_charge_records, name='charge_records'),
    
    # 充值相关
    path('recharge/', views.recharge, name='recharge'),
    path('recharge/create/', views.create_charge_record, name='create_charge_record'),
    path('recharge/result/<str:transaction_code>/', views.recharge_result, name='recharge_result'),
    
    # 支付通知和回调
    path('payment/notify/', views.payment_notify, name='payment_notify'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/cancel/', views.payment_cancel, name='payment_cancel'),
    
    # 管理员功能
    path('admin/charge-records/', views.admin_charge_records, name='admin_charge_records'),
    path('admin/process-charge/<int:record_id>/', views.process_charge_record, name='process_charge_record'),
    
    # API接口
    path('api/user-credits/', views.user_credits_api, name='user_credits_api'),
] 