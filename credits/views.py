from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.db import transaction
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Sum, Case, When, IntegerField, F
from django.views.decorators.csrf import csrf_exempt
import datetime
import json
import logging
import time

from .models import UserProfile, CreditRecord, ChargeRecord, SystemConfig, PaymentConfig
from .utils import create_lantu_payment, verify_lantu_payment_notification, process_payment_notification
from django.contrib.auth.models import User
from chat.models import AIModel

# 配置日志
logger = logging.getLogger('payment')

# 获取系统配置值的辅助函数
def get_system_config(key, default=None):
    """获取系统配置值"""
    try:
        config = SystemConfig.objects.get(key=key, is_active=True)
        return config.value
    except SystemConfig.DoesNotExist:
        return default

# 获取用户积分统计的辅助函数
def get_user_credits_stats(user):
    """获取用户积分统计信息"""
    # 获取用户资料
    profile, created = UserProfile.objects.get_or_create(
        user=user,
        defaults={'credits': 0}
    )
    
    # 统计总获得和消费的积分
    credit_records = CreditRecord.objects.filter(user=user)
    total_earned = credit_records.filter(credit_change__gt=0).aggregate(total=Sum('credit_change'))['total'] or 0
    total_spent = credit_records.filter(credit_change__lt=0).aggregate(total=Sum('credit_change'))['total'] or 0
    
    # 转换总消费为正数
    total_spent = abs(total_spent)
    
    return {
        'profile': profile,
        'total_earned': total_earned,
        'total_spent': total_spent
    }

# 格式化充值选项的辅助函数
def format_recharge_options():
    """获取并格式化充值选项为侧边栏所需的格式"""
    # 获取充值选项
    recharge_options = get_system_config('recharge_options', '[]')
    try:
        recharge_options = json.loads(recharge_options)
    except json.JSONDecodeError:
        recharge_options = []
    
    # 获取积分兑换比例
    credit_exchange_rate = float(get_system_config('credit_exchange_rate', '10.0'))
    
    # 处理快速充值选项为侧边栏所需的格式
    quick_recharge_options = []
    for option in recharge_options:
        amount = float(option) if isinstance(option, (int, float, str)) else option.get('amount', 0)
        credits = int(amount * credit_exchange_rate)
        bonus = 0
        
        # 如果充值额度大于等于100，则额外赠送10%
        if amount >= 100:
            bonus = int(amount * 0.1)
        
        quick_recharge_options.append({
            'amount': amount,
            'credits': credits,
            'bonus': bonus if bonus > 0 else None
        })
    
    return {
        'recharge_options': recharge_options,
        'quick_recharge_options': quick_recharge_options,
        'credit_exchange_rate': credit_exchange_rate
    }

# 判断是否是管理员的辅助函数
def is_admin(user):
    """判断用户是否具有管理员权限"""
    return user.is_superuser or user.is_staff

@login_required
def dashboard(request):
    """积分中心首页，显示用户积分概况"""
    # 获取用户积分统计
    credits_stats = get_user_credits_stats(request.user)
    
    # 获取最近5条积分记录
    recent_records = CreditRecord.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    # 获取最近5条充值记录
    recent_charges = ChargeRecord.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    # 获取AI模型列表及其积分消耗
    ai_models = AIModel.objects.filter(is_active=True).order_by('sort_order')
    models_with_prices = []
    
    for model in ai_models:
        # 获取模型对应的token价格
        token_price = model.token_prices.filter(is_active=True).first()
        
        if token_price:
            models_with_prices.append({
                'name': model.model_id,
                'display_name': model.display_name,
                'input_price': token_price.input_price,
                'output_price': token_price.output_price,
                'description': model.description
            })
    
    # 获取格式化的充值选项
    recharge_data = format_recharge_options()
    
    # 判断用户今天是否已经签到
    profile = credits_stats['profile']
    today = timezone.now().date()
    signed_today = profile.last_sign_in and profile.last_sign_in == today
    
    # 计算可能的签到奖励积分
    base_credits = int(get_system_config('sign_in_base_credits', '5'))
    continuous_bonus = int(get_system_config('sign_in_continuous_bonus', '2'))
    max_bonus = int(get_system_config('sign_in_max_bonus', '15'))
    
    # 如果明天是连续签到，计算额外奖励
    continuous_days = profile.continuous_sign_days + 1 if signed_today else 1
    bonus_credits = min(continuous_bonus * (continuous_days - 1), max_bonus) if continuous_days > 1 else 0
    possible_credits = base_credits + bonus_credits
    
    context = {
        'profile': profile,
        'total_earned': credits_stats['total_earned'],
        'total_spent': credits_stats['total_spent'],
        'recent_records': recent_records,
        'recent_charges': recent_charges,
        'models_with_prices': models_with_prices,
        'signed_today': signed_today,  # 添加是否已签到的状态
        'possible_credits': possible_credits  # 添加可能获得的积分数
    }
    
    # 更新context，添加充值选项相关数据
    context.update(recharge_data)
    
    return render(request, 'credits/dashboard.html', context)

