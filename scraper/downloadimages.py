import asyncio
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from pathlib import Path
import json
import multiprocessing
from typing import Union
import itertools

import aiofiles
import aiohttp
from aiohttp.client import ClientSession
from sqlalchemy.orm import Session
from tinydb import TinyDB, Query
from tqdm.auto import tqdm
from uuid import uuid4
from meme_database.models import MemeEntry, MemeImage
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
from azure.storage.blob.aio import BlobClient
from azure.storage.blob import BlobServiceClient
import requests
from pyquery import PyQuery as pq

load_dotenv()
account_url = "https://aimemes.blob.core.windows.net"


blob_service_client = BlobServiceClient(account_url, credential=os.getenv("AZURE_STORAGE_KEY"))

meme_entries = []
meme_photo_links = []


async def azure_blob_check(meme_id, file_name) -> bool:
    try:

        async with BlobClient.from_connection_string(os.getenv("AZURE_STORAGE_CONN_KEY"), container_name="memes", blob_name=f"{meme_id}/{file_name}") as blob:
            exists = await blob.exists()
            return exists
    except Exception as e:
        print(e)
        return False


executor = ThreadPoolExecutor()
async def upload_to_azure(content, service_client: BlobServiceClient, container_name: str, meme_id: str, filename: str) -> str:

    blob_client = service_client.get_blob_client(container=container_name, blob=f"{meme_id}/{filename}")

    def upload_action():
        blob_client.upload_blob(content, overwrite=True)

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(executor, upload_action)

    return blob_client.url


async def fetch(session: ClientSession, url: str, proxies, retries=3, backoff_factor=0.5):
    for attempt in range(retries):
        try:
            async with session.get(url, proxy=proxies['https']) as response:
                return await response.text()
        except aiohttp.ServerDisconnectedError:
            if attempt < retries - 1:
                sleep_time = backoff_factor * (2 ** attempt)
                await asyncio.sleep(sleep_time)
            else:
                return None
        except Exception as e:
            return None  # Reraising the exception after logging it

async def scrape_image(url, session):
    proxies = {'http': 'http://brd-customer-hl_4a5981ec-zone-business:lgw3i1br1nkx@brd.superproxy.io:22225',
               'https': 'http://brd-customer-hl_4a5981ec-zone-business:lgw3i1br1nkx@brd.superproxy.io:22225'}
    response_text = await fetch(session, f"https://knowyourmeme.com{url}", proxies)

    if response_text is None:
        return "None"

    site = pq(response_text)
    image_link = site("#photo_wrapper a").attr("href")


    # r = requests.get(image_link, proxies=proxies)
    #
    # # Get filename from https://i.kym-cdn.com/photos/images/original/002/738/807/55e.jpg
    # filename = image_link.split("/")[-1]
    # Path("images/").mkdir(exist_ok=True)
    # with open(f"images/{filename}", "wb") as f:
    #     f.write(r.content)
    #
    # blob_url = upload_to_azure(Path(f"images/{filename}"), blob_service_client, "memes")
    #
    # # delete file after upload
    # Path(f"images/{filename}").unlink()
    return image_link

async def process_photo_link(photo_link, meme_id, session):
    if not photo_link:
        return
    image_url = await scrape_image(photo_link, session)
    # meme_image = MemeImage(
    #     meme_entry=meme_id,
    #     source_url=image_url,
    # )
    meme_photo_links.append({
        "id": str(meme_id),
        "source_url": image_url,
        "meme_entry": meme_id,
    })


async def process_meme(meme, pbar, session):
    # Create a uuid for the meme
    meme_id = str(uuid4())
    meme_name = meme['title'].replace(" | Know Your Meme", "")
    # Process meme details
    meme_entries.append({
        "id": str(meme_id),
        "name": meme_name,
        "url": meme['url'],
        "content": meme['content'],
        "meme_added": meme['posted_date'],
    })
    if meme['photo_links']:

        for idx, photo_link in enumerate(meme['photo_links']):
            await process_photo_link(photo_link, meme_id, session)
            pbar.update(1)
            pbar.set_description(f"Successfully processed {pbar.n} memes")
    pbar.update(1)


async def main():
    engine = create_engine(os.getenv("NEON_POSTGRES"), pool_pre_ping=True)
    db = TinyDB('memes.json')
    Memes = Query()
    successful_memes = db.search(Memes.photo_links != [])
    photo_links = len(list(itertools.chain.from_iterable([s['photo_links'] for s in successful_memes])))
    err_count = 1
    async with aiohttp.ClientSession() as session:
        with tqdm(total=len(successful_memes) + photo_links, leave=True) as pbar:
            tasks = [process_meme(meme, pbar, session) for meme in successful_memes]
            results = []

            for task in asyncio.as_completed(tasks):
                try:
                    result = await task
                    results.append(result)
                except Exception as e:
                    pbar.display(msg="Errors: {}".format(err_count), pos=1)
                    err_count += 1
                    pbar.update(1)




if __name__ == "__main__":
    asyncio.run(main())
    # with open("meme_entries.json", "w") as f:
    #     json.dump(meme_entries, f)
    #
    # with open("meme_photo_links.json", "w") as f:
    #     json.dump(meme_photo_links, f)