import base64
import io
import textwrap
from io import BytesIO
from pathlib import Path

import requests
from fastapi import UploadFile
from PIL import Image, ImageDraw, ImageFont

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


def create_bounding_boxes(results: list) -> list[tuple[int, int, int, int]]:
    boxes = []
    for result in results:
        result.save("boxes.jpg")
        for box in result.boxes:
            print(box.xyxy)
            xyxy_coords = [coord for coord in box.xyxy[0].tolist()]

            # Unpack the coordinates
            x1, y1, x2, y2 = xyxy_coords

            # Create a tuple representing the bounding box
            bbox = (x1, y1, x2, y2)

            print(bbox)
            boxes.append(bbox)

    return boxes


def create_bounding_box_in_image(image: bytes, box_coords: tuple[int, int, int, int]) -> Path:
    from PIL import Image, ImageDraw
    import random
    # Open the image
    img = Image.open(io.BytesIO(image)).convert("L")
    img.save("gray_image.jpg")

    img = Image.open("gray_image.jpg").convert("RGB")

    # Create a drawing object
    draw = ImageDraw.Draw(img)

    # Draw the bounding boxes
    draw.rectangle(box_coords, outline="red", width=5)

    file_name = Path(f"outputs/boxed_image_{random.randint(0, 1000)}.jpg", mkdir=True)

    # Save the image with the bounding boxes
    img.save(file_name)

    return Path(file_name)


def add_captions_to_image(boxes, original_image):
    original_image = io.BytesIO(original_image)
    img = Image.open(original_image)

    draw = ImageDraw.Draw(img)
    font_path = "/System/Library/Fonts/Supplemental/Arial.ttf"
    font_size = 24
    font = ImageFont.truetype(font_path, font_size)

    for box in boxes:
        bbox = box['box']
        text = box['metaphor']

        # Calculate bounding box width and height
        box_width = bbox[2] - bbox[0]
        max_line_length = int(box_width / (font_size * 0.2))  # Estimate max characters per line, adjust multiplier as needed

        # Wrap text to fit within bounding box width
        lines = textwrap.wrap(text, width=max_line_length)
        y_text = bbox[1]

        for line in lines:
            # Measure text size for each line
            text_size = draw.textlength(line, font=font)
            # If the text width is wider than the box, reduce the font size
            while text_size > box_width:
                font_size -= 1
                font = ImageFont.truetype(font_path, font_size)
                text_size = draw.textlength(line, font=font)

            # Calculate text position to center it horizontally
            text_x = bbox[0] + (box_width - text_size) / 2

            # Draw each line of text
            draw.text((text_x, y_text), line, font=font, fill=(255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0))
            y_text += text_size  # Move y coordinate for next line

    img.save("image_with_text_stroke.jpg")
    return Path("image_with_text_stroke.jpg")