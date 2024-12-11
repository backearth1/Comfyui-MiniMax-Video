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
        print("初始化 MiniMaxPreviewVideo 节点")
        pass
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_url": ("STRING", {"forceInput": True}),
            }
        }
    
    OUTPUT_NODE = True
    FUNCTION = "run"
    CATEGORY = "minimax"
    RETURN_TYPES = ()
    
    def run(self, video_url):
        return {"ui": {"video_url": [video_url]}}

class MiniMaxAIAPIClient:
    def __init__(self):
        self.api_url = "https://api.minimax.chat/v1"
    
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
            "api_key": ("STRING", {
                "default": "", 
                "multiline": True,
                "display": "API Key"
            }),
            "api_url": (["https://api.minimax.chat/v1", "https://api.minimaxi.chat/v1"], {
                "default": "https://api.minimax.chat/v1"
            }),
        }}
    
    RETURN_TYPES = ("API_KEY", "API_URL",)
    RETURN_NAMES = ("api_key", "api_url",)
    FUNCTION = "setup_client"
    CATEGORY = "minimax"
    
    def setup_client(self, api_key, api_url):
        if not api_key.strip():
            raise ValueError("API key 不能为空")
        return (api_key, api_url,)

class MiniMaxImage2Video:
    def __init__(self):
        self.output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'output')
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "api_key": ("API_KEY",),
                "api_url": ("API_URL",),
                "model": (["video-01", "video-01-live2d"],),
                "prompt": ("STRING", {
                    "default": "", 
                    "multiline": True,
                    "display": "Prompt"
                }),
                "prompt_optimizer": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "first_frame_image": ("IMAGE",),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("video_url",)
    OUTPUT_NODE = True
    FUNCTION = "generate_video"
    CATEGORY = "minimax"
    
    @classmethod
    def IS_CHANGED(s):
        return float("NaN")  # 确保节点每次都会执行
    
    def encode_image(self, image_tensor):
        print("输入图像形状:", image_tensor.shape)
        print("输入图像类型:", image_tensor.dtype)
        
        # 将 tensor 转换为 PIL Image
        if isinstance(image_tensor, torch.Tensor):
            if len(image_tensor.shape) == 4:
                image_tensor = image_tensor[0]  # 移除批次维度
            
            # 确保数值在 0-1 之间
            if image_tensor.max() > 1.0:
                image_tensor = image_tensor / 255.0
            
            # 转换为 numpy 数组
            image_np = (image_tensor.cpu().numpy() * 255).astype(np.uint8)
            
            # 已经是 (H, W, C) 格式，不需要转置
            
            # 创建 PIL 图像
            image = Image.fromarray(image_np, 'RGB')
            print(f"处理后的图像尺寸: {image.size}")
        else:
            raise ValueError("输入必须是 torch.Tensor 类型")
        
        # 转换为 base64
        buffered = io.BytesIO()
        image.save(buffered, format="PNG", quality=95)  # 使用高质量设置
        return base64.b64encode(buffered.getvalue()).decode('utf-8')

    def invoke_video_generation(self, api_key, api_url, prompt, model, base64_image=None):
        print("-----------------提交视频生成任务-----------------")
        url = f"{api_url}/video_generation"
        
        # 构建基本 payload
        payload = {
            "prompt": prompt,
            "model": model,
            "prompt_optimizer": self.prompt_optimizer,
        }
        
        # 如果有图像，则添加到 payload
        if base64_image is not None:
            payload["first_frame_image"] = f"data:image/png;base64,{base64_image}"
        
        headers = {
            'authorization': f'Bearer {api_key}',
            'content-type': 'application/json',
        }
        
        # 添加 SSL 验证选项
        session = requests.Session()
        session.verify = False  # 禁用 SSL 验证
        
        # 忽略 SSL 警告
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        try:
            response = session.post(url, headers=headers, data=json.dumps(payload))
            response_json = response.json()
            print("API Response:", response.text)
            
            # 保存 trace_id 为类属性，以便后续使用
            self.trace_id = response.headers.get('Trace-ID', '')
            print("Trace-ID:", self.trace_id)
            
            if not response_json.get('task_id'):
                error_msg = response_json.get('base_resp', {}).get('status_msg', '未知错误')
                raise Exception(f"API 调用失败: {error_msg}")
            
            task_id = response_json['task_id']
            print("视频生成任务提交成功，任务ID：" + task_id)
            return task_id
        except requests.exceptions.RequestException as e:
            print(f"API 请求失败: {str(e)}")
            raise Exception(f"API 请求失败: {str(e)}")

    def query_video_generation(self, api_key, api_url, task_id):
        url = f"{api_url}/query/video_generation?task_id={task_id}"
        headers = {
            'authorization': f'Bearer {api_key}'
        }
        
        session = requests.Session()
        session.verify = False
        
        # 设置重试策略
        retry_strategy = urllib3.Retry(
            total=5,  # 总重试次数
            backoff_factor=1,  # 重试间隔
            status_forcelist=[500, 502, 503, 504]  # 需要重试的HTTP状态码
        )
        adapter = requests.adapters.HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        
        try:
            # 设置超时时间
            response = session.get(url, headers=headers, timeout=(5, 30))  # (连接超时, 读取超时)
            result = response.json()
            status = result.get('status')
            
            if status == 'Queueing':
                print("...队列中...")
                return "", status
            elif status == 'Processing':
                print("...生成中...")
                return "", status
            elif status == 'Success':
                return result.get('file_id'), status
            else:
                error_msg = result.get('base_resp', {}).get('status_msg', 'Unknown')
                print(f"查询状态失败: {error_msg}")
                return "", "Failed"
        except requests.exceptions.Timeout:
            print("查询超时，将在下一轮重试")
            return "", "Processing"  # 返回 Processing 状态以继续轮询
        except requests.exceptions.RequestException as e:
            print(f"请求异常: {str(e)}")
            return "", "Processing"  # 返回 Processing 状态以继续轮询

    def fetch_video_result(self, api_key, api_url, file_id, output_path):
        print("---------------视频生成成功，下载中---------------")
        url = f"{api_url}/files/retrieve?file_id={file_id}"
        headers = {
            'authorization': f'Bearer {api_key}',
        }
        
        session = requests.Session()
        session.verify = False
        
        try:
            response = session.get(url, headers=headers, timeout=(5, 30))
            print("获取下载链接响应:", response.text)

            download_url = response.json()['file']['download_url']
            print("视频下载链接：" + download_url)
            
            # 确保使用完整路径
            full_output_path = os.path.join(self.output_dir, output_path)
            
            # 下载视频
            video_response = session.get(download_url, timeout=(5, 60))
            if video_response.status_code == 200:
                with open(full_output_path, 'wb') as f:
                    f.write(video_response.content)
                print(f"视频已保存到：{full_output_path}")
                return full_output_path
            else:
                print(f"下载失败，状态码：{video_response.status_code}")
                print(f"错误信息：{video_response.text}")
                raise Exception("视频下载失败")
        except Exception as e:
            print(f"下载失败: {str(e)}")
            raise

    def generate_video(self, api_key, api_url, model, prompt, prompt_optimizer, first_frame_image=None):
        try:
            self.prompt_optimizer = prompt_optimizer
            
            # 生成新的文件名格式：MM{时间}_{trace_id}.mp4
            current_time = time.strftime("%m%d%H%M")
            
            # 初始化输出路径（此时还没有 trace_id）
            self.output_path = f"MM{current_time}"
            
            print(f"开始生成视频，输出路径将基于: {self.output_path}")
            
            base64_image = None
            if first_frame_image is not None:
                base64_image = self.encode_image(first_frame_image)
            
            task_id = self.invoke_video_generation(api_key, api_url, prompt, model, base64_image)
            
            # 更新完整的输出路径（现在有了 trace_id）
            self.output_path = f"MM{current_time}_{self.trace_id}.mp4"
            print(f"更新后的输出路径: {os.path.join(self.output_dir, self.output_path)}")
            
            progress_count = 0
            while True:
                file_id, status = self.query_video_generation(api_key, api_url, task_id)
                
                if status == "Success" and file_id:
                    video_url = self.get_video_url(api_key, api_url, file_id)
                    video_path = self.fetch_video_result(api_key, api_url, file_id, self.output_path)
                    print("---------------生成成功---------------")
                    print(f"视频已保存到: {video_path}")
                    print(f"视频URL: {video_url}")
                    
                    return {
                        "ui": {"video_url": [video_url]},
                        "result": (video_url,)
                    }
                elif status in ["Fail", "Unknown"]:
                    print("---------------生成失败---------------")
                    raise Exception(f"视频生成失败: {status}")
                
                progress_count += 1
                if status == "Queueing":
                    progress_msg = f"排队中... ({progress_count * 20}秒)"
                else:
                    progress_msg = f"生成中... ({progress_count * 20}秒)"
                
                print(progress_msg)
                time.sleep(20)
                
        except Exception as e:
            print(f"发生错误: {str(e)}")
            raise e

    def get_video_url(self, api_key, api_url, file_id):
        """获取视频下载链接"""
        url = f"{api_url}/files/retrieve?file_id={file_id}"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        response = requests.get(url, headers=headers)
        result = response.json()
        return result['file']['download_url']

# 导出节点映射
NODE_CLASS_MAPPINGS = {
    "MiniMaxPreviewVideo": MiniMaxPreviewVideo,
    "MiniMaxAIAPIClient": MiniMaxAIAPIClient,
    "MiniMaxImage2Video": MiniMaxImage2Video,
}

# 导出节点显示名称映射
NODE_DISPLAY_NAME_MAPPINGS = {
    "MiniMaxPreviewVideo": "MiniMax Preview Video",
    "MiniMaxAIAPIClient": "MiniMax API Client",
    "MiniMaxImage2Video": "MiniMax Image to Video",
}