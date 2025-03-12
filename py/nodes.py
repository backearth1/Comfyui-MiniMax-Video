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
                "model": (["I2V-01","T2V-01","I2V-01-Director","T2V-01-Director", "I2V-01-live", "S2V-01"],),  # 添加 S2V-01 模型
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
                "first_frame_image": ("IMAGE",),  # 用于 I2V-01 , I2V-01-live和I2V-01-Director
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

class ImageToPrompt:
    def __init__(self):
        self.last_result = None
        self.last_inputs = None
        print("初始化 ImageToPrompt 节点")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_key": ("API_KEY",),
                "api_url": ("API_URL",),
                "model": (["MiniMax-Text-01", "abab6.5s-chat"],),
                "image": ("IMAGE",),
                "LLM_prompt": ("STRING", {
                    "default": "You will receive an image (which will be the first frame of the video) and user input (which describes what the user wants to generate based on this image). \n"
                              "Your task is to combine their information to construct a video description that will be used to generate a video.\n\n"
                              "- Do NOT add any content that is not in the image or user input!!!\n"
                              "- Do NOT add any camera movement that is not in the image or user input!!!\n"
                              "- If the user input does not mention any movement for the main subject, add subtle motions based on the current actions of the subject in the image to avoid stillness in the video.\n"
                              "- The user input may be empty, meaning the user did not provide any information. Please follow the above rules to generate a video description.\n"
                              "- Please return the description in English and in 150 words.\n\n"
                              "User Input:\n",
                    "multiline": True,
                    "display": "LLM Prompt"
                }),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "generate_prompt"
    CATEGORY = "minimax"

    def generate_prompt(self, api_key, api_url, model, image, LLM_prompt):
        print("\n=== ImageToPrompt 节点执行 ===")
        
        # 检查输入是否与上次相同
        current_inputs = (
            api_key, 
            api_url, 
            model, 
            hash(image.cpu().numpy().tobytes()),  # 使用 numpy 数组的哈希值
            LLM_prompt
        )
        
        if self.last_inputs == current_inputs and self.last_result is not None:
            print("使用缓存的结果")
            return self.last_result

        # 确保 API URL 包含完整的端点路径
        if not api_url.endswith('/chat/completions'):
            api_url = f"{api_url.rstrip('/')}/chat/completions"
        
        # 将 Tensor 转换为 PIL Image
        if isinstance(image, torch.Tensor):
            if len(image.shape) == 4:
                image = image[0]  # 移除批次维度
            image = image.permute(1, 2, 0)  # 将通道维度移到最后
            image = (image * 255).clamp(0, 255).byte().cpu().numpy()  # 转换为 numpy 数组
            if image.shape[2] == 1:  # 如果是单通道图像
                image = image.squeeze(axis=2)  # 移除单通道维度
                mode = "L"  # 灰度图像模式
            else:
                mode = "RGB"  # 彩色图像模式
            image = Image.fromarray(image, mode)

        # 将图像编码为 base64
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": LLM_prompt
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
            print(f"请求的 API URL: {api_url}")
            response = requests.post(api_url, headers=headers, json=payload)
            print(f"API 响应状态码: {response.status_code}")
            print(f"API 响应内容: {response.text}")

            # 检查响应状态码
            if response.status_code != 200:
                raise Exception(f"API 请求失败，状态码: {response.status_code}")

            response_json = response.json()
            prompt = response_json.get('choices', [{}])[0].get('message', {}).get('content', '')
            print(f"生成的文本提示: {prompt}")
            
            # 缓存结果
            self.last_inputs = current_inputs
            self.last_result = (prompt,)
            return self.last_result
        except requests.exceptions.JSONDecodeError as e:
            print(f"JSON 解析错误: {str(e)}")
            raise
        except Exception as e:
            print(f"API 请求失败: {str(e)}")
            raise

