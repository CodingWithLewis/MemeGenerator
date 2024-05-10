import random
from typing import List

import gradio_client
import instructor
import requests
from dotenv import load_dotenv
from gradio_client import Client
from openai import OpenAI
from pydantic import BaseModel, Field

from datatypes.types import (
    MemeInformation,
    Descriptions,
    Owlv2Classification,
    FinalMetaphorImageLabel,
    MetaphorLabel,
    Scenario,
)

load_dotenv()

tools = [
    {
        "type": "function",
        "function": {
            "name": "create_scenarios",
            "description": "Creates many scenarios that is relatable to a human being in a funny and crude way"
            "given a description of the image and the backstory of the meme. Use the news article given to reference and relate. Use those as primary subjects of interest."
            "This is for memes, so make it funny and follow the prompt / caption given.",
            "parameters": {
                "type": "object",
                "properties": {
                    "scenarios": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "description": "A scenario that the objects in the image can be compared to. Very relatable to"
                            "the person that would be reading the meme. Relate this to the news article that was given and use proper nouns within it.",
                            "maxLength": 40,
                            "uniqueItems": True,
                        },
                        "minContains": 1,
                        "maxContains": 5,
                    }
                },
                "required": ["metaphor"],
            },
        },
    },
]


# litellm.add_function_to_prompt = True
def different_scenarios(
    meme_information: MemeInformation, relevant_meme_history: str, news_information: str
) -> Scenario:
    client = instructor.from_openai(OpenAI())
    scenarios = client.chat.completions.create(
        model="gpt-4-turbo",
        response_model=Scenario,
        messages=[
            {
                "role": "system",
                "content": "You create funny scenarios based off of the news article that is given."
                "In the scenarios use the subjects of interest in the news article to determine."
                "",
            },
            {
                "role": "user",
                "content": f"""
             Give me a list of funny scenarios based off of the news article given. Take into account the theme of the image when thinking of what these funyn scenarios might look like.
             The theme for this meme will be {meme_information.funny_theme}. Follow this as closely as possible. Use the news source
             as context for the meme. Use as many subjects of interest as possible so that the meme is relatable to the viewer.
            Be as crude and strange as possible and make it relatable to human beings in a funny and clever way.
            
            Use context of this news article to help you form these scenarios. Be specific and try to use proper nouns.
            
            Image Description: {meme_information.image_description}
            Funny Theme: {meme_information.funny_theme}
            News Article: {news_information}
             """,
            },
        ],
    )

    return scenarios


def detect_objects_in_image(
    image: bytes, items_to_detect: List[str]
) -> List[Owlv2Classification]:
    # save the image to a file
    path = "outputs/test_image.jpg"
    with open(path, "wb") as f:
        f.write(image)
    client = Client("https://codingwithlewis-owlv2.hf.space")
    result = client.predict(
        gradio_client.file(path),
        ",".join(items_to_detect),  # str  in 'text_queries' Textbox component
        0.15,  # float (numeric value between 0 and 1) in 'score_threshold' Slider component
        api_name="/predict",
    )
    retrieved_items = []
    items = []
    for res in result[1]:
        # Check to see if the object is in the list of items to detect
        # if res["object"] in retrieved_items:
        #     continue
        items.append(Owlv2Classification(object=res["object"], pos=res["pos"]))
        retrieved_items.append(res["object"])
    return items


def get_type_of_humor(base64_image):
    # Patch the OpenAI client
    client = instructor.from_openai(OpenAI())

    # Extract structured data from natural language
    descriptions = client.chat.completions.create(
        model="gpt-4-turbo",
        response_model=Descriptions,
        messages=[
            {
                "role": "system",
                "content": "Explain why this meme is funny and suggest a reason how it can be used as a meme to be captioned.",
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Based on what is in this image, what would be the best way to describe why this is funny? ",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                    },
                ],
            },
        ],
    )

    return descriptions.theme


