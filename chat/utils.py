import tiktoken
import logging
from datetime import datetime
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from .models import Message
from credits.models import UserProfile, CreditRecord, TokenPrice

logger = logging.getLogger(__name__)

def num_tokens_from_string(string, model="gpt-4o"):
    """计算字符串的token数量"""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        logger.warning(f"Model {model} not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
    
    # 特殊情况：空字符串
    if not string.strip():
        return 0
    
    # 针对较长的字符串进行优化处理
    if len(string) > 1000000:
        # 对于非常长的字符串，我们采用采样估算的方式
        sample_size = min(len(string), 100000)
        samples = [
            string[:sample_size//3],
            string[len(string)//2-sample_size//6:len(string)//2+sample_size//6],
            string[-sample_size//3:]
        ]
        tokens_per_char = sum(len(encoding.encode(s)) for s in samples) / sum(len(s) for s in samples)
        return int(tokens_per_char * len(string))
    
    return len(encoding.encode(string))

def count_message_tokens(message, model="gpt-4o"):
    """计算消息的token数量"""
    if not message:
        return 0, 0

    if not message.content:
        return 0, 0

    if message.role == "user":
        return num_tokens_from_string(message.content, model), 0
    elif message.role == "assistant":
        return 0, num_tokens_from_string(message.content, model)
    return 0, 0

def update_message_tokens(message, model="gpt-4o"):
    """更新消息的token计数"""
    if message.input_tokens > 0 and message.output_tokens > 0:
        # 如果已经计算过token，则跳过
        return message.input_tokens, message.output_tokens
        
    input_tokens, output_tokens = count_message_tokens(message, model)
    
    # 更新消息的token计数
    message.input_tokens = input_tokens
    message.output_tokens = output_tokens
    message.save(update_fields=['input_tokens', 'output_tokens'])
    
    return input_tokens, output_tokens

def deduct_message_credits(user, message, model_id):
    """根据消息token数量扣除用户积分"""
    with transaction.atomic():
        # 获取用户资料
        profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={'credits': 0}
        )
        
        # 获取token价格配置
        try:
            token_price = TokenPrice.objects.get(model__model_id=model_id, is_active=True)
        except TokenPrice.DoesNotExist:
            logger.warning(f"Token price for model {model_id} not found, using default pricing")
            input_price = 0.05  # 默认输入token价格：0.05积分/1000token
            output_price = 0.1   # 默认输出token价格：0.1积分/1000token
        else:
            input_price = token_price.input_price
            output_price = token_price.output_price
        
        # 计算需要扣除的积分
        input_tokens = message.input_tokens
        output_tokens = message.output_tokens
        
        input_credits = (input_tokens / 1000) * input_price
        output_credits = (output_tokens / 1000) * output_price
        total_credits = int((input_credits + output_credits) * 100) / 100  # 保留2位小数
        
        # 如果总积分小于0.01，则不扣除
        if total_credits < 0.01:
            return 0
        
        # 扣除积分
        total_credits_int = int(total_credits)  # 取整
        if total_credits_int == 0:
            total_credits_int = 1  # 最少扣除1积分
            
        if profile.credits < total_credits_int:
            logger.warning(f"User {user.username} has insufficient credits")
            return -1  # 积分不足
        
        profile.credits -= total_credits_int
        profile.save(update_fields=['credits'])
        
        # 创建积分记录
        description = f"使用AI对话 (输入:{input_tokens}词元, 输出:{output_tokens}词元)"
        CreditRecord.objects.create(
            user=user,
            credit_change=-total_credits_int,
            record_type='usage',
            description=description,
            message=message,
            balance=profile.credits
        )
        
        return total_credits_int  # 返回扣除的积分 