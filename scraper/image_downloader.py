import asyncio
import traceback
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from pathlib import Path
import json
import multiprocessing
from typing import Union, List
import itertools
from urllib.parse import urlparse

import aiofiles
import aiohttp
from aiohttp.client import ClientSession
from pydantic import BaseModel, RootModel, ValidationError
from sqlalchemy.orm import Session
from tinydb import TinyDB, Query
from tqdm.auto import tqdm
from uuid import uuid4
from meme_database.models import MemeEntry, MemeImage
from sqlalchemy import create_engine, select
from dotenv import load_dotenv
import os
from azure.storage.blob.aio import BlobClient
from azure.storage.blob import BlobServiceClient
import requests
from pyquery import PyQuery as pq

load_dotenv()
account_url = "https://aimemes.blob.core.windows.net"

blob_service_client = BlobServiceClient(account_url, credential=os.getenv("AZURE_STORAGE_KEY"))

azure_uploaded_links = []


async def azure_blob_check(meme_id, file_name) -> bool:
    try:

        async with BlobClient.from_connection_string(os.getenv("AZURE_STORAGE_CONN_KEY"), container_name="memes",
                                                     blob_name=f"{meme_id}/{file_name}") as blob:
            exists = await blob.exists()
            return exists
    except Exception as e:
        print(e)
        return False


executor = ThreadPoolExecutor()


async def upload_to_azure(content, service_client: BlobServiceClient, container_name: str, meme_id: str,
                          filename: str) -> str:
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

                return await response.read()
        except aiohttp.ServerDisconnectedError:
            if attempt < retries - 1:
                sleep_time = backoff_factor * (2 ** attempt)
                await asyncio.sleep(sleep_time)
            else:
                return None
        except Exception as e:
            print(e)
            return None  # Reraising the exception after logging it


async def scrape_image(url, session):
    proxies = {'http': 'http://brd-customer-hl_4a5981ec-zone-business:lgw3i1br1nkx@brd.superproxy.io:22225',
               'https': 'http://brd-customer-hl_4a5981ec-zone-business:lgw3i1br1nkx@brd.superproxy.io:22225'}
    response_text = await fetch(session, url, proxies)

    return response_text


async def get_file_extension(url):
    parsed_url = urlparse(url)
    _, file_extension = os.path.splitext(parsed_url.path)
    return file_extension.lstrip('.')


async def process_photo_link(photo_link: str, meme_id: str, session: ClientSession):

    if not photo_link:
        return
    image_content = await scrape_image(photo_link, session)
    # get file extension from url
    file_extension = await get_file_extension(photo_link)

    template_image_url = await upload_to_azure(image_content, blob_service_client, "memes", meme_id,
                                         f"{meme_id}_template.{file_extension}")

    azure_uploaded_links.append({
        "id": str(meme_id),
        "azure_url": photo_link,
        "photo_url": template_image_url,
    })


class MemeLink(BaseModel):
    id: str
    template_url: str


class MemeLinkList(RootModel):
    root: List[MemeLink]


async def process_meme(meme: MemeLink, pbar: tqdm, client_session: ClientSession):

    if not meme.template_url:
        return

    await process_photo_link(meme.template_url, meme.id, client_session)
    pbar.update(1)


async def main():
    engine = create_engine(os.getenv("NEON_POSTGRES"), pool_pre_ping=True)

    err_count = 1
    memes = []
    async with aiofiles.open("template_memes.json", "r") as fout:
        memes_json = json.loads(await fout.read())
        memes_len = len(memes_json)
    try:
        for meme in memes_json:
            memes.append(MemeLink.parse_obj(
                meme
            ))

    except ValidationError as e:
        print(traceback.format_exc())

    async with aiohttp.ClientSession() as client_session:
        with tqdm(total=memes_len, leave=True) as pbar:
            tasks = [process_meme(meme, pbar, client_session) for meme in memes]
            results = []

            for task in asyncio.as_completed(tasks):
                try:
                    result = await task
                    results.append(result)
                except Exception as e:
                    print(traceback.format_exc())
                    pbar.display(msg="Errors: {}".format(err_count), pos=1)
                    err_count += 1
                    pbar.update(1)


if __name__ == "__main__":
    asyncio.run(main())
    with open("meme_templates_azure.json", "w") as f:
        json.dump(azure_uploaded_links, f)
    #
    # with open("meme_photo_links.json", "w") as f:
    #     json.dump(meme_photo_links, f)
