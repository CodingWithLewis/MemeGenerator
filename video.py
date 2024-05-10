from scraper.get_news_source import get_news_article
from utils.image import convert_to_base_64_string
from utils.llm_queries import create_meme_based_off_news


def get_news_meme(url: str, image: bytes):
    news_source = get_news_article(url)
    image = convert_to_base_64_string(image)
    meme = create_meme_based_off_news(news_source, image)

    return meme
