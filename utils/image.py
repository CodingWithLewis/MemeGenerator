import base64
import io
import textwrap
from io import BytesIO
from pathlib import Path
from typing import List

from PIL import Image, ImageDraw, ImageFont
from pydantic import conlist

from datatypes.types import FinalMetaphorImageLabel


def convert_to_base_64_string(image: bytes) -> str:
    return base64.b64encode(image).decode("utf-8")


def image_2_b64(image):
    buff = BytesIO()
    image.save(buff, format="JPEG")
    img_str = base64.b64encode(buff.getvalue()).decode("utf-8")
    return img_str


def create_bounding_box_in_image(
    image: bytes, box_coords: conlist(int, min_length=4, max_length=4)
) -> Path:
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


def add_captions_to_image(boxes: List[FinalMetaphorImageLabel], original_image: bytes):
    original_image = io.BytesIO(original_image)
    img = Image.open(original_image)
    draw = ImageDraw.Draw(img)
    font_size = 24
    font = ImageFont.load_default(font_size)  # Ensure you have the correct font path

    for box in boxes:
        bbox = box.box
        text = box.label

        # Calculate bounding box dimensions
        box_width = bbox[2] - bbox[0]
        box_height = bbox[3] - bbox[1]
        max_line_length = int(
            box_width / (font_size * 0.2)
        )  # Adjust multiplier as needed

        # Wrap text to fit within bounding box width
        lines = textwrap.wrap(text, width=max_line_length)

        # Calculate the total text height
        text_height = len(lines) * font_size

        # Calculate initial y position to center text vertically
        y_text = bbox[1] + (box_height - text_height) / 2

        for line in lines:
            # Measure text size for each line
            text_size = draw.textlength(line, font=font)

            # Calculate text position to center it horizontally
            text_x = bbox[0] + (box_width - text_size) / 2

            # Draw each line of text
            draw.text(
                (text_x, y_text),
                line,
                font=font,
                fill=(255, 255, 255),
                stroke_width=2,
                stroke_fill=(0, 0, 0),
            )
            y_text += font_size  # Move y coordinate for next line

    img.save("image_with_text_stroke.jpg")
    return Path("image_with_text_stroke.jpg")
