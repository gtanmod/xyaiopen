import hashlib
import time
import json
import requests
import logging
import uuid
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from django.contrib.sites.models import Site

from .models import PaymentConfig, ChargeRecord

logger = logging.getLogger('payment')

def generate_lantu_sign(params, api_key):
    """
    生成蓝兔支付签名
    
    签名规则：
    1. 按参数名ASCII码从小到大排序
    2. 使用URL键值对的格式拼接成字符串
    3. 在字符串最后拼接上key=API_KEY
    4. 对字符串进行MD5运算，并转换为大写
    """
    # 1. 按参数名ASCII码从小到大排序
    sorted_params = sorted(params.items(), key=lambda x: x[0])
    
    # 2. 使用URL键值对的格式拼接成字符串
    query_string = '&'.join([f"{k}={v}" for k, v in sorted_params if v])
    
    # 3. 在字符串最后拼接上key=API_KEY
    query_string += f"&key={api_key}"
    
    # 4. 对字符串进行MD5运算，并转换为大写
    sign = hashlib.md5(query_string.encode('utf-8')).hexdigest().upper()
    
    return sign

def create_lantu_payment(charge_record):
    """创建蓝兔支付订单并获取支付链接"""
    try:
        # 获取支付配置
        payment_config = PaymentConfig.objects.filter(provider='lantupay', is_active=True).first()
        if not payment_config:
            logger.error("未找到蓝兔支付配置或配置未启用")
            return None, "未找到支付配置或配置未启用"
        
        # 获取当前域名
        try:
            current_site = Site.objects.get_current()
            domain = f"https://{current_site.domain}"
        except Exception as e:
            logger.warning(f"无法获取当前站点: {str(e)}，使用默认域名")
            domain = settings.SITE_URL if hasattr(settings, 'SITE_URL') else "https://example.com"
        
        # 构建回调地址
        notify_url = payment_config.notify_url or f"{domain}{reverse('credits:payment_notify')}"
        return_url = payment_config.return_url or f"{domain}{reverse('credits:payment_success')}"
        quit_url = payment_config.quit_url or f"{domain}{reverse('credits:payment_cancel')}"
        
        # 构建请求参数
        timestamp = str(int(time.time()))
        out_trade_no = charge_record.transaction_code
        
        params = {
            "mch_id": payment_config.merchant_id,
            "out_trade_no": out_trade_no,
            "total_fee": str(charge_record.amount),
            "body": f"积分充值-{charge_record.credits}积分",
            "timestamp": timestamp,
            "notify_url": notify_url,
            "return_url": return_url,
            "quit_url": quit_url,
            "time_expire": payment_config.expire_time,
            "attach": str(charge_record.id)
        }
        
        # 生成签名
        sign = generate_lantu_sign(params, payment_config.api_key)
        params["sign"] = sign
        
        # 发送请求
        logger.info(f"蓝兔支付请求参数: {params}")
        response = requests.post(payment_config.api_url, data=params)
        result = response.json()
        logger.info(f"蓝兔支付响应: {result}")
        
        if result.get('code') == 0:
            # 支付链接创建成功
            payment_url = result.get('data')
            
            # 更新充值记录
            charge_record.payment_url = payment_url
            charge_record.payment_data = result
            charge_record.save()
            
            return payment_url, None
        else:
            # 支付链接创建失败
            error_msg = result.get('msg', '创建支付链接失败')
            logger.error(f"创建支付链接失败: {error_msg}")
            return None, error_msg
    
    except Exception as e:
        logger.exception(f"创建支付链接异常: {str(e)}")
        return None, f"创建支付链接异常: {str(e)}"

def verify_lantu_payment_notification(request_data, api_key):
    """验证蓝兔支付回调通知的签名"""
    try:
        # 复制请求数据
        data = request_data.copy()
        
        # 取出签名
        sign = data.pop('sign', '')
        
        # 生成签名
        expected_sign = generate_lantu_sign(data, api_key)
        
        # 验证签名
        return sign == expected_sign
    
    except Exception as e:
        logger.exception(f"验证支付回调签名异常: {str(e)}")
        return False

def process_payment_notification(notification_data):
    """处理支付回调通知"""
    try:
        # 获取交易号
        out_trade_no = notification_data.get('out_trade_no')
        
        # 查找对应的充值记录
        charge_record = ChargeRecord.objects.filter(transaction_code=out_trade_no).first()
        if not charge_record:
            logger.error(f"未找到对应的充值记录: {out_trade_no}")
            return False, "未找到对应的充值记录"
        
        # 获取支付状态
        trade_state = notification_data.get('trade_state')
        
        # 只处理成功的支付
        if trade_state == 'SUCCESS':
            # 更新充值记录状态
            if charge_record.status == 'pending':
                charge_record.status = 'paid'
                charge_record.processed_at = timezone.now()
                charge_record.payment_data = notification_data
                charge_record.save()
                
                logger.info(f"充值记录 {out_trade_no} 已更新为已支付状态")
                return True, "支付成功"
            else:
                logger.warning(f"充值记录 {out_trade_no} 当前状态为 {charge_record.status}，无需重复处理")
                return True, "订单已处理"
        elif trade_state == 'NOTPAY':
            # 未支付，不做处理
            return True, "等待支付"
        else:
            # 其他状态，标记为失败
            charge_record.status = 'failed'
            charge_record.admin_remark = f"支付失败: {trade_state}"
            charge_record.processed_at = timezone.now()
            charge_record.save()
            
            logger.warning(f"充值记录 {out_trade_no} 支付失败: {trade_state}")
            return False, f"支付失败: {trade_state}"
    
    except Exception as e:
        logger.exception(f"处理支付回调通知异常: {str(e)}")
        return False, f"处理支付回调异常: {str(e)}" 