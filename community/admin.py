from django.contrib import admin
from .models import Post, Comment, Like

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at', 'updated_at', 'views', 'get_comments_count', 'get_likes_count')
    list_filter = ('created_at', 'author')
    search_fields = ('title', 'content')
    date_hierarchy = 'created_at'
    readonly_fields = ('views',)
    
    def get_comments_count(self, obj):
        return obj.comments.count()
    get_comments_count.short_description = '评论数'
    
    def get_likes_count(self, obj):
        return obj.likes.count()
    get_likes_count.short_description = '点赞数'
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:  # 如果是新创建的对象
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'post', 'short_content', 'created_at')
    list_filter = ('created_at', 'author')
    search_fields = ('content', 'author__username', 'post__title')
    date_hierarchy = 'created_at'
    
    def short_content(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    short_content.short_description = '评论内容'


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'created_at')
    list_filter = ('created_at', 'user')
    date_hierarchy = 'created_at'
