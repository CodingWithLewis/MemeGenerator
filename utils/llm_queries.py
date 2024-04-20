import json
import random

import anthropic
import lmql
from dotenv import load_dotenv
import requests
from litellm import completion

from utils.image import convert_to_base_64_string

load_dotenv()

client = anthropic.Anthropic()

tools = [
    {
        "type": "function",
        "function": {
            "name": "create_metaphor",
            "description": "Create a metaphor that the object in the picture given can be compared to. This is for memes, so make it funny and follow the prompt / caption given.",
            "parameters": {
                "type": "object",
                "properties": {
                    "metaphor": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "description": "The metaphor that the object in the image can be compared to.",
                            "maxLength": 20,
                            "uniqueItems": True,

                        },
                    "minContains": 2,
                    "maxContains": 2,
                    }
                },
                "required": ["metaphor"]
            },
        }}
]


@lmql.query
async def different_metaphors(image_description: str, funny_reason: str):
    '''lmql
    "Based on this detailed image description: {image_description}. And the reason why it's funny: The image is funny because: {funny_reason}"
    "Here are a list of metaphors that the objects in this image could represent in terms of personal and funny:"
    metaphors=[]
    for i in range(10):
        "[METAPHOR] \n" where STOPS_BEFORE(METAPHOR, "\n")
        metaphors.append(METAPHOR.strip())
    return metaphors
    '''

@lmql.query
async def get_all_objects(image_description: str):
    '''lmql
    "Based on this detailed image description: {image_description}. Give me a list of the main things of subject seperated by commas. Do not use proper nouns. Only common nouns. This will be going in YOLO object detection. e.g 'person'', 'character' or 'animal'"
    items=[]
    for i in range(5):
        "[THING]" where STOPS_BEFORE(THING, ",")
        items.append(THING.strip())
    return items
    '''


# @lmql.query
# async def label_objects(image_description: str):
#     '''lmql
#
#     '''

# def gpt4(prompt: str, image_base64: str = None):
#     response = openai_client.chat.completions.create(
#         model="gpt-4-vision-preview",
#         messages=[
#             {"role": "system", "content": "Based off of the image provided. Identify what is funny about the image. Then, give examples of things in the bounding boxes represented in a scenario that would be relevant based on the context of the image."},
#             {
#                 "role": "user",
#                 "content": [
#                     {"type": "text", "text": prompt},
#                     {
#                         "type": "image_url",
#                         "image_url": {
#                             "url": f"data:image/jpeg;base64,{image_base64}",
#                         },
#                     },
#                 ],
#             }
#         ],
#         max_tokens=300,
#     )
#
#     return response.choices[0]


def claude(prompt: str, image_base64: str = None):
    if image_base64:
        content = [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": image_base64
                }
            },
            {"type": "text", "text": prompt}
        ]
    else:
        content = [
            {"type": "text", "content": prompt}
        ]

    messages = [
        {"role": "user", "content": content}
    ]

    message = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=1024,
        messages=messages,
        system="You explain metaphors and similes in the image. You explain why something is funny. Please be detailed about why it's funny and include a metaphor for the things inside the bounding boxes."
    )

    return message.content


def create_metaphor_labels(boxes: list, initial_image, metaphor_list: list[str]):
    metaphor_list = [x for x in metaphor_list if x] # Remove duds

    chosen_metaphor = random.choice(metaphor_list)

    messages = [
        {"role": "system",
         "content": "Based off of the image and reasoning/metaphor provided. Think of a label that could be"
                    "applied to the items in the bounding boxes. This label should be a metaphorical way of"
                    "relating the items to the viewer in a meme. For example: 'me' or 'the food i just ate' etc."
                    "Be as crude, silly, and random as possible. Base it off of the caption, reasoning and image"
                    "description provided.",
     },
        {
            "role": "user",
            "content": [
                {"type": "text",
                 "text": "Image Description: 2 Spiderman characters are looking and pointing at each other. In a cartoony/silly way.\n"
                         "Reasoning: The image is funny because it shows 2 spiderman that look identical pointing to each other. \n"
                         "The reason this is funny is because both spiderman look alike and are trying to accuse each other of something that they are also themselves guilty of \n"
                            "Metaphor: The metaphor of the image is a meme poster. \n"
                         f"Use this Metaphor to think of labels: {chosen_metaphor}"

                 },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{initial_image}",
                    },
                }
            ],
        }
    ]

    metaphors = []
    for box in boxes:
        with open(box['image'], "rb") as image_file:
            image = image_file.read()
            messages[1]["content"].append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{convert_to_base_64_string(image)}",
                },
            })
    response = completion(model="gpt-4-turbo", messages=messages, tools=tools, tool_choice={
        "type": "function",
        "function": {"name": "create_metaphor"}
    })

    metaphor = json.loads(response.choices[0].message.tool_calls[0].function.arguments)['metaphor']
    for idx, m in enumerate(metaphor):
        if idx + 1 > len(boxes):
            break
        metaphors.append({
            "box": boxes[idx]['coords'],
            "metaphor": m,
            "image": boxes[idx]['image']
        })

    return metaphors


def create_completion(prompt: str, image_base64=None):
    messages = [
        {"role": "system",
         "content": "Based off of the image provided. Identify what is funny about the image. Then, give examples of things in the bounding boxes represented in a scenario that would be relevant based on the context of the image."},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
            ],
        }
    ]

    if image_base64:
        messages[1]["content"].append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{image_base64}",
            },
        })

    tools = [
        {
            "type": "function",
            "function": {
                "name": "create_metaphor",
                "description": "Create a metaphor that the object in the picture given can be compared to. This is for memes, so make it funny and follow the prompt / caption given.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "metaphor": {
                            "type": "string",
                            "description": "The metaphor that the object in the image can be compared to.",
                            "maxLength": 20
                        }
                    },
                    "required": ["metaphor"]
                }
            }
        }
    ]

    # openai call
    response = completion(model="gpt-4-turbo", messages=messages, tools=tools, tool_choice={
        "type": "function",
        "function": {"name": "create_metaphor"}
    })

    print(response)


def create_meme_caption():
    url = "https://app.openpipe.ai/api/v1/chat/completions"

    headers = {
        "Authorization": "Bearer opk_ac45d39119f0e9cb3c4d7f49c02f2a369ffb7a412d",
        "Content-Type": "application/json",
        "op-log-request": "true"
    }

    data = {
        "model": "openpipe:cold-socks-say",
        "messages": [
            {
                "role": "system",
                "content": "Write a caption for this meme based on the description and tone of the image. Be as obscure, silly and funny as possible. You will be given Metaphors, image descriptions and more."
            },
            {
                "role": "user",
                "content": "Image Description: Joker is looking playful at a old man in a bar.\n"
                           "Metaphor: The metaphor of Joker is Meme poster.\n"
                           "Metaphor: The metaphor of a old man is Meme poster. \n"
                           "Metaphor: The metaphor of a bar is Meme poster. \n"
                           "Metaphor: The metaphor of looking is Meme poster."
            }
        ],
        "temperature": 0
    }

    response = requests.post(url, headers=headers, json=data)

    print(response.json())
    return "HI"
