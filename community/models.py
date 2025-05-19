from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import markdown
from django.utils.safestring import mark_safe

class Post(models.Model):
    """帖子模型 - 只有管理员可以创建"""
    title = models.CharField('标题', max_length=200)
    content = models.TextField('内容')
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='作者')
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    views = models.PositiveIntegerField('浏览次数', default=0)
    image = models.CharField('图片路径', max_length=255, blank=True, null=True)
    
    class Meta:
        verbose_name = '帖子'
        verbose_name_plural = '帖子'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # 确保只有管理员才能发帖
        if not self.pk and not self.author.is_staff:
            raise PermissionError("只有管理员才能发布帖子")
        super().save(*args, **kwargs)
    
    def get_comments_count(self):
        return self.comments.count()
    
    def get_likes_count(self):
        return self.likes.count()
    
    def get_markdown_content(self):
        """将Markdown内容转换为HTML"""
        extensions = [
            'markdown.extensions.extra',
            'markdown.extensions.codehilite',
            'markdown.extensions.tables',
            'markdown.extensions.toc',
        ]
        html = markdown.markdown(self.content, extensions=extensions)
        return mark_safe(html)


class Comment(models.Model):
    """评论模型 - 所有用户都可以评论"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments', verbose_name='帖子')
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='作者')
    content = models.TextField('内容')
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    
    class Meta:
        verbose_name = '评论'
        verbose_name_plural = '评论'
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.author.username}的评论: {self.content[:30]}"


class Like(models.Model):
    """点赞模型 - 用户可以点赞帖子"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes', verbose_name='帖子')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    
    class Meta:
        verbose_name = '点赞'
        verbose_name_plural = '点赞'
        unique_together = ('post', 'user')  # 确保一个用户只能给一个帖子点一次赞
        
    def __str__(self):
        return f"{self.user.username}点赞了{self.post.title[:20]}"