class MiniMaxImageGenerator:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_key": ("API_KEY",),
                "api_url": ("API_URL",),
                "prompt": ("STRING", {
                    "default": "", 
                    "multiline": True,
                    "display": "Prompt"
                }),
                "model": (["image-xy01", "image-01"], {"default": "image-xy01"}),
                "aspect_ratio": (["1:1", "16:9", "4:3", "3:2", "2:3", "3:4", "9:16", "21:9"], {"default": "16:9"}),
                "n": ("INT", {"default": 1, "min": 1, "max": 9, "step": 1}),
                "prompt_optimizer": ("BOOLEAN", {"default": True})
            },
            "hidden": {
                "seed": ("INT", {"default": -1, "min": -1, "max": 2147483647})
            }
        }
    
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)
    FUNCTION = "generate_image"
    CATEGORY = "minimax"

    def generate_image(self, api_key, api_url, prompt, model, aspect_ratio, n, prompt_optimizer, seed=-1):
        # 构建完整的图像生成API URL
        image_api_url = f"{api_url.rstrip('/')}/image_generation"
        
        payload = {
            "model": model,
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "response_format": "url",
            "n": n,
            "prompt_optimizer": prompt_optimizer
        }
        
        # 只有当种子值不为-1时，才添加到payload中
        if seed != -1:
            payload["seed"] = seed
            
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        print(f"正在请求MiniMax API生成图像，提示词: {prompt}")
        
        try:
            response = requests.post(image_api_url, headers=headers, data=json.dumps(payload))
            response_data = json.loads(response.text)
            
            print(f"Trace-Id: {response.headers.get('Trace-Id')}")
            
            if 'data' in response_data and 'image_urls' in response_data['data']:
                images = []
                
                for i, image_url in enumerate(response_data['data']['image_urls']):
                    # 解码URL中的转义字符
                    decoded_url = image_url.encode('utf-8').decode('unicode_escape')
                    print(f"获取图像 {i+1} URL: {decoded_url}")
                    
                    # 下载图像
                    img_response = requests.get(decoded_url)
                    img = Image.open(io.BytesIO(img_response.content))
                    
                    # 转换为ComfyUI可用的格式
                    img_tensor = torch.from_numpy(np.array(img).astype(np.float32) / 255.0)
                    # 确保图像格式为[H, W, 3]
                    if len(img_tensor.shape) == 2:  # 灰度图
                        img_tensor = img_tensor.unsqueeze(-1).repeat(1, 1, 3)
                    images.append(img_tensor)
                
                # 打包图像为批次
                if images:
                    batch_images = torch.stack(images)
                    print(f"成功生成 {len(images)} 张图像")
                    return (batch_images,)
                else:
                    raise Exception("无法获取图像")
            else:
                error_msg = response_data.get('message', '未知错误')
                error_code = response_data.get('code', '未知代码')
                raise Exception(f"API错误: {error_code} - {error_msg}")
        
        except Exception as e:
            print(f"请求处理过程中出错: {str(e)}")
            # 返回空图像，防止节点崩溃
            empty_image = torch.zeros((1, 64, 64, 3))
            return (empty_image,)

# 更新节点映射
NODE_CLASS_MAPPINGS = {
    "MiniMaxPreviewVideo": MiniMaxPreviewVideo,
    "MiniMaxAIAPIClient": MiniMaxAIAPIClient,
    "MiniMaxImage2Video": MiniMaxImage2Video,
    "ImageToPrompt": ImageToPrompt,
    "MiniMaxImageGenerator": MiniMaxImageGenerator,  # 添加新节点
}

# 更新节点显示名称映射
NODE_DISPLAY_NAME_MAPPINGS = {
    "MiniMaxPreviewVideo": "MiniMax Preview Video",
    "MiniMaxAIAPIClient": "MiniMax API Client",
    "MiniMaxImage2Video": "MiniMax Image to Video",
    "ImageToPrompt": "Image to Prompt",
    "MiniMaxImageGenerator": "MiniMax Image Generator",  # 添加新节点显示名称
}