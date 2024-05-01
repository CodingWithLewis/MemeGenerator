from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

import easyocr
import requests
from azure.storage.blob import BlobClient
from dotenv import load_dotenv
import os
from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials

from array import array
import os
from PIL import Image
import sys
import time

from tqdm import tqdm

from meme_database.models import MemeImage

load_dotenv()

subscription_key = os.environ["AZURE_VISION_KEY"]
endpoint = os.environ["AZURE_VISION_ENDPOINT"]

computervision_client = ComputerVisionClient(endpoint, CognitiveServicesCredentials(subscription_key))
engine = create_engine(os.getenv("NEON_POSTGRES"), pool_pre_ping=True)


def read_image(meme: MemeImage, session: Session):
    read_response = computervision_client.read(f"{meme.source_url}?{os.getenv('AZURE_BLOB_SAS_TOKEN')}", raw=True)
    read_operation_location = read_response.headers["Operation-Location"]
    operation_id = read_operation_location.split("/")[-1]
    while True:
        read_result = computervision_client.get_read_result(operation_id)
        if read_result.status == OperationStatusCodes.succeeded:
            text = ""
            for text_result in read_result.analyze_result.read_results:
                for line in text_result.lines:
                    text += line.text + " "
            meme.caption_text = text
            return

        time.sleep(1)


def read_image_locally(meme: MemeImage, session: Session, reader: easyocr.Reader):
    try:

        image_data = requests.get(f"{meme.source_url}?{os.getenv('AZURE_BLOB_SAS_TOKEN')}").content
        result = reader.readtext(image_data)
        text = ''
        for detection in result:
            text += f"'{detection[1]}' \n"
        if len(text) > 8000:
            text = text[:8000]
        if text == '':
            text = "No text detected"
        meme.caption_text = text
    except Exception as e:
        meme.caption_text = "No text detected"

def process_images_concurrently(meme_images: List[MemeImage], session: Session):
    reader = easyocr.Reader(['en'])
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(read_image_locally, meme, session, reader) for meme in meme_images]
        for future in list(tqdm(as_completed(futures), total=len(futures))):
            try:
                future.result()
            except Exception as e:
                pass
    session.commit()


session = Session(engine)
i = 1
while True:
    print(f"Starting iteration {i}")
    query = session.query(MemeImage).filter(MemeImage.caption_text == None).order_by(func.random()).limit(100)
    if len(query.all()) > 0:
        process_images_concurrently(query.all(), session)
        i += 1
    else:
        break
