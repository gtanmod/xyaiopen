from django import template
import math

register = template.Library()

@register.filter
def multiply(value, arg):
    """将值乘以参数"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def div(value, arg):
    """将值除以参数"""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0
        
@register.filter
def bonus_credits(amount):
    """计算充值金额对应的赠送积分（满100赠送10%）"""
    try:
        amount = float(amount)
        if amount >= 100:
            return math.floor(amount * 0.1)
        return 0
    except (ValueError, TypeError):
        return 0 