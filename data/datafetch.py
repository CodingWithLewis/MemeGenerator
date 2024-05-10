from sqlalchemy import select
from sqlalchemy.orm import Session

from meme_database.models import MemeEntry, MemeImage
import openai
from dotenv import load_dotenv
import os
from sqlalchemy.engine import create_engine


load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai.Client()


def retrieve_relevant_meme(meme_description: str):

    embedding = client.embeddings.create(
        model="text-embedding-3-small",
        input=meme_description
    )
    # Query postgres database with SQLAlchemy
    engine = create_engine(os.getenv("NEON_POSTGRES"))

    with Session(engine) as session:
        query = session.scalars(select(MemeEntry).order_by(MemeEntry.content_embedding.l2_distance(embedding.data[0].embedding)).limit(5))

        meme = query.first()

        # retrieve images
        images = session.scalars(select(MemeImage).where(MemeImage.meme_entry == meme.id))

        image_captions = []
        for caption in images:
            if caption.caption_text != "No text detected":
                image_captions.append(caption.caption_text)
        nl = "\n"
        random_choice = f"""
            Meme Name: {meme.name}
            
            Meme Description: {meme.content}
            
            Meme Caption Samples: {nl} {nl.join(image_captions)}
        """

    return random_choice


if __name__ == "__main__":
    relevant_meme = retrieve_relevant_meme(
        "2 spiderman looking at each other and pointing")


    print(relevant_meme)