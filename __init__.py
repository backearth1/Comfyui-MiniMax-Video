import os
import sys

sys.path.append(os.path.dirname(os.path.realpath(__file__)))

from .py.nodes import (
    MiniMaxAIAPIClient,
    MiniMaxImage2Video,
    MiniMaxPreviewVideo,
    ImageToPrompt,
)

NODE_CLASS_MAPPINGS = {
    "MiniMaxAIAPIClient": MiniMaxAIAPIClient,
    "MiniMaxImage2Video": MiniMaxImage2Video,
    "MiniMaxPreviewVideo": MiniMaxPreviewVideo,
    "ImageToPrompt": ImageToPrompt,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MiniMaxAIAPIClient": "MiniMax API Client",
    "MiniMaxImage2Video": "MiniMax Image to Video",
    "MiniMaxPreviewVideo": "MiniMax Preview Video",
    "ImageToPrompt": "Image to Prompt",
}

WEB_DIRECTORY = os.path.join(os.path.dirname(os.path.realpath(__file__)), "web")
print(f"加载 MiniMax 扩展 Web 目录: {WEB_DIRECTORY}")

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']