@login_required
@require_POST
def sign_in(request):
    """用户签到领取积分"""
    # 添加请求信息记录，用于调试
    print(f"签到请求头: {request.headers}")
    
    try:
        # 获取用户资料
        profile, created = UserProfile.objects.get_or_create(
            user=request.user,
            defaults={'credits': 0}
        )
        
        # 检查今天是否已经签到
        today = timezone.now().date()
        
        # 更全面的AJAX请求检查
        is_ajax = (
            request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 
            request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest' or
            request.GET.get('ajax') == '1' or
            request.POST.get('ajax') == '1'
        )
        
        if profile.last_sign_in and profile.last_sign_in == today:
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'message': '您今天已经签到过了，明天再来吧'
                })
            messages.info(request, '您今天已经签到过了，明天再来吧')
            return redirect('credits:dashboard')
        
        # 判断是否是连续签到（昨天签到过）
        yesterday = today - datetime.timedelta(days=1)
        is_continuous = profile.last_sign_in == yesterday
        
        # 获取签到基础积分和连续签到奖励
        base_credits = int(get_system_config('sign_in_base_credits', '5'))
        continuous_bonus = int(get_system_config('sign_in_continuous_bonus', '2'))
        max_bonus = int(get_system_config('sign_in_max_bonus', '15'))
        
        # 更新连续签到天数
        if is_continuous:
            profile.continuous_sign_days += 1
        else:
            profile.continuous_sign_days = 1
        
        # 计算额外奖励（最多不超过上限）
        bonus_credits = min(continuous_bonus * (profile.continuous_sign_days - 1), max_bonus) if profile.continuous_sign_days > 1 else 0
        
        # 计算总奖励积分
        awarded_credits = base_credits + bonus_credits
        
        # 更新用户积分和签到记录
        with transaction.atomic():
            profile.credits += awarded_credits
            profile.last_sign_in = today
            profile.total_sign_days += 1
            profile.save()
            
            # 记录积分变动
            CreditRecord.objects.create(
                user=request.user,
                credit_change=awarded_credits,
                record_type='sign_in',
                description=f"签到奖励 (基础{base_credits} + 连续{bonus_credits})",
                balance=profile.credits
            )
        
        # 返回响应消息
        success_message = f'签到成功！获得{awarded_credits}积分'
        if bonus_credits > 0:
            success_message = f'签到成功！获得{awarded_credits}积分 (含连续签到{profile.continuous_sign_days}天奖励{bonus_credits}积分)'
        
        if is_ajax:
            return JsonResponse({
                'success': True,
                'message': success_message,
                'credits': profile.credits,
                'awarded_credits': awarded_credits
            })
        
        messages.success(request, success_message)
        return redirect('credits:dashboard')
        
    except Exception as e:
        logger.error(f"签到异常: {str(e)}")
        error_message = f'签到失败: {str(e)}'
        
        # 更全面的AJAX请求检查
        is_ajax = (
            request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 
            request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest' or
            request.GET.get('ajax') == '1' or
            request.POST.get('ajax') == '1'
        )
        
        if is_ajax:
            return JsonResponse({
                'success': False,
                'message': error_message,
                'error': str(e)
            })
            
        messages.error(request, error_message)
        return redirect('credits:dashboard')

