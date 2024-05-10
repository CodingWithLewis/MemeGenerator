import gradio_client
from dotenv import load_dotenv
from gradio_client import Client

load_dotenv()


# Define your desired output structure


def detect_objects(image):
    client = Client("http://127.0.0.1:7860/")
    result = client.predict(
        gradio_client.file("tests/dax.png"),
        "man with beard",  # str  in 'text_queries' Textbox component
        0.15,  # float (numeric value between 0 and 1) in 'score_threshold' Slider component
        api_name="/predict",
    )

    return result[1]


with open("tests/dax.png", "rb") as f:
    image = f.read()

    detect_objects(image)
