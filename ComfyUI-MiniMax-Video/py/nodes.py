import torch
import numpy as np
import requests
import json
import base64
import time
from PIL import Image
import io
import os
import urllib3

class MiniMaxPreviewVideo:
    def __init__(self):
        self.video_urls = []
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "video_url": ("STRING", {"forceInput": True}),
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "preview"
    CATEGORY = "minimax"
    OUTPUT_NODE = True

    def preview(self, video_url):
        print("\n=== MiniMaxPreviewVideo 节点执行 ===")
        print(f"接收到视频URL:\n{video_url}")
        
        # 处理输入的视频URL
        if isinstance(video_url, (list, tuple)):
            urls = list(video_url)
        else:
            try:
                urls = json.loads(video_url) if isinstance(video_url, str) else [video_url]
            except:
                urls = [video_url]
        
        print(f"处理后的视频URLs: {urls}")
        
        # 更新视频URL列表
        self.video_urls = urls
        
        # 返回UI更新信息
        return {"ui": {"video_url": urls}}

class MiniMaxAIAPIClient:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {}}
    
    RETURN_TYPES = ("API_KEY", "API_URL",)
    FUNCTION = "get_api_key"
    CATEGORY = "minimax"

    def get_api_key(self):
        print("\n=== MiniMaxAIAPIClient 节点执行 ===")
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.ini')
        print(f"配置文件路径: {config_path}")
        
        api_key = ""
        api_url = "https://api.minimax.chat/v1"
        
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('MINIMAXAI_API_KEY'):
                        api_key = line.split('=')[1].strip()
                        break
        
        print(f"API Key: {api_key}")
        print(f"API URL: {api_url}")
        return (api_key, api_url,)

