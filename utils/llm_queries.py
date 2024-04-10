import anthropic
import lmql
from dotenv import load_dotenv
from openai import Client
load_dotenv()

client = anthropic.Anthropic()
openai_client = Client()

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

def gpt4(prompt: str, image_base64: str = None):
    response = openai_client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[
            {"role": "system", "content": "Based off of the image provided. Identify what is funny about the image. Then, give examples of things in the bounding boxes represented in a scenario that would be relevant based on the context of the image."},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}",
                        },
                    },
                ],
            }
        ],
        max_tokens=300,
    )

    return response.choices[0]


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
