from dotenv import load_dotenv

from data.datafetch import retrieve_relevant_meme
from scraper.get_news_source import get_news_article
from utils.image import (
    convert_to_base_64_string,
    add_captions_to_image,
)
from utils.llm_queries import (
    different_scenarios,
    get_image_caption_from_llm,
    create_metaphor_labels,
    detect_objects_in_image,
)

load_dotenv()


def send_to_logs(log, log_area, completed=None):
    if completed:
        log_area.update(label=log)
    log_area.update(label=log)


def create_upload_file(image: bytes, news_url: str, log_area):
    send_to_logs("grabbing news article...", log_area)
    news_information = get_news_article(news_url)
    if news_information is None:
        return

    send_to_logs("grabbing image descriptions and captions...", log_area)
    image_text = convert_to_base_64_string(image)
    meme_information = get_image_caption_from_llm(image_text)
    relevant_meme_description = retrieve_relevant_meme(
        meme_information.image_description
    )
    send_to_logs("Grabbing Metaphors...", log_area)
    scenarios = different_scenarios(
        meme_information, relevant_meme_description, news_information
    )

    send_to_logs("Looking for objects", log_area)
    object_coordinates = detect_objects_in_image(
        image, meme_information.physical_items_in_image
    )

    send_to_logs("Creating labels...", log_area)

    metaphor_labels = create_metaphor_labels(
        object_coordinates,
        image_text,
        scenarios.funny_scenarios,
        news_information,
        meme_information,
    )
    print(metaphor_labels)
    send_to_logs("Finishing up...", log_area)
    final_image_path = add_captions_to_image(metaphor_labels, image)
    return final_image_path
