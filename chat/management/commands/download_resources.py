from django.core.management.base import BaseCommand
import os
import urllib.request
import shutil
import subprocess

class Command(BaseCommand):
    help = '下载并安装所需的JavaScript资源文件'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('开始下载所需资源...'))
        
        # 创建必要的目录
        self._ensure_directories()
        
        # 下载marked.min.js
        self._download_marked()
        
        # 下载其他可能需要的资源
        # self._download_additional_resources()
        
        self.stdout.write(self.style.SUCCESS('所有资源下载完成!'))
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        directories = [
            'static/js',
            'static/css',
            'static/images',
        ]
        
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)
                self.stdout.write(f'创建目录: {directory}')
    
    def _download_marked(self):
        """下载marked.min.js文件"""
        url = 'https://cdn.jsdelivr.net/npm/marked@15.0.7/marked.min.js'
        target_path = 'static/js/marked.min.js'
        
        if os.path.exists(target_path):
            # 检查文件大小，如果太小可能是不完整的
            if os.path.getsize(target_path) < 1000:
                self.stdout.write(f'发现不完整的marked.min.js文件，重新下载...')
                os.remove(target_path)
            else:
                self.stdout.write(self.style.SUCCESS(f'marked.min.js文件已存在，跳过下载'))
                return
        
        try:
            self.stdout.write(f'正在下载 {url}...')
            
            # 尝试使用urllib下载
            try:
                with urllib.request.urlopen(url) as response, open(target_path, 'wb') as out_file:
                    shutil.copyfileobj(response, out_file)
                    self.stdout.write(self.style.SUCCESS(f'成功下载 marked.min.js 到 {target_path}'))
                    return
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'使用urllib下载失败: {str(e)}'))
            
            # 尝试使用Python的requests库
            try:
                import requests
                response = requests.get(url)
                with open(target_path, 'wb') as f:
                    f.write(response.content)
                self.stdout.write(self.style.SUCCESS(f'使用requests成功下载 marked.min.js 到 {target_path}'))
                return
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'使用requests下载失败: {str(e)}'))
            
            # 尝试使用curl命令
            try:
                subprocess.run(['curl', url, '--output', target_path], check=True)
                self.stdout.write(self.style.SUCCESS(f'使用curl成功下载 marked.min.js 到 {target_path}'))
                return
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'使用curl下载失败: {str(e)}'))
            
            # 尝试使用wget命令
            try:
                subprocess.run(['wget', url, '-O', target_path], check=True)
                self.stdout.write(self.style.SUCCESS(f'使用wget成功下载 marked.min.js 到 {target_path}'))
                return
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'使用wget下载失败: {str(e)}'))
            
            self.stdout.write(self.style.ERROR(f'所有下载方法均失败，请手动下载 {url} 到 {target_path}'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'下载 marked.min.js 时出错: {str(e)}'))
            
    def _download_additional_resources(self):
        """下载其他可能需要的资源"""
        # 可以在这里添加其他资源的下载逻辑
        pass 