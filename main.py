import io

from ultralytics import YOLO
from dotenv import load_dotenv

from data.datafetch import retrieve_relevant_meme
from scraper.get_news_source import get_news_article
from utils.image import convert_to_base_64_string, get_image_caption_from_llm, image_2_b64, create_bounding_boxes, \
    create_bounding_box_in_image, add_captions_to_image
from PIL import Image

from utils.llm_queries import get_all_objects, \
    different_metaphors, create_metaphor_labels

load_dotenv()

def send_to_logs(log, logs, log_area):
    logs.append(log)
    log_area.markdown = "\n".join(logs)

def create_upload_file(image: bytes, news_url: str, log_area):
    logs = []
    send_to_logs("grabbing news article...", logs, log_area)
    news_information = get_news_article(news_url)
    if news_information is None:
        return

    send_to_logs("grabbing image descriptions and captions...", logs, log_area)
    image_text = convert_to_base_64_string(image)
    image_caption = get_image_caption_from_llm(image_text)
    relevant_meme_description = retrieve_relevant_meme(image_caption)
    send_to_logs("Grabbing Metaphors...", logs, log_area)
    metaphors = different_metaphors(image_caption, relevant_meme_description, news_information)
    # TODO: Get a topic that the user wants to use.
    send_to_logs("Looking for objects", logs, log_area)
    # Initialize a YOLO-World model
    model = YOLO('yolov8s-world.pt')  # or choose yolov8m/l-world.pt
    yolo_classes =  get_all_objects(image_caption)
    yolo_classes = list(filter(None, yolo_classes))
    # model.set_classes(yolo_classes)
    # TODO: fix the classes being generated
    model.set_classes(['person'])
    # Execute prediction for specified categories on an image

    results = model.predict(source=Image.open(io.BytesIO(image)))
    send_to_logs("Creating bounding boxes...", logs, log_area)
    box_coords = create_bounding_boxes(results)

    box_images = []
    for box in box_coords:
        box_images.append({
            "image": create_bounding_box_in_image(image, box),
            "coords": box
        })

    # Try GPT-4
    send_to_logs("Creating labels...", logs, log_area)
    metaphor_labels = create_metaphor_labels(box_images, image_text, metaphors, news_information, image_caption)
    send_to_logs("Finishing up...", logs, log_area)
    final_image_path = add_captions_to_image(metaphor_labels, image)
    return final_image_path
    # bounded_boxes = image_2_b64(Image.open("boxes.jpg"))
    # create_completion(image_caption, bounded_boxes)
    # # box_analysis = gpt4("Based on the image. Explain what the things in the bounding boxes represent in a scenario that would be relevant based on the context of the image.", bounded_boxes)
    # # print(box_analysis)
    # # TODO Create an LMQL prompt that labels each object in the image based off the meme.
    #
    #
    # messages = [
    #     ChatMessage.from_system("You are a meme captioner. Your job is to write a caption for the image based off of the description that is given."),
    #     ChatMessage.from_user("Image Description: {{image_caption}}"),
    # ]
    # pipe = Pipeline()
    #
    # pipe.add_component("prompt_builder", DynamicChatPromptBuilder())
    # pipe.add_component("claude", AnthropicChatGenerator(
    #     api_key=Secret.from_env_var("ANTHROPIC_API_KEY"),
    #     model="claude-3-opus-20240229"
    # ))
    #
    # pipe.connect("prompt_builder", "claude")
    # result = pipe.run({
    #     "prompt_builder": {
    #         "template_variables": {
    #             "image_caption": image_caption
    #         },
    #         "prompt_source": messages
    #     },
    # })
    #
    # return {"results": result}