@login_required
def credit_records(request):
    """查看用户的积分记录"""
    # 获取用户积分统计
    credits_stats = get_user_credits_stats(request.user)
    
    # 获取用户的所有积分记录
    records = CreditRecord.objects.filter(user=request.user).order_by('-created_at')
    
    # 分页处理
    paginator = Paginator(records, 20)  # 每页20条
    page = request.GET.get('page')
    
    try:
        paginated_records = paginator.page(page)
    except PageNotAnInteger:
        paginated_records = paginator.page(1)
    except EmptyPage:
        paginated_records = paginator.page(paginator.num_pages)
    
    context = {
        'page_obj': paginated_records,
        'profile': credits_stats['profile'],
        'total_earned': credits_stats['total_earned'],
        'total_spent': credits_stats['total_spent']
    }
    
    return render(request, 'credits/credit_records.html', context)

@login_required
def recharge(request):
    """积分充值页面"""
    # 获取用户积分统计
    credits_stats = get_user_credits_stats(request.user)
    
    # 获取格式化的充值选项
    recharge_data = format_recharge_options()
    
    # 如果URL中有预选金额参数
    pre_selected_amount = request.GET.get('amount', None)
    
    context = {
        'profile': credits_stats['profile'],
        'pre_selected_amount': pre_selected_amount,
        'total_earned': credits_stats['total_earned'],
        'total_spent': credits_stats['total_spent'],
        'exchange_rate': recharge_data['credit_exchange_rate']
    }
    
    # 更新context，添加充值选项相关数据
    context.update(recharge_data)
    
    # 检查是否有蓝兔支付配置
    has_payment_config = PaymentConfig.objects.filter(provider='lantupay', is_active=True).exists()
    context['has_payment_config'] = has_payment_config
    
    if not has_payment_config:
        messages.warning(request, '支付功能暂未配置，请联系管理员')
    
    return render(request, 'credits/recharge.html', context)

@login_required
@require_POST
def create_charge_record(request):
    """创建充值记录并生成支付链接"""
    try:
        amount = float(request.POST.get('amount', 0))
        payment_method = request.POST.get('payment_method', 'lantupay')
        
        if amount <= 0:
            messages.error(request, '充值金额必须大于0')
            return redirect('credits:recharge')
        
        # 获取积分兑换比例
        credit_exchange_rate = float(get_system_config('credit_exchange_rate', '10.0'))
        
        # 计算积分值 (如果金额≥100元，赠送10%积分)
        base_credits = int(amount * credit_exchange_rate)
        bonus_credits = int(amount * 0.1) if amount >= 100 else 0
        credits = base_credits + bonus_credits
        
        # 创建充值记录
        charge_record = ChargeRecord.objects.create(
            user=request.user,
            amount=amount,
            credits=credits,
            payment_method=payment_method
        )
        
        # 创建支付链接
        if payment_method == 'lantupay':
            payment_url, error_msg = create_lantu_payment(charge_record)
            
            if payment_url:
                # 支付链接创建成功，重定向到支付链接
                return redirect(payment_url)
            else:
                # 支付链接创建失败
                messages.error(request, f'创建支付链接失败: {error_msg}')
                charge_record.delete()  # 删除创建的充值记录
                return redirect('credits:recharge')
        else:
            messages.error(request, f'不支持的支付方式: {payment_method}')
            charge_record.delete()
            return redirect('credits:recharge')
        
    except ValueError:
        messages.error(request, '请输入有效的金额')
        return redirect('credits:recharge')
    except Exception as e:
        logger.exception(f"创建充值记录异常: {str(e)}")
        messages.error(request, f'创建充值记录失败: {str(e)}')
        return redirect('credits:recharge')

