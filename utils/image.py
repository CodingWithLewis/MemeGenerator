import base64
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


def create_bounding_box_in_image(image: Path, box_coords: tuple[int, int, int, int]) -> Path:
    from PIL import Image, ImageDraw
    import random
    # Open the image
    img = Image.open(image).convert("L")
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
    print(boxes)
    # Open the image
    img = Image.open(original_image.file, 'r')

    # Create a drawing context
    draw = ImageDraw.Draw(img)

    # Specify the font and size
    font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 24)
    for box in boxes:
        bbox = box['box']
        x_center = (bbox[0] + bbox[2]) / 2
        y_center = (bbox[1] + bbox[3]) / 2
        # Specify the position (x, y) where you want to place the text
        position = (x_center, y_center)  # (x, y) coordinates

        # Specify the text, text color, and stroke color
        text = box['metaphor']
        text_color = (255, 255, 255)  # RGB color tuple (white in this case)
        stroke_color = (0, 0, 0)  # RGB color tuple (black in this case)

        # Specify the stroke width
        stroke_width = 2

        # Draw the text on the image with the stroke
        draw.text(position, text, font=font, fill=text_color, stroke_width=stroke_width, stroke_fill=stroke_color, anchor="mm")

    # Save the modified image
    img.save("image_with_text_stroke.jpg")