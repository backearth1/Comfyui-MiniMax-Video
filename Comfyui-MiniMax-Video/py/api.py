import requests
import json
import time
import base64

class MiniMaxAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            'authorization': f'Bearer {api_key}',
            'content-type': 'application/json'
        }

    def generate_video(self, prompt, model, image_base64):
        url = "https://api.minimax.chat/v1/video_generation"
        payload = {
            "prompt": prompt,
            "model": model,
            "first_frame_image": f"data:image/jpeg;base64,{image_base64}"
        }
        
        response = requests.post(url, headers=self.headers, json=payload)
        if response.status_code != 200:
            raise RuntimeError(f"API request failed: {response.text}")
        return response.json()['task_id']

    def query_status(self, task_id):
        url = f"https://api.minimax.chat/v1/query/video_generation?task_id={task_id}"
        response = requests.get(url, headers=self.headers)
        result = response.json()
        
        if result['status'] == 'Success':
            return result['file_id'], "Success"
        elif result['status'] in ['Queueing', 'Processing']:
            return None, result['status']
        else:
            return None, "Failed"

    def get_video_url(self, file_id):
        url = f"https://api.minimax.chat/v1/files/retrieve?file_id={file_id}"
        response = requests.get(url, headers=self.headers)
        return response.json()['file']['download_url']

    def download_video(self, url, output_path):
        response = requests.get(url)
        with open(output_path, 'wb') as f:
            f.write(response.content)
        return output_path