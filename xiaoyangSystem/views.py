from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django import forms
from django.views.decorators.csrf import ensure_csrf_cookie

class CustomUserCreationForm(UserCreationForm):
    """扩展Django默认的UserCreationForm，添加电子邮件字段"""
    email = forms.EmailField(label='电子邮箱', required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 自定义表单字段的标签
        self.fields['username'].label = '用户名'
        self.fields['username'].help_text = '用户名只能包含字母、数字和下划线。'
        self.fields['password1'].label = '密码'
        self.fields['password1'].help_text = '您的密码必须至少包含8个字符，不能太常见。'
        self.fields['password2'].label = '确认密码'
        self.fields['password2'].help_text = '请再次输入相同的密码进行验证。'
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

@ensure_csrf_cookie
def register_view(request):
    """用户注册视图"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            # 注册成功后自动登录用户
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            messages.success(request, f'账号创建成功！欢迎 {username}')
            return redirect('chat:index')
    else:
        form = CustomUserCreationForm()
    
    # 确保context包含了request，这对CSRF token很重要
    return render(request, 'register.html', {'form': form}) 