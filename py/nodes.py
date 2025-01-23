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
        self.video_urls = []
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_url": ("STRING", {"forceInput": True, "multiline": True}),
            }
        }
    
    OUTPUT_NODE = True
    FUNCTION = "run"
    CATEGORY = "minimax"
    RETURN_TYPES = ()
    
    def run(self, video_url):
        print("\n=== MiniMaxPreviewVideo 节点执行 ===")
        # 处理输入的视频URL
        if isinstance(video_url, (list, tuple)):
            urls = list(video_url)
        else:
            # 如果是字符串，尝试解析是否为JSON数组
            try:
                import json
                urls = json.loads(video_url) if isinstance(video_url, str) else [video_url]
            except:
                urls = [video_url]
        
        print(f"接收到 {len(urls)} 个视频URL:")
        for i, url in enumerate(urls):
            print(f"视频 #{i+1}: {url}")
        
        # 更新视频URL列表
        self.video_urls = urls
        
        # 返回UI更新信息
        return {"ui": {"video_url": urls}}

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
                "model": (["video-01", "video-01-live2d", "S2V-01"],),  # 添加 S2V-01 模型
                "prompt": ("STRING", {
                    "default": "", 
                    "multiline": True,
                    "display": "Prompt"
                }),
                "prompt_optimizer": ("BOOLEAN", {"default": True}),
                "watermark": (["yes", "no"], {"default": "yes"}),
                "concurrent_tasks": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 5,
                    "step": 1,
                    "display": "并发生成数量"
                }),
            },
            "optional": {
                "first_frame_image": ("IMAGE",),  # 用于 video-01 和 video-01-live2d
                "subject_reference_image": ("IMAGE",),  # 新增：用于 S2V-01 的主体参考图
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

    def invoke_video_generation(self, api_key, api_url, prompt, model, base64_image=None, base64_subject_image=None):
        print("-----------------提交视频生成任务-----------------")
        url = f"{api_url}/video_generation"
        
        # 构建基本 payload
        payload = {
            "prompt": prompt,
            "model": model,
            "prompt_optimizer": self.prompt_optimizer,
        }
        
        # 根据watermark选项添加水印参数
        if self.watermark == "yes":
            payload["watermark"] = "hailuo"
        
        # 根据不同模型添加不同的图像参数
        if model == "S2V-01":
            if base64_subject_image is not None:
                payload["subject_reference"] = [{
                    "type": "character",
                    "image": [f"data:image/png;base64,{base64_subject_image}"]
                }]
        else:
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

    def generate_video(self, api_key, api_url, model, prompt, prompt_optimizer, watermark="yes", concurrent_tasks=1, first_frame_image=None, subject_reference_image=None):
        try:
            print(f"\n=== 开始视频生成任务 ===")
            print(f"并发任务数: {concurrent_tasks}")
            self.prompt_optimizer = prompt_optimizer
            self.watermark = watermark
            video_urls = []
            tasks_info = []
            
            # 处理图像编码
            base64_image = None
            base64_subject_image = None
            
            if model == "S2V-01":
                if subject_reference_image is None:
                    raise ValueError("使用 S2V-01 模型时必须提供主体参考图片")
                print("检测到 S2V-01 模型，编码主体参考图片...")
                base64_subject_image = self.encode_image(subject_reference_image)
            else:
                if first_frame_image is not None:
                    print("检测到输入图像，进行编码...")
                    base64_image = self.encode_image(first_frame_image)
            
            current_time = time.strftime("%m%d%H%M")
            print(f"\n--- 开始发起并发请求 ---")
            
            for i in range(concurrent_tasks):
                if i > 0:
                    print(f"等待5秒后发起下一个请求...")
                    time.sleep(5)
                
                try:
                    print(f"\n开始发起任务 #{i+1}/{concurrent_tasks}")
                    task_id = self.invoke_video_generation(api_key, api_url, prompt, model, base64_image, base64_subject_image)
                    trace_id = getattr(self, 'trace_id', 'unknown')
                    
                    tasks_info.append({
                        'index': i + 1,
                        'task_id': task_id,
                        'trace_id': trace_id,
                        'status': 'Queueing',
                        'output_path': f"MM{current_time}_{i+1}_{trace_id}.mp4",
                        'start_time': time.time()
                    })
                    
                    print(f"任务 #{i+1} 请求成功:")
                    print(f"- Task ID: {task_id}")
                    print(f"- Trace ID: {trace_id}")
                    print(f"- Output Path: {tasks_info[-1]['output_path']}")
                    
                except Exception as e:
                    print(f"任务 #{i+1} 发起失败: {str(e)}")
                    raise

            print(f"\n--- 开始监控任务状态 ---")
            while tasks_info:
                for task in tasks_info[:]:
                    try:
                        file_id, status = self.query_video_generation(api_key, api_url, task['task_id'])
                        task['status'] = status
                        
                        elapsed_time = int(time.time() - task['start_time'])
                        print(f"\n任务 #{task['index']} 状态更新:")
                        print(f"- Status: {status}")
                        print(f"- 已用时: {elapsed_time}秒")
                        
                        if status == "Success" and file_id:
                            print(f"\n任务 #{task['index']} 生成成功!")
                            video_url = self.get_video_url(api_key, api_url, file_id)
                            video_path = self.fetch_video_result(api_key, api_url, file_id, task['output_path'])
                            video_urls.append(video_url)
                            print(f"- Video URL: {video_url}")
                            print(f"- Saved to: {video_path}")
                            
                            print(f"\n正在更新预览界面...")
                            print(f"当前视频URLs: {video_urls}")
                            result = self.update_preview(video_urls)
                            print(f"预览更新结果: {result}")
                            
                            tasks_info.remove(task)
                        elif status in ["Fail", "Unknown"]:
                            print(f"\n任务 #{task['index']} 失败!")
                            tasks_info.remove(task)
                            raise Exception(f"视频生成失败 (Task #{task['index']})")
                            
                    except Exception as e:
                        print(f"\n任务 #{task['index']} 处理异常: {str(e)}")
                        tasks_info.remove(task)
                        raise
                
                if tasks_info:
                    print("\n等待20秒后继续查询...")
                    time.sleep(20)
            
            print(f"\n=== 所有 {concurrent_tasks} 个视频生成完成 ===")
            print(f"最终视频URLs: {video_urls}")
            return {
                "ui": {"video_url": video_urls},
                "result": (video_urls,)
            }
                
        except Exception as e:
            print(f"\n=== 发生错误 ===")
            print(f"错误详情: {str(e)}")
            raise e

    def update_preview(self, video_urls):
        """实时更新预览"""
        return {"ui": {"video_url": video_urls}}

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