@login_required
def recharge_result(request, transaction_code):
    """充值结果页面"""
    charge_record = get_object_or_404(ChargeRecord, transaction_code=transaction_code, user=request.user)
    
    # 获取用户积分统计
    credits_stats = get_user_credits_stats(request.user)
    
    # 获取格式化的充值选项
    recharge_data = format_recharge_options()
    
    context = {
        'charge_record': charge_record,
        'profile': credits_stats['profile'],
        'total_earned': credits_stats['total_earned'],
        'total_spent': credits_stats['total_spent']
    }
    
    # 更新context，添加充值选项相关数据
    context.update(recharge_data)
    
    return render(request, 'credits/recharge_result.html', context)

@csrf_exempt
def payment_notify(request):
    """支付通知接口，接收支付平台的支付结果通知"""
    try:
        if request.method != 'POST':
            return HttpResponse("仅支持POST请求")
        
        # 获取请求数据
        try:
            notification_data = json.loads(request.body)
            logger.info(f"收到支付通知: {notification_data}")
        except:
            notification_data = request.POST.dict()
            logger.info(f"收到表单格式支付通知: {notification_data}")
        
        # 获取支付配置
        payment_config = PaymentConfig.objects.filter(provider='lantupay', is_active=True).first()
        if not payment_config:
            logger.error("未找到蓝兔支付配置")
            return HttpResponse("未找到支付配置")
        
        # 验证通知数据的签名
        if not verify_lantu_payment_notification(notification_data, payment_config.api_key):
            logger.error("支付通知签名验证失败")
            return HttpResponse("签名验证失败")
        
        # 处理支付通知
        success, msg = process_payment_notification(notification_data)
        
        # 返回处理结果
        if success:
            return HttpResponse("SUCCESS")
        else:
            return HttpResponse(f"FAIL: {msg}")
            
    except Exception as e:
        logger.exception(f"处理支付通知异常: {str(e)}")
        return HttpResponse(f"FAIL: {str(e)}")

@login_required
def payment_success(request):
    """支付成功回跳页面"""
    # 查询用户最近的充值记录
    charge_record = ChargeRecord.objects.filter(
        user=request.user,
        status__in=['paid', 'approved']
    ).order_by('-created_at').first()
    
    if charge_record:
        messages.success(request, '支付成功！积分将在确认后添加到您的账户')
        return redirect('credits:recharge_result', transaction_code=charge_record.transaction_code)
    else:
        messages.info(request, '支付成功！但未找到对应的充值记录，请联系客服')
        return redirect('credits:charge_records')

@login_required
def payment_cancel(request):
    """支付取消回跳页面"""
    messages.info(request, '您已取消本次支付，可以重新发起充值')
    return redirect('credits:recharge')

@login_required
@user_passes_test(is_admin)
def admin_charge_records(request):
    """管理员查看充值记录"""
    status = request.GET.get('status', '')
    username = request.GET.get('username', '')
    
    charges = ChargeRecord.objects.all().order_by('-created_at')
    
    # 按状态筛选
    if status:
        charges = charges.filter(status=status)
    
    # 按用户名筛选
    if username:
        charges = charges.filter(user__username__icontains=username)
    
    # 分页处理
    paginator = Paginator(charges, 20)  # 每页20条
    page = request.GET.get('page')
    
    try:
        charge_records = paginator.page(page)
    except PageNotAnInteger:
        charge_records = paginator.page(1)
    except EmptyPage:
        charge_records = paginator.page(paginator.num_pages)
    
    context = {
        'charge_records': charge_records,
        'status': status,
        'username': username
    }
    
    return render(request, 'credits/admin_charge_records.html', context)

