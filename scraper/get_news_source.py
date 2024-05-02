import requests
from newspaper import Article
from newspaper.configuration import Configuration
def get_news_article(url):

    proxies = {'http': 'http://brd-customer-hl_4a5981ec-zone-business:lgw3i1br1nkx@brd.superproxy.io:22225',
               'https': 'http://brd-customer-hl_4a5981ec-zone-business:lgw3i1br1nkx@brd.superproxy.io:22225'}
    USER_AGENT = "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0"

    config = Configuration()

    config.proxies = proxies

    # response = requests.get(url, proxies=proxies)

    article = Article(url, config=config)
    article.download()
    article.parse()
    if not article.text:
        return None
    return article.text


if __name__ == "__main__":
    get_news_article(
        "https://www.cnn.com/2024/04/24/tech/tiktok-ban-bytedance-split-the-world-further-intl-hnk/index.html")
