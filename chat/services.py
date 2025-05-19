import json
import requests
from django.conf import settings
from typing import List, Dict, Any, Optional
import logging
from chat.models import ServiceProvider, AIModel

# 获取chat应用的日志记录器
logger = logging.getLogger('chat')

class ChatAPIService:
    """处理与外部聊天API的交互"""
    
    def __init__(self, service_provider=None, model_instance=None):
        """
        初始化聊天API服务
        
        Args:
            service_provider: 指定的服务商配置，如果为None则使用默认配置
            model_instance: AI模型实例，如果提供则从其关联的服务商获取配置
        """
        # 设置是否使用自定义端点的标志
        self.using_custom_endpoint = False
        
        # 如果提供了模型实例，优先使用其关联的服务商
        if model_instance and hasattr(model_instance, 'provider') and model_instance.provider:
            self.service_provider = model_instance.provider
            # 检查模型是否有自定义API端点
            if hasattr(model_instance, 'api_endpoint') and model_instance.api_endpoint:
                self.base_url = model_instance.api_endpoint
                self.using_custom_endpoint = True
            else:
                self.base_url = model_instance.provider.api_base
        elif service_provider:
            self.service_provider = service_provider
            self.base_url = service_provider.api_base
        else:
            # 尝试从数据库中获取默认服务商配置
            try:
                self.service_provider = ServiceProvider.objects.filter(is_active=True).first()
            except Exception:
                # 如果数据库查询出错或未找到，使用settings中的默认配置
                self.service_provider = None
                
        # 如果找到了数据库中的服务商配置，使用它
        if self.service_provider and not hasattr(self, 'base_url'):
            self.base_url = self.service_provider.api_base
            self.api_token = self.service_provider.api_key
            self.auth_method = 'bearer'  # 默认使用bearer认证
            self.auth_key_name = None
        else:
            # 如果没有找到服务商配置或已经设置了base_url，只需要设置API token和认证方式
            if self.service_provider:
                self.api_token = self.service_provider.api_key
                self.auth_method = 'bearer'  # 默认使用bearer认证
                self.auth_key_name = None
            else:
                # 使用settings中的默认配置
                self.base_url = settings.API_BASE_URL
                self.using_custom_endpoint = False
                self.api_token = settings.API_TOKEN
                self.auth_method = 'bearer'  # 默认使用bearer认证
                self.auth_key_name = None
                
        # 设置各种API路径
        self.chat_path = "v1/chat/completions"
        self.image_path = "v1/images/generations"
        self.embedding_path = "v1/embeddings"
        self.audio_path = "v1/audio/transcriptions"
    
    @classmethod
    def get_service_for_model(cls, model_id: str) -> 'ChatAPIService':
        """
        根据模型ID获取对应的ChatAPIService实例
        
        API端点优先级：
        1. 模型自定义API端点(api_endpoint)
        2. 服务商的API基础URL(api_base)
        3. settings中的默认配置
        
        Args:
            model_id: 模型ID
            
        Returns:
            ChatAPIService: 服务实例
        """
        try:
            # 查找模型并获取其关联的服务商
            model_instance = AIModel.objects.get(model_id=model_id, is_active=True)
            
            # 使用模型实例创建服务，自动处理自定义API端点优先级
            return cls(model_instance=model_instance)
            
        except AIModel.DoesNotExist:
            # 模型不存在，使用默认服务
            return cls()
    
    @staticmethod
    def get_model_type(model_id: str) -> str:
        """
        根据模型ID确定模型类型
        
        Args:
            model_id: 模型ID
            
        Returns:
            str: 模型类型 - 'chat', 'image', 'embedding', 'audio'等
        """
        model_id = model_id.lower()
        
        # 图像生成模型特征
        if any(x in model_id for x in ['dall-e', 'dalle', 'midjourney', 'stable-diffusion', 'gpt-image']):
            return 'image'
            
        # 音频转文本模型特征
        if any(x in model_id for x in ['whisper', 'audio', 'voice', 'speech']):
            return 'audio'
            
        # 嵌入向量模型特征
        if any(x in model_id for x in ['embedding', 'text-embedding', 'vector']):
            return 'embedding'
            
        # 默认为聊天模型
        return 'chat'
    
    def process_request(self, model_id: str, messages: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """
        根据模型类型处理请求并调用相应的API
        
        Args:
            model_id: 模型ID
            messages: 消息内容，每个消息包含角色和内容（内容可以是字符串或包含text和image_url的数组）
            **kwargs: 其他参数
            
        Returns:
            Dict[str, Any]: API响应
        """
        model_type = self.get_model_type(model_id)
        
        # 根据模型类型选择合适的API调用方法
        if model_type == 'image':
            # 从messages中提取用户的最后一条消息作为图像生成提示
            user_prompts = [msg['content'] for msg in messages if msg.get('role') == 'user']
            prompt = user_prompts[-1] if user_prompts else ""
            
            # 对于包含数组格式内容的消息，提取文本部分
            if isinstance(prompt, list):
                text_parts = []
                for item in prompt:
                    if isinstance(item, dict) and item.get('type') == 'text':
                        text_parts.append(item.get('text', ''))
                prompt = ' '.join(text_parts)
            
            # 提取图像生成相关参数
            image_model = kwargs.get('image_model', 'dall-e-3')
            size = kwargs.get('size', '1024x1024')
            quality = kwargs.get('quality', 'standard')
            n = kwargs.get('n', 1)
            
            return self.image_generation(
                prompt=prompt, 
                model=image_model,
                size=size,
                quality=quality,
                n=n
            )
        elif model_type == 'audio':
            # 这里可以添加音频模型的调用逻辑
            pass
        elif model_type == 'embedding':
            # 这里可以添加embedding模型的调用逻辑
            pass
        else:
            # 默认使用聊天完成API
            stream = kwargs.get('stream', False)
            temperature = kwargs.get('temperature', 0.7)
            max_tokens = kwargs.get('max_tokens', 1500)
            top_p = kwargs.get('top_p', 1.0)
            presence_penalty = kwargs.get('presence_penalty', 0.0)
            frequency_penalty = kwargs.get('frequency_penalty', 0.0)
            
            return self.chat_completion(
                messages=messages,
                model=model_id,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                presence_penalty=presence_penalty,
                frequency_penalty=frequency_penalty,
                stream=stream
            )
    
    def _prepare_headers(self):
        """
        根据认证方式准备请求头
        
        Returns:
            Dict[str, str]: 请求头字典
        """
        headers = {
            "Content-Type": "application/json"
        }
        
        if self.auth_method == 'bearer':
            headers["Authorization"] = f"Bearer {self.api_token}"
        elif self.auth_method == 'header' and self.auth_key_name:
            headers[self.auth_key_name] = self.api_token
            
        return headers
    
    def _prepare_url(self, endpoint=None):
        """准备API URL"""
        if endpoint is None:
            endpoint = self.chat_path
            
        # 检查endpoint是否已经是完整URL
        if endpoint.startswith(('http://', 'https://')):
            url = endpoint
        else:
            # 确保base_url以/结尾，endpoint不以/开头
            base_url = self.base_url.rstrip('/')
            endpoint = endpoint.lstrip('/')
            url = f"{base_url}/{endpoint}"
            
        # 调试信息
        logger.debug(f"构建的API URL: {url}")
        return url
        
    def chat_completion(self, messages: List[Dict[str, Any]], 
                        model: str = "gpt-4o", 
                        temperature: float = 0.7,
                        max_tokens: int = 1500,
                        top_p: float = 1.0,
                        presence_penalty: float = 0.0,
                        frequency_penalty: float = 0.0,
                        stream: bool = False) -> Dict[str, Any]:
        """
        调用聊天完成API
        
        Args:
            messages: 消息列表，每个消息包含角色和内容（内容可以是字符串或包含text和image_url的数组）
            model: 使用的模型名称
            temperature: 采样温度，控制随机性
            max_tokens: 生成的最大token数量
            top_p: 核采样概率
            presence_penalty: 存在惩罚
            frequency_penalty: 频率惩罚
            stream: 是否流式输出
            
        Returns:
            API响应的字典
        """
        headers = self._prepare_headers()
        url = self._prepare_url(self.chat_path)
        
        # 检查URL是否是图片URL，如果是则返回错误
        if url.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
            error_message = f"尝试向图片URL发送API请求: {url}"
            logger.error(error_message)
            return {"error": error_message}
            
        # 也检查是否是文件系统URL
        if 'filesystem.site/cdn/' in url:
            error_message = f"尝试向CDN URL发送API请求: {url}"
            logger.error(error_message)
            return {"error": error_message}
        
        # 预处理消息，确保它们符合图片分析API的格式要求
        processed_messages = []
        for message in messages:
            message_copy = message.copy()
            content = message_copy.get('content')
            
            # 如果内容是字符串，需要检查是否包含图片标记并处理
            if isinstance(content, str):
                # 检查内容是否包含markdown图片链接 ![...](...)
                if '![' in content and '](' in content:
                    # 创建内容数组格式
                    content_array = []
                    try:
                        # 尝试提取图片URL和文本说明
                        parts = content.split('![')
                        text_part = parts[0].strip()
                        
                        if text_part:
                            content_array.append({"type": "text", "text": text_part})
                        
                        # 处理图片部分
                        for i in range(1, len(parts)):
                            img_part = parts[i]
                            if '](' in img_part and ')' in img_part:
                                img_description = img_part.split('](')[0].strip()
                                img_url = img_part.split('](')[1].split(')')[0].strip()
                                
                                # 检查图片URL是否有效
                                if img_url.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')) or 'filesystem.site/cdn/' in img_url:
                                    # 不要尝试向图片URL发送API请求
                                    if img_url == url:
                                        error_message = f"尝试向图片URL发送API请求: {img_url}"
                                        logger.error(error_message)
                                        return {"error": error_message}
                                    
                                    # 添加图片URL到内容数组
                                    content_array.append({
                                        "type": "image_url", 
                                        "image_url": {
                                            "url": img_url,
                                            "detail": "auto"  # 添加detail参数，自动决定分析详细程度
                                        }
                                    })
                        
                        # 如果处理成功，使用新的内容数组替换原始内容
                        if content_array:
                            message_copy['content'] = content_array
                            logger.info(f"从Markdown提取的图片内容数组: {json.dumps(content_array, ensure_ascii=False)}")
                    except Exception as e:
                        logger.error(f"处理图片URL时出错: {str(e)}")
                        # 如果解析失败，保持原始内容
            
            # 处理已经是列表格式的内容（可能包含图片）
            elif isinstance(content, list):
                content_array = []
                for item in content:
                    if isinstance(item, dict):
                        # 已经是字典格式，检查是否需要调整
                        if item.get('type') == 'image_url':
                            # 确保image_url是正确格式
                            image_url = item.get('image_url')
                            if isinstance(image_url, str):
                                # 检查图片URL与API URL是否相同
                                if image_url == url:
                                    error_message = f"尝试向图片URL发送API请求: {image_url}"
                                    logger.error(error_message)
                                    return {"error": error_message}
                                item = {
                                    "type": "image_url", 
                                    "image_url": {
                                        "url": image_url,
                                        "detail": "auto"  # 添加detail参数，使用auto自动决定分析详细程度
                                    }
                                }
                            elif isinstance(image_url, dict) and 'url' in image_url:
                                # 检查URL与API URL是否相同
                                if image_url['url'] == url:
                                    error_message = f"尝试向图片URL发送API请求: {image_url['url']}"
                                    logger.error(error_message)
                                    return {"error": error_message}
                                
                                # 添加detail参数（如果不存在）
                                if 'detail' not in image_url:
                                    image_url['detail'] = 'auto'
                                    item['image_url'] = image_url
                            logger.info(f"处理图片URL后的结构: {json.dumps(item, ensure_ascii=False)}")
                        content_array.append(item)
                    elif isinstance(item, str):
                        # 文本项
                        content_array.append({"type": "text", "text": item})
                
                message_copy['content'] = content_array
                logger.info(f"处理后的图片内容数组: {json.dumps(content_array, ensure_ascii=False)}")
            
            processed_messages.append(message_copy)
        
        payload = {
            "model": model,
            "messages": processed_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "presence_penalty": presence_penalty,
            "frequency_penalty": frequency_penalty,
            "stream": stream
        }
        
        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=60  # 设置超时时间为60秒
            )
            
            response.raise_for_status()  # 如果请求失败，抛出异常
            return response.json()
        
        except requests.exceptions.RequestException as e:
            # 处理请求异常
            error_message = f"API请求失败: {str(e)}"
            logger.error(error_message)
            return {"error": error_message}
        
        except json.JSONDecodeError:
            # 处理JSON解析异常
            return {"error": "解析API响应时出错"}
        
    def stream_chat_completion(self, messages: List[Dict[str, Any]], 
                           model: str = "gpt-4o", 
                           temperature: float = 0.7,
                           max_tokens: int = 1500,
                           top_p: float = 1.0,
                           presence_penalty: float = 0.0,
                           frequency_penalty: float = 0.0):
        """
        流式调用聊天完成API，用于生成器函数
        
        Args:
            messages: 消息列表，每个消息包含角色和内容（内容可以是字符串或包含text和image_url的数组）
            model: 使用的模型名称
            temperature: 采样温度
            max_tokens: 生成的最大token数量
            top_p: 核采样概率
            presence_penalty: 存在惩罚
            frequency_penalty: 频率惩罚
            
        Yields:
            流式响应的每个部分
        """
        # 检查模型类型，确保它是聊天模型而非图像模型
        model_type = self.get_model_type(model)
        if model_type != 'chat':
            error_message = f"不支持对{model_type}类型模型进行流式响应"
            logger.error(error_message)
            yield {"error": error_message}
            return
            
        headers = self._prepare_headers()
        url = self._prepare_url(self.chat_path)
        
        # 检查URL是否是图片URL，如果是则返回错误
        if url.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
            error_message = f"尝试向图片URL发送流式API请求: {url}"
            logger.error(error_message)
            yield {"error": error_message}
            return
            
        # 也检查是否是文件系统URL
        if 'filesystem.site/cdn/' in url:
            error_message = f"尝试向CDN URL发送流式API请求: {url}"
            logger.error(error_message)
            yield {"error": error_message}
            return
        
        # 调试信息
        logger.debug(f"流式聊天请求URL: {url}")
        
        # 预处理消息，确保它们符合图片分析API的格式要求
        processed_messages = []
        for message in messages:
            message_copy = message.copy()
            content = message_copy.get('content')
            
            # 如果内容是字符串，需要检查是否包含图片标记并处理
            if isinstance(content, str):
                # 检查内容是否包含markdown图片链接 ![...](...)
                if '![' in content and '](' in content:
                    # 创建内容数组格式
                    content_array = []
                    try:
                        # 尝试提取图片URL和文本说明
                        parts = content.split('![')
                        text_part = parts[0].strip()
                        
                        if text_part:
                            content_array.append({"type": "text", "text": text_part})
                        
                        # 处理图片部分
                        for i in range(1, len(parts)):
                            img_part = parts[i]
                            if '](' in img_part and ')' in img_part:
                                img_description = img_part.split('](')[0].strip()
                                img_url = img_part.split('](')[1].split(')')[0].strip()
                                
                                # 检查图片URL是否有效
                                if img_url.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')) or 'filesystem.site/cdn/' in img_url:
                                    # 不要尝试向图片URL发送API请求
                                    if img_url == url:
                                        error_message = f"尝试向图片URL发送流式API请求: {img_url}"
                                        logger.error(error_message)
                                        yield {"error": error_message}
                                        return
                                    
                                    # 添加图片URL到内容数组
                                    content_array.append({
                                        "type": "image_url", 
                                        "image_url": {
                                            "url": img_url,
                                            "detail": "auto"  # 添加detail参数，自动决定分析详细程度
                                        }
                                    })
                        
                        # 如果处理成功，使用新的内容数组替换原始内容
                        if content_array:
                            message_copy['content'] = content_array
                            logger.info(f"从Markdown提取的图片内容数组: {json.dumps(content_array, ensure_ascii=False)}")
                    except Exception as e:
                        logger.error(f"处理图片URL时出错: {str(e)}")
                        # 如果解析失败，保持原始内容
            
            # 处理已经是列表格式的内容（可能包含图片）
            elif isinstance(content, list):
                content_array = []
                for item in content:
                    if isinstance(item, dict):
                        # 已经是字典格式，检查是否需要调整
                        if item.get('type') == 'image_url':
                            # 确保image_url是正确格式
                            image_url = item.get('image_url')
                            if isinstance(image_url, str):
                                # 检查图片URL与API URL是否相同
                                if image_url == url:
                                    error_message = f"尝试向图片URL发送流式API请求: {image_url}"
                                    logger.error(error_message)
                                    yield {"error": error_message}
                                    return
                                item = {
                                    "type": "image_url", 
                                    "image_url": {
                                        "url": image_url,
                                        "detail": "auto"  # 添加detail参数，使用auto自动决定分析详细程度
                                    }
                                }
                            elif isinstance(image_url, dict) and 'url' in image_url:
                                # 检查URL与API URL是否相同
                                if image_url['url'] == url:
                                    error_message = f"尝试向图片URL发送流式API请求: {image_url['url']}"
                                    logger.error(error_message)
                                    yield {"error": error_message}
                                    return
                                
                                # 添加detail参数（如果不存在）
                                if 'detail' not in image_url:
                                    image_url['detail'] = 'auto'
                                    item['image_url'] = image_url
                            logger.info(f"处理图片URL后的结构: {json.dumps(item, ensure_ascii=False)}")
                        content_array.append(item)
                    elif isinstance(item, str):
                        # 文本项
                        content_array.append({"type": "text", "text": item})
                
                message_copy['content'] = content_array
                logger.info(f"处理后的图片内容数组: {json.dumps(content_array, ensure_ascii=False)}")
            
            processed_messages.append(message_copy)
        
        payload = {
            "model": model,
            "messages": processed_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "presence_penalty": presence_penalty,
            "frequency_penalty": frequency_penalty,
            "stream": True
        }
        
        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                stream=True,
                timeout=120  # 增加流式请求的超时时间
            )
            
            response.raise_for_status()
            
            # 用于累积DeepSeek推理内容
            reasoning_content = ""
            
            for line in response.iter_lines():
                if not line:
                    continue
                    
                line = line.decode('utf-8')
                if not line.startswith('data: '):
                    continue
                    
                data = line[6:]
                if data == '[DONE]':
                    break
                    
                try:
                    chunk = json.loads(data)
                    
                    # 处理DeepSeek Reasoner模型的特殊格式
                    if 'choices' in chunk and len(chunk['choices']) > 0:
                        choice = chunk['choices'][0]
                        if 'delta' in choice:
                            delta = choice['delta']
                            
                            # 检查是否有推理内容（DeepSeek Reasoner特有）
                            if 'reasoning_content' in delta and delta['reasoning_content'] is not None:
                                reasoning_content += delta['reasoning_content']
                                
                                # 创建一个包含推理内容的临时chunk
                                reasoning_chunk = {
                                    'choices': [{
                                        'message': {
                                            'reasoning': reasoning_content
                                        }
                                    }]
                                }
                                yield reasoning_chunk
                            
                    yield chunk
                except json.JSONDecodeError as e:
                    logger.error(f"JSON解析错误: {str(e)}, 数据: {data}")
                    continue
                    
        except requests.exceptions.RequestException as e:
            error_message = f"流式API请求失败: {str(e)}"
            logger.error(error_message)
            yield {"error": error_message}
        except Exception as e:
            error_message = f"流式处理时发生未知错误: {str(e)}"
            logger.error(error_message)
            yield {"error": error_message}
        
    @staticmethod
    def extract_reasoning(response, model_id=None):
        """
        从不同模型的响应中提取推理过程
        
        Args:
            response: API响应
            model_id: 模型ID，用于确定处理方式
            
        Returns:
            提取的推理过程，如果没有则返回None
        """
        if not response:
            return None
        
        # 如果响应不包含choices，检查是否有其他格式
        if 'choices' not in response or not response['choices']:
            # 特殊情况：DeepSeek Reasoner的推理可能直接放在响应根级别
            if 'reasoning' in response:
                return response['reasoning']
            return None
        
        # 获取消息内容
        choice = response['choices'][0]
        message = choice.get('message', {})
        
        # 尝试从不同格式中提取推理
        reasoning = None
        
        # 1. 检查message中是否有reasoning字段（DeepSeek特有）
        if 'reasoning' in message:
            reasoning = message.get('reasoning')
        
        # 2. 查找OpenAI格式的工具调用中的推理
        if not reasoning and 'tool_calls' in message:
            for tool_call in message.get('tool_calls', []):
                if tool_call.get('type') == 'function' and tool_call.get('function', {}).get('name') == 'reasoning':
                    try:
                        arguments = json.loads(tool_call['function'].get('arguments', '{}'))
                        reasoning = arguments.get('reasoning')
                    except:
                        pass
        
        # 3. 查找DeepSeek格式的思考过程
        if not reasoning and 'thinking' in message:
            reasoning = message.get('thinking')
        
        # 4. 检查message的内容是否包含特定格式的推理过程
        content = message.get('content', '')
        if not reasoning and content:
            # 常见的推理标记格式
            reasoning_markers = [
                {'start': '<reasoning>', 'end': '</reasoning>'},
                {'start': '<thinking>', 'end': '</thinking>'},
            ]
            for marker in reasoning_markers:
                if marker['start'] in content and marker['end'] in content:
                    reasoning = content.split(marker['start'])[1].split(marker['end'])[0].strip()
                    break
        
        return reasoning

    def image_generation(self, prompt: str, 
                        model: str = "dall-e-3", 
                        size: str = "1024x1024",
                        quality: str = "standard",
                        n: int = 1) -> Dict[str, Any]:
        """
        调用图像生成API
        
        Args:
            prompt: 图像生成提示词
            model: 使用的模型名称
            size: 图像尺寸，如1024x1024
            quality: 图像质量，standard或hd
            n: 生成图像数量
            
        Returns:
            API响应的字典
        """
        headers = self._prepare_headers()
        
        # 使用图像生成的路径配置
        url = self._prepare_url(self.image_path)
        
        # 调试信息
        logger.debug(f"图像生成请求URL: {url}")
        
        payload = {
            "model": model,
            "prompt": prompt,
            "size": size,
            "quality": quality,
            "n": n
        }
        
        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=60
            )
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            # 处理请求异常，记录更详细的错误信息
            error_message = f"图像生成API请求失败: {str(e)}, URL: {url}"
            logger.error(f"API请求错误: {error_message}")
            return {"error": error_message}
        
        except json.JSONDecodeError:
            # 处理JSON解析异常
            return {"error": "解析API响应时出错"}

    @classmethod
    def test_url_generation(cls, api_base=None, api_endpoint=None, endpoint_type='chat'):
        """
        测试生成API URL的功能
        
        Args:
            api_base: 服务商基础URL
            api_endpoint: 自定义端点URL
            endpoint_type: 端点类型 (chat, image, embedding, audio)
            
        Returns:
            生成的URL字符串
        """
        # 创建ServiceProvider实例
        provider = None
        if api_base:
            provider = type('ServiceProvider', (), {'api_base': api_base, 'api_key': 'test-key'})
            
        # 创建AIModel实例
        model = None
        if api_endpoint:
            # 确保自定义端点优先级高于服务商API基础URL
            model = type('AIModel', (), {
                'api_endpoint': api_endpoint, 
                'provider': provider
            })
        elif provider:
            model = type('AIModel', (), {
                'api_endpoint': None, 
                'provider': provider
            })
            
        # 初始化服务
        service = cls(service_provider=provider, model_instance=model)
        
        # 如果设置了自定义端点，直接返回
        if api_endpoint:
            return api_endpoint
            
        # 根据端点类型选择路径
        if endpoint_type == 'image':
            path = service.image_path
        elif endpoint_type == 'embedding':
            path = service.embedding_path
        elif endpoint_type == 'audio':
            path = service.audio_path
        else:
            path = service.chat_path
            
        # 生成并返回URL
        return service._prepare_url(path)