@login_required
@user_passes_test(is_admin)
@require_POST
def process_charge_record(request, record_id):
    """管理员处理充值记录"""
    action = request.POST.get('action')
    admin_remark = request.POST.get('admin_remark', '')
    
    if action not in ['approve', 'reject']:
        messages.error(request, '无效的操作')
        return redirect('credits:admin_charge_records')
    
    try:
        with transaction.atomic():
            charge_record = get_object_or_404(ChargeRecord, id=record_id)
            
            # 确保记录是待处理或已支付状态
            if charge_record.status not in ['pending', 'paid']:
                messages.error(request, '只能处理待处理或已支付状态的记录')
                return redirect('credits:admin_charge_records')
            
            if action == 'approve':
                # 获取用户资料
                profile, created = UserProfile.objects.get_or_create(
                    user=charge_record.user,
                    defaults={'credits': 0}
                )
                
                # 更新用户积分
                profile.credits += charge_record.credits
                profile.save()
                
                # 记录积分变动
                base_credits = int(charge_record.amount * float(get_system_config('credit_exchange_rate', '10.0')))
                bonus_credits = charge_record.credits - base_credits
                
                description = f"充值{charge_record.amount}元获得{base_credits}积分"
                if bonus_credits > 0:
                    description += f" (赠送{bonus_credits}积分)"
                
                CreditRecord.objects.create(
                    user=charge_record.user,
                    credit_change=charge_record.credits,
                    record_type='charge',
                    description=description,
                    balance=profile.credits
                )
                
                # 更新充值记录状态
                charge_record.status = 'approved'
                charge_record.admin_remark = admin_remark
                charge_record.processed_at = timezone.now()
                charge_record.save()
                
                messages.success(request, f'已批准充值记录 #{record_id}')
            
            elif action == 'reject':
                # 更新充值记录状态
                charge_record.status = 'rejected'
                charge_record.admin_remark = admin_remark
                charge_record.processed_at = timezone.now()
                charge_record.save()
                
                messages.success(request, f'已拒绝充值记录 #{record_id}')
        
        return redirect('credits:admin_charge_records')
        
    except Exception as e:
        messages.error(request, f'处理充值记录失败: {str(e)}')
        return redirect('credits:admin_charge_records')

@login_required
def user_charge_records(request):
    """用户查看自己的充值记录"""
    # 获取用户积分统计
    credits_stats = get_user_credits_stats(request.user)
    
    # 获取用户的所有充值记录
    charges = ChargeRecord.objects.filter(user=request.user).order_by('-created_at')
    
    # 分页处理
    paginator = Paginator(charges, 10)  # 每页10条
    page = request.GET.get('page')
    
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    context = {
        'page_obj': page_obj,
        'profile': credits_stats['profile'],
        'total_earned': credits_stats['total_earned'],
        'total_spent': credits_stats['total_spent']
    }
    
    return render(request, 'credits/charge_records.html', context)

@login_required
def user_credits_api(request):
    """API接口获取用户积分信息"""
    try:
        # 直接查询用户的积分信息，避免使用辅助函数可能带来的复杂性
        profile, created = UserProfile.objects.get_or_create(
            user=request.user,
            defaults={'credits': 0}
        )
        
        # 确保积分数据是整数
        credits = int(profile.credits) if profile and profile.credits is not None else 0
        
        # 可选地获取总收入和支出
        try:
            from django.db.models import Sum
            credit_records = CreditRecord.objects.filter(user=request.user)
            total_earned = credit_records.filter(credit_change__gt=0).aggregate(total=Sum('credit_change'))['total'] or 0
            total_spent = abs(credit_records.filter(credit_change__lt=0).aggregate(total=Sum('credit_change'))['total'] or 0)
            
            # 确保是整数
            total_earned = int(total_earned)
            total_spent = int(total_spent)
        except Exception as e:
            logger.warning(f"计算总收入和支出时出错: {str(e)}")
            total_earned = 0
            total_spent = 0
        
        # 添加时间戳，帮助客户端识别响应时间
        timestamp = int(time.time())
        
        return JsonResponse({
            'success': True,
            'credits': credits,
            'total_earned': total_earned,
            'total_spent': total_spent,
            'timestamp': timestamp
        })
    except Exception as e:
        logger.error(f"获取用户积分API异常: {str(e)}")
        
        # 尝试获取用户资料作为备用方案
        try:
            profile = UserProfile.objects.get(user=request.user)
            credits = int(profile.credits) if profile.credits is not None else 0
        except:
            credits = 0
        
        # 添加时间戳，帮助客户端识别响应时间
        timestamp = int(time.time())
            
        return JsonResponse({
            'success': False,
            'message': str(e),
            'credits': credits,  # 使用获取到的积分或默认为0
            'total_earned': 0,
            'total_spent': 0,
            'timestamp': timestamp
        })
