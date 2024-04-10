import os
from ultralytics import YOLO
from fastapi import FastAPI, UploadFile, File
from typing import List
from haystack import Pipeline
from haystack.components.builders import PromptBuilder, DynamicChatPromptBuilder
from haystack.dataclasses import ChatMessage
from haystack.utils import Secret
from haystack_integrations.components.generators.anthropic import AnthropicChatGenerator
from dotenv import load_dotenv
from utils.image import convert_to_base_64_string, get_image_caption_from_llm, image_2_b64
from PIL import Image

from utils.llm_queries import get_all_objects, claude, gpt4

load_dotenv()

app = FastAPI()


@app.post("/uploadimage/")
async def create_upload_file(image: UploadFile = File(...)):
    image_text = convert_to_base_64_string(image.file.read())
    image_caption = get_image_caption_from_llm(image_text)

    # TODO: Get a topic that the user wants to use.

    # Initialize a YOLO-World model
    model = YOLO('yolov8s-world.pt')  # or choose yolov8m/l-world.pt
    yolo_classes = await get_all_objects(image_caption)
    yolo_classes = list(filter(None, yolo_classes))
    # model.set_classes(yolo_classes)
    # TODO: fix the classes being generated
    model.set_classes(['person'])
    # Execute prediction for specified categories on an image
    results = model.predict(Image.open(image.file, 'r'))
    for result in results:
        result.save("boxes.jpg")
        result.show()

    bounded_boxes = image_2_b64(Image.open("boxes.jpg"))

    box_analysis = gpt4("Based on the image. Explain what the things in the bounding boxes represent in a scenario that would be relevant based on the context of the image.", bounded_boxes)
    print(box_analysis)
    # TODO Create an LMQL prompt that labels each object in the image based off the meme.


    messages = [
        ChatMessage.from_system("You are a meme captioner. Your job is to write a caption for the image based off of the description that is given."),
        ChatMessage.from_user("Image Description: {{image_caption}}"),
    ]
    pipe = Pipeline()

    pipe.add_component("prompt_builder", DynamicChatPromptBuilder())
    pipe.add_component("claude", AnthropicChatGenerator(
        api_key=Secret.from_env_var("ANTHROPIC_API_KEY"),
        model="claude-3-opus-20240229"
    ))

    pipe.connect("prompt_builder", "claude")
    result = pipe.run({
        "prompt_builder": {
            "template_variables": {
                "image_caption": image_caption
            },
            "prompt_source": messages
        },
    })

    return {"results": result}
