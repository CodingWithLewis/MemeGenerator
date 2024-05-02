import json
import random

import anthropic
import litellm
import lmql
from dotenv import load_dotenv
import requests
from litellm import completion
import os
from utils.image import convert_to_base_64_string

load_dotenv()

client = anthropic.Anthropic()

tools = [
    {
        "type": "function",
        "function": {
            "name": "create_metaphor",
            "description": "Create a metaphor that the object in the picture given can be compared to. "
                           "This is for memes, so make it funny and follow the prompt / caption given.",
            "parameters": {
                "type": "object",
                "properties": {
                    "metaphor": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "description": "A metaphor that the object in the image can be compared to.",
                            "maxLength": 20,
                            "uniqueItems": True,

                        },
                        "minContains": 2,
                        "maxContains": 2,
                    }
                },
                "required": ["metaphor"]
            },
        }},
    {
        "type": "function",
        "function": {
            "name": "create_scenarios",
            "description": "Creates many scenarios that is relatable to a human being in a funny and crude way"
                           "given a description of the image and the backstory of the meme. "
                           "This is for memes, so make it funny and follow the prompt / caption given.",
            "parameters": {
                "type": "object",
                "properties": {
                    "scenarios": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "description": "A scenario that the objects in the image can be compared to. Very relatable to"
                                           "the person that would be reading the meme.",
                            "maxLength": 40,
                            "uniqueItems": True,

                        },
                        "minContains": 1,
                        "maxContains": 20,
                    }
                },
                "required": ["metaphor"]
            },
        }
    }
]


# litellm.add_function_to_prompt = True
def different_metaphors(image_description: str, funny_reason: str, news_information: str):
    metaphors = completion(
        model="command-r-plus",
        messages=[
            {'role': 'user',
             'content': f'''
             Based on this image description: {image_description}. And the meme history:  {funny_reason}
            Give me a list of relatable scenarios that the objects in this image could represent in terms of personal and funny. 
            Be as crude and strange as possible and make it relatable to human beings in a funny and clever way.
            
            Use context of this news article to help you form these scenarios. Be specific and try to use proper nouns.
            News Article: {news_information} 
             '''}
        ],
        tools=tools,
        tool_choice={
            "type": "function",
            "function": {"name": "create_scenarios"}
        }
    )
    return json.loads(metaphors.choices[0].message.tool_calls[0].function.arguments)['scenarios']


@lmql.query
def get_all_objects(image_description: str):
    '''lmql
    "Based on this detailed image description: {image_description}. Give me a list of the main things of subject seperated by commas. Do not use proper nouns. Only common nouns. This will be going in YOLO object detection. e.g 'person'', 'character' or 'animal'"
    items=[]
    for i in range(5):
        "[THING]" where STOPS_BEFORE(THING, ",")
        items.append(THING.strip())
    return items
    '''


def create_metaphor_labels(boxes: list, initial_image, metaphor_list: list[str], news_information: str, image_description: str, ):
    metaphor_list = [x for x in metaphor_list if x]  # Remove duds

    chosen_metaphor = random.choice(metaphor_list)

    messages = [
        {"role": "system",
         "content": "Based off of the image and reasoning/metaphor provided. Think of a label that could be"
                    "applied to the items in the bounding boxes. This label should be a metaphorical way of"
                    "relating the items to the viewer in a meme. For example: 'me' or 'the food i just ate' etc."
                    "Be as crude, silly, and random as possible. Base it off of the caption, reasoning and image"
                    "description provided. Please use the news information provided and the subjects of interest within it.",
         },
        {
            "role": "user",
            "content": [
                {"type": "text",
                 "text": f"Image Description: {image_description}"
                         f"Use this Scenario to think of labels for each object. Scenario: {chosen_metaphor}"
                         f"Please use the news information provided and the subjects of interest within it to create something people will "
                         f"recognize."
                         f"News Article: {news_information}",

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