def create_metaphor_labels(
    boxes: List[Owlv2Classification],
    initial_image,
    metaphor_list: list[str],
    news_information: str,
    meme_information: MemeInformation,
) -> List[FinalMetaphorImageLabel]:
    client = instructor.from_openai(OpenAI())
    metaphor_list = [x for x in metaphor_list if x]  # Remove duds
    labels = []
    chosen_metaphor = random.choice(metaphor_list)

    characters = []
    for box in boxes:
        metaphor_label = client.chat.completions.create(
            model="gpt-4-turbo",
            response_model=MetaphorLabel,
            messages=[
                {
                    "role": "system",
                    "content": "Based off of the image and reasoning/scenario provided. Think of a label that could be"
                    "applied to the image in bounding boxes.",
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Use this Scenario to think of labels for each object that will be going into a meme. The label should be a {meme_information.funny_theme}"
                            f"way of relating the items to the viewer in a meme. Use the news information characters as the metaphor/representation of the meme. Avoid terms like: 'me' or 'I'."
                            f"Use Proper nouns of the most relevant people in the news article "
                            f"Please use the news information provided and the subjects of interest within it to create something people will recognize."
                            f"Object you are labelling: {box.object}"
                            f"Scenario: {chosen_metaphor}"
                            f"Image Description: {meme_information.image_description}"
                            f"News Article: {news_information}"
                            f"Why It's Funny: {meme_information.funny_reason}"
                            f"Previous Character Labels: {characters}",
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{initial_image}",
                            },
                        },
                    ],
                },
            ],
        )
        characters.append(f"Character: {box.object} Label: {metaphor_label.metaphor}")
        labels.append(
            FinalMetaphorImageLabel.parse_obj(
                {
                    "box": box.pos,
                    "label": metaphor_label.metaphor,
                    "object": box.object,
                }
            )
        )

    return labels


def get_image_caption_from_llm(image: str) -> MemeInformation:
    client = instructor.from_openai(OpenAI())

    meme_response = client.chat.completions.create(
        model="gpt-4-turbo",
        response_model=MemeInformation,
        messages=[
            {
                "role": "system",
                "content": "You are a humor bot. Based on the image given, give me the reason something is funny,"
                "an extremely detailed description of the image, a funny theme that can work well with the"
                "image, as well as a list of subjects of interest within the image that can be used to relate"
                "to the viewer so we can label it.",
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Please give me a detailed description, reason that it's funny, a funny theme and the subjects"
                        "of interest",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image}"},
                    },
                ],
            },
        ],
    )

    print(meme_response)

    return meme_response


def create_meme_caption():
    url = "https://app.openpipe.ai/api/v1/chat/completions"

    headers = {
        "Authorization": "Bearer opk_ac45d39119f0e9cb3c4d7f49c02f2a369ffb7a412d",
        "Content-Type": "application/json",
        "op-log-request": "true",
    }

    data = {
        "model": "openpipe:cold-socks-say",
        "messages": [
            {
                "role": "system",
                "content": "Write a caption for this meme based on the description and tone of the image. Be as obscure, silly and funny as possible. You will be given Metaphors, image descriptions and more.",
            },
            {
                "role": "user",
                "content": "Image Description: Joker is looking playful at a old man in a bar.\n"
                "Metaphor: The metaphor of Joker is Meme poster.\n"
                "Metaphor: The metaphor of a old man is Meme poster. \n"
                "Metaphor: The metaphor of a bar is Meme poster. \n"
                "Metaphor: The metaphor of looking is Meme poster.",
            },
        ],
        "temperature": 0,
    }

    response = requests.post(url, headers=headers, json=data)

    print(response.json())
    return "HI"


class NewsMemeData(BaseModel):
    meme_caption: str = Field(
        description="A one sentence caption for the meme. "
        "The caption should be in the point of view of one of the subjects in the article. Don't use words like 'I' or 'Me'. Only proper nouns of the items in the article "
        "For example: <SUBJECT> when...."
        "Be Crude and abrupt."
        "Make grammar mistakes for fun. Use the description of the image as a juxtaposition"
    )


def create_meme_based_off_news(news: str, image: str):
    client = instructor.from_openai(OpenAI())
    meme_response = client.chat.completions.create(
        model="gpt-4-turbo",
        response_model=NewsMemeData,
        messages=[
            {
                "role": "system",
                "content": "You make memes based off of the image and news article provided. "
                "You are putting a caption on the image. Use one of the subjects in the news articles as a point of view. for example: <subject> when... Use the proper nouns within the news article to"
                "use as the joke within the image caption.",
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Use the proper nouns within the news article to"
                        "use as the joke within the image caption."
                        f"News Article: {news}",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image}"},
                    },
                ],
            },
        ],
    )
    return meme_response.meme_caption.lower()
