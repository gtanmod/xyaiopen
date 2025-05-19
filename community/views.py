from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib import messages
from django.core.paginator import Paginator
from django.urls import reverse
from django.db.models import Count
from django.conf import settings
from .models import Post, Comment, Like
import os
import uuid

def post_list(request):
    """显示所有帖子列表"""
    # 获取所有帖子，并附带评论数和点赞数
    posts = Post.objects.annotate(
        comment_count=Count('comments', distinct=True),
        like_count=Count('likes', distinct=True)
    ).order_by('-created_at')
    
    # 分页
    paginator = Paginator(posts, 10)  # 每页显示10篇帖子
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'community/post_list.html', {
        'page_obj': page_obj,
        'posts': page_obj,  # 添加posts变量，与模板中的变量名匹配
    })

def post_detail(request, pk):
    """帖子详情页"""
    post = get_object_or_404(Post, pk=pk)
    
    # 增加浏览次数
    post.views += 1
    post.save()
    
    # 获取评论
    comments = post.comments.all().select_related('author')
    
    # 检查当前用户是否已点赞
    user_liked = False
    if request.user.is_authenticated:
        user_liked = Like.objects.filter(post=post, user=request.user).exists()
    
    return render(request, 'community/post_detail.html', {
        'post': post,
        'comments': comments,
        'user_liked': user_liked
    })

@login_required
def add_comment(request, post_id):
    """添加评论"""
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if not content:
            messages.error(request, '评论内容不能为空')
            return redirect('community:post_detail', pk=post_id)
        
        post = get_object_or_404(Post, pk=post_id)
        Comment.objects.create(
            post=post,
            author=request.user,
            content=content
        )
        messages.success(request, '评论发表成功')
        return redirect('community:post_detail', pk=post_id)
    
    return redirect('community:post_detail', pk=post_id)

@login_required
def toggle_like(request, post_id):
    """切换点赞状态"""
    if request.method == 'POST':
        post = get_object_or_404(Post, pk=post_id)
        like_exists = Like.objects.filter(post=post, user=request.user).exists()
        
        if like_exists:
            # 如果已点赞，则取消点赞
            Like.objects.filter(post=post, user=request.user).delete()
            liked = False
        else:
            # 如果未点赞，则添加点赞
            Like.objects.create(post=post, user=request.user)
            liked = True
        
        # 获取最新的点赞数
        like_count = post.likes.count()
        
        # 如果是AJAX请求，返回JSON响应
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'liked': liked,
                'like_count': like_count
            })
        
        # 否则重定向回帖子详情页
        return redirect('community:post_detail', pk=post_id)
    
    return redirect('community:post_list')

@login_required
def create_post(request):
    """创建新帖子（仅管理员可用）"""
    # 检查用户是否为管理员
    if not request.user.is_staff:
        messages.error(request, '只有管理员才能发布帖子')
        return redirect('community:post_list')
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        
        if not title or not content:
            messages.error(request, '标题和内容不能为空')
            return render(request, 'community/create_post.html')
        
        try:
            # 处理图片上传
            image_path = None
            if request.FILES and 'post_image' in request.FILES:
                uploaded_image = request.FILES['post_image']
                
                # 检查文件大小（限制为2MB）
                if uploaded_image.size > 2 * 1024 * 1024:
                    messages.error(request, '图片大小不能超过2MB')
                    return render(request, 'community/create_post.html')
                
                # 检查文件类型
                allowed_types = ['image/jpeg', 'image/png', 'image/svg+xml']
                if uploaded_image.content_type not in allowed_types:
                    messages.error(request, '只支持JPG、PNG和SVG格式的图片')
                    return render(request, 'community/create_post.html')
                
                # 生成唯一文件名
                ext = uploaded_image.name.split('.')[-1]
                filename = f"{uuid.uuid4().hex}.{ext}"
                
                # 确保目录存在
                upload_dir = os.path.join(settings.MEDIA_ROOT, 'community/posts')
                os.makedirs(upload_dir, exist_ok=True)
                
                # 保存文件
                file_path = os.path.join(upload_dir, filename)
                with open(file_path, 'wb+') as destination:
                    for chunk in uploaded_image.chunks():
                        destination.write(chunk)
                
                # 设置相对路径
                image_path = f'community/posts/{filename}'
            
            # 创建帖子
            post = Post.objects.create(
                title=title,
                content=content,
                author=request.user,
                image=image_path
            )
            
            messages.success(request, '帖子发布成功')
            return redirect('community:post_detail', pk=post.id)
            
        except PermissionError:
            messages.error(request, '只有管理员才能发布帖子')
            return redirect('community:post_list')
        except Exception as e:
            messages.error(request, f'发布失败：{str(e)}')
            return render(request, 'community/create_post.html')
    
    return render(request, 'community/create_post.html')
