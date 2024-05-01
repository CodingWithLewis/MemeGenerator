import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Uuid, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from dotenv import load_dotenv
import os
load_dotenv()


class Base(DeclarativeBase):
    pass


class MemeEntry(Base):
    __tablename__ = 'meme_entry'
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text("gen_random_uuid()"))
    name: Mapped[str] = mapped_column(String(200))
    url: Mapped[str]
    content: Mapped[str] = mapped_column(Text)
    images: Mapped[List["MemeImage"]] = relationship()
    meme_added: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=True
    )


class MemeImage(Base):

    __tablename__ = 'meme_image'
    id: Mapped[int] = mapped_column(primary_key=True)
    meme_entry: Mapped[uuid.UUID] = mapped_column(ForeignKey("meme_entry.id"))
    source_url: Mapped[str]
    caption_text: Mapped[Optional[str]] = mapped_column(String(8000), nullable=True)