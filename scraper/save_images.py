import asyncio
import json
from pathlib import Path

import aiohttp
import ijson
from azure.core.exceptions import ResourceNotFoundError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
import aiofiles
import requests
from azure.storage.blob.aio import BlobServiceClient, ContainerClient
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker
from tqdm import tqdm

from meme_database.models import MemeEntry, MemeImage
from scraper.downloadimages import upload_to_azure, azure_blob_check
import os
load_dotenv()
account_url = "https://aimemes.blob.core.windows.net"

blob_service_client = BlobServiceClient(account_url, credential=os.getenv("AZURE_STORAGE_KEY"))
proxies = {'http': 'http://brd-customer-hl_4a5981ec-zone-business:lgw3i1br1nkx@brd.superproxy.io:22225',
               'https': 'http://brd-customer-hl_4a5981ec-zone-business:lgw3i1br1nkx@brd.superproxy.io:22225'}


engine = create_async_engine(os.getenv("NEON_POSTGRES"), echo=True)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def save_image_to_database(session, meme_entry_id, source_url, blob_url):
    new_image = MemeImage(meme_entry=meme_entry_id, source_url=blob_url)
    session.add(new_image)

async def download_and_save_image(session, meme_entry_id, image_link):
    if image_link is None or image_link == "None":
        return
    async with aiohttp.ClientSession() as http_session:
        async with http_session.get(image_link) as response:
            if response.status != 200:
                print("error")
                return
            try:

                content = await response.read()
                filename = image_link.split("/")[-1]
                # Ensure upload_to_azure function is async or adjust accordingly
                blob_url = await upload_to_azure(content, blob_service_client, "memes", meme_entry_id, filename)

                await save_image_to_database(session, meme_entry_id, image_link, blob_url)
            except Exception as e:
                return

async def process_batch(session, batch, pbar):
    tasks = []

    for meme in batch:
        task = download_and_save_image(session, meme['id'], meme['source_url'])
        tasks.append(task)


    
    if not tasks:
        return
    # Create a tqdm progress bar for tasks
    for f in asyncio.as_completed(tasks):
        await f  # Awaiting completion here, ensures we track each task


    pbar.update(1)

async def check_if_exists(meme, container):
    blob_client = container.get_blob_client(f'{meme["id"]}/{meme["source_url"].split("/")[-1]}')

    try:
        await blob_client.get_blob_properties()  # Ensure to use await here

        return True, meme
    except ResourceNotFoundError:
        return False, meme
    except Exception as e:
        print(f"Error checking blob existence: {e}")
        return False, meme

async def process_meme_file_batch(batch, non_used_memes, container, pbar):
    tasks = [asyncio.create_task(check_if_exists(meme, container)) for meme in batch]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    await asyncio.sleep(1)  # Add a small delay to avoid rate limiting
    for result in results:
        if isinstance(result, Exception):
            print(f"Error processing meme: {result}")
        else:
            exists, meme = result
            if not exists:
                non_used_memes.append(meme)

    pbar.update(1)  # Update the progress bar each time a batch is processed
    await asyncio.sleep(2)
async def main():

    # try:
    #     async with aiofiles.open('meme_photo_links.json', mode='r') as file:
    #         memes = json.loads(await file.read())
    #
    #     non_used_memes = []
    #     memes = [meme for meme in memes if meme['source_url'] is not None]
    #
    #     batch_size = 300  # Adjust based on your environment and resources
    #     batches = [memes[i:i + batch_size] for i in range(0, len(memes), batch_size)]
    #
    #     print(f"Scanning {len(memes)} memes in {len(batches)} batches.")
    #
    #     # Create tqdm progress bar
    #     pbar = tqdm(total=len(batches), desc="Processing Batches")
    #     sem = asyncio.Semaphore(10)  # Adjust based on your environment and Azure's rate limits
    #
    #     async def limited_process_batch(batch, non_used_memes, container, pbar):
    #         async with sem:
    #             await process_meme_file_batch(batch, non_used_memes, container, pbar)
    #
    #     tasks = [asyncio.create_task(limited_process_batch(batch, non_used_memes, container, pbar)) for batch in
    #              batches]
    #     await asyncio.gather(*tasks)
    #     pbar.close()  # Make sure to close the progress bar after all batches are processed
    #
    #     print(f"Found {len(non_used_memes)} memes that haven't been uploaded")
    #
    # finally:
    #     await container.close()  # Ensure the container client is closed properly
    # # Save to json file outside the loop
    # async with aiofiles.open('non_used_memes.json', mode='w') as f:
    #     await f.write(json.dumps(non_used_memes))

    container = ContainerClient.from_connection_string(os.getenv("AZURE_STORAGE_CONN_KEY"), container_name="memes")
    async with aiofiles.open('non_used_memes.json', mode='r') as file:
        memes = json.loads(await file.read())  # Consider using ijson for large files
        # remove all memes with none
        memes = [meme for meme in memes if meme['source_url'] is not None]
        batch_size = 20
        batches = [memes[i:i + batch_size] for i in range(0, len(memes), batch_size)]
        sem = asyncio.Semaphore(3)  # Adjust based on your environment and Azure's rate limits
        pbar = tqdm(total=len(batches), desc="Processing Batches", position=0, leave=True)
        async with SessionLocal() as session:
            async def limited_process_batch(session, batch, pbar):
                async with sem:
                    await process_batch(session, batch, pbar)

            tasks = [asyncio.create_task(limited_process_batch(session, batch, pbar)) for batch in
                     batches]
            await asyncio.gather(*tasks)
            await session.commit()
asyncio.run(main())