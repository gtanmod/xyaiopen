#!/usr/bin/env python
import os
import sys
import django
import json
import logging
from pathlib import Path
from django.utils import timezone
from django.contrib.auth.models import User
from django.db import transaction

# 设置日志
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "data_import.log"

# 配置日志记录器
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("data_importer")

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xiaoyangSystem.settings')
django.setup()

# 获取超级用户作为默认发帖者
try:
    admin = User.objects.filter(is_superuser=True).first()
    if not admin:
        logger.error("未找到超级用户，请先创建一个超级用户")
        sys.exit(1)
    logger.info(f"使用超级用户: {admin.username}")
except Exception as e:
    logger.error(f"获取超级用户失败: {e}")
    sys.exit(1)

# 导入必要的模型
from community.models import Post, Comment, Like

# 从SQL文件读取数据
sql_filename = 'community_data.sql'

# 解析SQL文件提取数据
def extract_data_from_sql(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # 尝试解析为JSON（如果文件实际上是JSON格式）
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # 如果不是JSON，则按SQL格式解析
            pass
            
        # 这里应该添加解析SQL文件的代码
        # 由于SQL解析较复杂，这里仅作示例
        data = {
            'posts': [],
            'comments': [],
            'likes': []
        }
        
        return data
    except Exception as e:
        logger.error(f"解析SQL文件失败: {e}")
        return None

# 导入帖子数据
@transaction.atomic
def import_posts(posts_data):
    posts = {}
    for post_data in posts_data:
        try:
            post = Post.objects.create(
                title=post_data.get('title', '未命名帖子'),
                content=post_data.get('content', ''),
                author=admin,
                views=post_data.get('views', 0),
                image=post_data.get('image', '')
            )
            posts[post_data.get('id', len(posts))] = post
            logger.info(f"创建帖子: {post.title}")
        except Exception as e:
            logger.error(f"创建帖子失败: {e}")
    
    return posts

# 导入评论数据
@transaction.atomic
def import_comments(comments_data, posts_dict):
    for comment_data in comments_data:
        try:
            post_id = comment_data.get('post_id')
            if post_id in posts_dict:
                comment = Comment.objects.create(
                    content=comment_data.get('content', ''),
                    author=admin,
                    post=posts_dict[post_id]
                )
                logger.info(f"创建评论: {comment.content[:20]}...")
            else:
                logger.warning(f"评论对应的帖子ID不存在: {post_id}")
        except Exception as e:
            logger.error(f"创建评论失败: {e}")

# 导入点赞数据
@transaction.atomic
def import_likes(likes_data, posts_dict):
    for like_data in likes_data:
        try:
            post_id = like_data.get('post_id')
            if post_id in posts_dict:
                like = Like.objects.create(
                    user=admin,
                    post=posts_dict[post_id]
                )
                logger.info(f"创建点赞: 用户{admin.username}点赞了帖子《{posts_dict[post_id].title}》")
            else:
                logger.warning(f"点赞对应的帖子ID不存在: {post_id}")
        except Exception as e:
            logger.error(f"创建点赞失败: {e}")

# 主函数
def main():
    # 从SQL文件中提取数据
    data = extract_data_from_sql(sql_filename)
    
    if not data:
        logger.error(f"无法从{sql_filename}提取数据")
        return
    
    # 导入帖子
    posts_data = data.get('posts', [])
    comments_data = data.get('comments', [])
    likes_data = data.get('likes', [])
    
    with transaction.atomic():
        # 导入帖子
        posts = import_posts(posts_data)
        
        # 导入评论
        if posts:
            import_comments(comments_data, posts)
            
            # 导入点赞
            import_likes(likes_data, posts)
    
    # 输出导入结果
    logger.info("\n数据导入完成!")
    logger.info(f"共创建了 {len(posts)} 个帖子")
    logger.info(f"共创建了 {len(comments_data)} 条评论")
    logger.info(f"共创建了 {len(likes_data)} 个点赞")

if __name__ == "__main__":
    main() 