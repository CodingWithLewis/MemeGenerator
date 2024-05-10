import os
from concurrent.futures import ThreadPoolExecutor

import requests
from sqlalchemy.orm import Session
from tqdm import tqdm

from meme_database.models import MemeEntry
from sqlalchemy import create_engine, select
from dotenv import load_dotenv
from pyquery import PyQuery as pq
import json

load_dotenv()
image_links = []
def fetch_and_process_meme(meme: MemeEntry):
    try:
        response = requests.get(meme.url, proxies=proxies)
        d = pq(response.text)
        # Assuming the header element with class 'photo' contains an href attribute
        href = d("header .photo").attr('href')
        if href:
            image_links.append({
                "id": str(meme.id),
                "template_url": href
            })
    except Exception as e:
        print(f"Error processing {meme.url}: {e}")


proxies = {'http': 'http://brd-customer-hl_4a5981ec-zone-business:lgw3i1br1nkx@brd.superproxy.io:22225',
               'https': 'http://brd-customer-hl_4a5981ec-zone-business:lgw3i1br1nkx@brd.superproxy.io:22225'}


engine = create_engine(os.getenv("NEON_POSTGRES"))


def main():
    with Session(engine) as session:
        memes = session.scalars(select(MemeEntry)).all()

    # Use a ThreadPoolExecutor to manage multiple threads
    with ThreadPoolExecutor(max_workers=10) as executor:
        list(tqdm(executor.map(fetch_and_process_meme, memes), total=len(memes)))

    with open("template_memes.json", 'w') as f:
        json.dump(image_links, f)


if __name__ == "__main__":
    main()
