import base64
from io import BytesIO

import requests
from fastapi import UploadFile


def convert_to_base_64_string(image: bytes) -> str:
    return base64.b64encode(image).decode("utf-8")


def image_2_b64(image):
    buff = BytesIO()
    image.save(buff, format="JPEG")
    img_str = base64.b64encode(buff.getvalue()).decode("utf-8")
    return img_str

def get_image_caption_from_llm(image: str):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llava",
            "prompt": f"Given the image below, go into as much detail as possible about "
                      f"the image and possible ways it could be humorous.",
            "images": [image],
            "stream": False
        }
    )

    return response.json()['response']
