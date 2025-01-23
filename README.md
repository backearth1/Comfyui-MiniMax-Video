# ComfyUI MiniMax Video Extension

[English](#english) | [中文](#中文)

# English

## Overview
A ComfyUI extension that integrates MiniMax AI's image-to-video, text-to-video, and image-to-prompt generation capabilities, allowing users to easily convert static images into dynamic videos with optimized prompts.

![alt text](image.png)

## Features
- Image to video conversion
- Text to video conversion
- Image to prompt generation
- Support for multiple video generation models
- Real-time video preview
- Custom prompt optimization
- Flexible API configuration

## Installation

1. Clone this repository to your ComfyUI custom_nodes directory:
```bash
cd custom_nodes
git clone https://github.com/backearth1/ComfyUI-MiniMax-Video.git
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Node Parameters

### MiniMax API Client Node
| Parameter | Description | Type | Default |
|-----------|-------------|------|---------|
| api_key | MiniMax API Key | STRING | - |
| api_url | API Base URL | ["https://api.minimax.chat/v1"] | "https://api.minimax.chat/v1" |

https://api.minimax.chat/v1 for users in China；
https://api.minimaxi.chat/v1 for users in other countries

### Image to Prompt Node
| Parameter | Description | Type | Default |
|-----------|-------------|------|---------|
| image | Input Image | IMAGE | - |
| api_key | MiniMax API Key | API_KEY | - |
| api_url | API Base URL | API_URL | - |
| model | LLM Model | ["MiniMax-Text-01",  "abab6.5s-chat"] | "MiniMax-Text-01" |
| VLM_prompt | Custom VLM Prompt | STRING | Default prompt template |
| temperature | Model Temperature | FLOAT | 0.1 |

### Image to Video Node
| Parameter | Description | Type | Default |
|-----------|-------------|------|---------|
| client | MiniMax API Client | MINIMAX_CLIENT | - |
| image | Input Image | IMAGE | - |
| prompt | Generation Prompt | STRING | "" |
| model | Video Model | ["video-01", "video-01-live2d","S2V-"] | "video-01" |
| prompt_optimizer | Enable Prompt Optimization | BOOLEAN | true |

## Example Workflows

### Basic Image to Video
- Load an image
- Connect to MiniMax API Client
- Use Image to Video node to generate video
- Preview the result

### Image to Video with Prompt Optimization
![alt text](image_to_prompt.png)
### AI fit clothes workflow
![alt text](fitting.png)
### subject reference
![alt text](S2V.png)

## Tips
1. Ensure you have a valid MiniMax API key
2. Video generation may take some time
3. Generated videos are saved in ComfyUI's output directory
4. Video files are named as "time+trace_id"
5. Use clear frontal images for best results
6. If you don't add any image, the node will support text to video
7. If you want to add watermark, please check "Add Watermark" option in the node parameters
8. If you open concurrent requests, please pay attention to the account configured with enough RPM
9. The Image to Prompt node can help generate better video descriptions

## Troubleshooting

**Q: Why did video generation fail?**
A: Check:
- API key validity
- Network connection
- Input image requirements
- Prompt appropriateness

**Q: How to get the best results?**
A: Recommendations:
- Use clear frontal images
- Use Image to Prompt node for better descriptions
- Write clear and specific prompts
- Choose appropriate models

---

# 中文

## 概述
ComfyUI MiniMax Video 扩展集成了 MiniMax AI 的图像转视频、文本转视频和图像转提示词生成功能，让用户能够轻松地将静态图像转换为动态视频。

![alt text](image.png)

## 功能特点
- 图片转视频
- 文本转视频
- 图像转提示词
- 支持多种视频生成模型
- 实时视频预览
- 自定义提示词优化
- 灵活的 API 配置

## 安装方法

1. 克隆仓库到 ComfyUI 的 custom_nodes 目录：
```bash
cd custom_nodes
git clone https://github.com/backearth1/ComfyUI-MiniMax-Video.git
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

## 节点参数说明

### MiniMax API 客户端节点
| 参数 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| api_key | MiniMax API 密钥 | STRING | - |
| api_url | API 基础地址 | ["https://api.minimax.chat/v1"] | "https://api.minimax.chat/v1" |

中国用户 https://api.minimax.chat/v1 ；
其他地区用户 https://api.minimaxi.chat/v1 

### 图像转提示词节点
| 参数 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| image | 输入图片 | IMAGE | - |
| api_key | MiniMax API 密钥 | API_KEY | - |
| api_url | API 基础地址 | API_URL | - |
| model | 语言模型 | ["MiniMax-Text-01",  "abab6.5s-chat"] | "MiniMax-Text-01" |
| VLM_prompt | 自定义 VLM 提示词 | STRING | 默认提示词模板 |
| temperature | 模型温度 | FLOAT | 0.1 |

### 图像转视频节点
| 参数 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| client | MiniMax API 客户端 | MINIMAX_CLIENT | - |
| image | 输入图片 | IMAGE | - |
| prompt | 生成提示词 | STRING | "" |
| model | 视频模型 | ["video-01", "video-01-live2d","S2V-01"] | "video-01" |
| prompt_optimizer | 启用提示词优化 | BOOLEAN | true |
| watermark | 添加水印 | BOOLEAN | false |
## 示例工作流

### 基础图像转视频
- 加载图像
- 连接 MiniMax API 客户端
- 使用图像转视频节点生成视频
- 预览结果

### 带提示词优化的图像转视频
![alt text](image_to_prompt.png)
### AI试衣服工作流
![alt text](fitting.png)
### 人脸主题参考
![alt text](S2V.png)

## 使用提示
1. 确保拥有有效的 MiniMax API 密钥
2. 视频生成可能需要一定时间
3. 生成的视频会保存在 ComfyUI 的输出目录中
4. 视频文件会以"时间+trace_id"命名
5. 建议使用清晰的正面图片以获得最佳效果
6. 如果未添加任何图片，节点将支持文本转视频
7. 如果需要添加水印，请在节点参数中勾选"添加水印"选项
8. 如果开启并发请求，请注意账号配置了足够的RPM
9. 图像转提示词节点可以帮助生成更好的视频描述

## 常见问题

**Q: 为什么视频生成失败？**
A: 请检查：
- API 密钥是否有效
- 网络连接是否正常
- 输入图片是否符合要求
- 提示词是否合适

**Q: 如何获得最佳效果？**
A: 建议：
- 使用清晰的正面图片
- 使用图像转提示词节点获取更好的描述
- 编写清晰具体的提示词
- 选择合适的模型

## License
MIT License

## 贡献
欢迎提交 Issues 和 Pull Requests！