class MiniMaxImage2Video:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "api_key": ("API_KEY",),
                "api_url": ("API_URL",),
                "first_frame_image": ("IMAGE",),
                "model": ("STRING", {"default": "video-01-live2d"}),
                "prompt": ("STRING", {"default": "the model take a catwalk"}),
                "watermark": ("BOOLEAN", {"default": True}),
                "enhance": (["no", "yes"],),
                "num_frames": ("INT", {"default": 4, "min": 4, "max": 32, "step": 1}),
            },
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "generate_video"
    CATEGORY = "minimax"

    def generate_video(self, api_key, api_url, first_frame_image, model, prompt, watermark=True, enhance="no", num_frames=4):
        print("\n=== MiniMaxImage2Video 节点执行 ===")
        print(f"接收到的参数：\nAPI Key: {api_key}\nAPI URL: {api_url}\nModel: {model}\nPrompt: {prompt}\nWatermark: {watermark}\nEnhance: {enhance}\nNum Frames: {num_frames}")
        
        # 将 PIL 图像转换为 base64
        first_frame_image = first_frame_image[0] if isinstance(first_frame_image, list) else first_frame_image
        if isinstance(first_frame_image, torch.Tensor):
            first_frame_image = 255. * first_frame_image.cpu().numpy()
            first_frame_image = Image.fromarray(np.clip(first_frame_image, 0, 255).astype(np.uint8))
        
        # 转换图像为 base64
        buffered = io.BytesIO()
        first_frame_image.save(buffered, format="PNG")
        image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "prompt": prompt,
            "image": image_base64,
            "watermark": watermark,
            "enhance": enhance == "yes",
            "num_frames": num_frames
        }
        
        try:
            response = requests.post(f"{api_url}/v1/text_to_video", headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            if "video_url" in result:
                video_url = result["video_url"]
                print(f"生成的视频URL: {video_url}")
                return (video_url,)
            else:
                print("API 返回中没有找到 video_url")
                return ("API 返回中没有找到 video_url",)
                
        except Exception as e:
            print(f"API 调用错误: {str(e)}")
            return ("API调用失败，请检查配置和网络连接",)

class MiniMaxImage2Prompt:
    def __init__(self):
        self.default_prompt = """用户提交的图片是一段广告展示视频的第一帧，请基于图片信息用英语描述接下来的视频
请采用以下描述方式
The video starts with a close-up of 主体商品的描述.As the video progresses, the camera performs a half-circle shot around the 商品名称, maintaining a steady focus on it. 商品名称remains completely still，产品环放置的境, shifts subtly to reflect the camera's movement. The overall scene is well-lit, emphasizing the colors and details of the 商品名称. The camera movement is smooth, providing a comprehensive view of the 商品名称 from different angles, while the 商品名称 itself stays motionless throughout the video.
比如一个完整的描述如下：
The video starts with a close-up of a colorful tote bag with the word 'GENTLEWOMAN' printed repeatedly on its handles. The bag is placed on a white desk, next to a book. As the video progresses, the camera performs a half-circle shot around the bag, maintaining a steady focus on it. The bag remains completely still on the desk, while the background, which includes a white wall and a framed picture with partially visible text, shifts subtly to reflect the camera's movement. The overall scene is well-lit, emphasizing the colors and details of the bag. The camera movement is smooth, providing a comprehensive view of the bag from different angles, while the bag itself stays motionless throughout the video."""

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "api_key": ("API_KEY",),
                "api_url": ("API_URL",),
                "model": (["MiniMax-Text-01", "abab7-chat-preview", "abab6.5s-chat"],),
                "VLM_prompt": ("STRING", {
                    "default": """用户提交的图片是一段广告展示视频的第一帧，请基于图片信息用英语描述接下来的视频
请采用以下描述方式
The video starts with a close-up of 主体商品的描述.As the video progresses, the camera performs a half-circle shot around the 商品名称, maintaining a steady focus on it. 商品名称remains completely still，产品环放置的境, shifts subtly to reflect the camera's movement. The overall scene is well-lit, emphasizing the colors and details of the 商品名称. The camera movement is smooth, providing a comprehensive view of the 商品名称 from different angles, while the 商品名称 itself stays motionless throughout the video.
比如一个完整的描述如下：
The video starts with a close-up of a colorful tote bag with the word 'GENTLEWOMAN' printed repeatedly on its handles. The bag is placed on a white desk, next to a book. As the video progresses, the camera performs a half-circle shot around the bag, maintaining a steady focus on it. The bag remains completely still on the desk, while the background, which includes a white wall and a framed picture with partially visible text, shifts subtly to reflect the camera's movement. The overall scene is well-lit, emphasizing the colors and details of the bag. The camera movement is smooth, providing a comprehensive view of the bag from different angles, while the bag itself stays motionless throughout the video.""", 
                    "multiline": True
                }),
                "temperature": ("FLOAT", {"default": 0.1, "min": 0.0, "max": 1.0, "step": 0.1}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "generate_prompt"
    CATEGORY = "minimax"

    def generate_prompt(self, image, api_key, api_url, model, VLM_prompt="", temperature=0.1):
        print("\n=== MiniMaxImage2Prompt 节点执行 ===")
        print(f"使用模型: {model}")
        print(f"API URL: {api_url}")
        
        # 使用用户输入的文本或默认文本
        prompt_text = VLM_prompt if VLM_prompt.strip() else self.default_prompt
        
        # 修复图像处理部分
        if isinstance(image, torch.Tensor):
            # 确保图像是正确的形状
            if len(image.shape) == 4:
                image = image[0]  # 移除批次维度
            elif len(image.shape) == 3:
                if image.shape[0] in [1, 3, 4]:  # 如果通道在前
                    image = image.permute(1, 2, 0)  # 将通道移到最后
            
            # 转换为 numpy 数组并确保值在 0-255 范围内
            image = image.cpu().numpy()
            if image.max() <= 1.0:
                image = (image * 255).astype(np.uint8)
            else:
                image = image.astype(np.uint8)
            
            # 如果是单通道，转换为 RGB
            if len(image.shape) == 2 or (len(image.shape) == 3 and image.shape[-1] == 1):
                image = np.stack([image] * 3, axis=-1)
            
            # 确保是 RGB 格式
            if image.shape[-1] == 4:  # RGBA
                image = image[..., :3]  # 只保留 RGB 通道
        
        # 转换为 PIL Image
        try:
            pil_image = Image.fromarray(image)
        except Exception as e:
            print(f"图像转换错误: {str(e)}")
            print(f"图像形状: {image.shape}")
            print(f"图像类型: {image.dtype}")
            raise
        
        # 转换为 base64
        buffered = io.BytesIO()
        pil_image.save(buffered, format="PNG")
        base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        payload = {
            "model": model,
            "temperature": temperature,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt_text
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 300
        }

        try:
            response = requests.post(f"{api_url}/chat/completions", 
                                  headers=headers, 
                                  json=payload)
            response.raise_for_status()
            result = response.json()
            
            # 提取返回的文本内容
            generated_prompt = result['choices'][0]['message']['content']
            print(f"生成的 prompt: {generated_prompt}")
            
            return (generated_prompt,)
            
        except Exception as e:
            print(f"API 调用错误: {str(e)}")
            print(f"请求 URL: {api_url}/chat/completions")
            print(f"请求头: {headers}")
            return ("API调用失败，请检查配置和网络连接",)

NODE_CLASS_MAPPINGS = {
    "MiniMaxPreviewVideo": MiniMaxPreviewVideo,
    "MiniMaxAIAPIClient": MiniMaxAIAPIClient,
    "MiniMaxImage2Video": MiniMaxImage2Video,
    "MiniMaxImage2Prompt": MiniMaxImage2Prompt,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MiniMaxPreviewVideo": "MiniMax Preview Video",
    "MiniMaxAIAPIClient": "MiniMax API Client",
    "MiniMaxImage2Video": "MiniMax Image to Video",
    "MiniMaxImage2Prompt": "MiniMax Image to Prompt",
}