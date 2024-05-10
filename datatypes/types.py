from enum import Enum

from pydantic import BaseModel, Field, conlist


class Owlv2Classification(BaseModel):
    object: str
    pos: conlist(int, min_length=4, max_length=4)


class MetaphorLabel(BaseModel):
    metaphor: str = Field(
        description="A literal definition of what the object/character can represent"
        "Don't make up anything. Just use the items that are specifically in the article. Use proper nouns to describe."
        "Ideally understand what the other metaphor is saying and use that as a basis for the metaphor.",
        max_length=18,
    )


class FinalMetaphorImageLabel(BaseModel):
    box: conlist(int, min_length=4, max_length=4)
    label: str
    object: str


class Theme(Enum):
    unexpected = "Unexpectedness"
    exaggeration = "Exaggeration"
    absurdity = "Absurdity"
    wordplay = "Wordplay"
    juxtaposition = "Juxtaposition"
    incongruity = "Incongruity"


class Descriptions(BaseModel):
    theme: Theme
    image_description: str


class MemeInformation(BaseModel):
    image_description: str
    funny_reason: str
    funny_theme: Theme
    physical_items_in_image: conlist(str, max_length=2) = Field(
        description="Subjects of interest in the image."
        "Use only things that can explicitly be"
        "seen or labelled. Try to do the most recognizable objects in the image."
        "or abstract concepts. only animals, people, characters or"
        "objects that are easily recognizable. Keep each description as 1 or 2 words max. Use labels that "
        "can uniquely identify humans (young, old, child)"
    )


class Scenario(BaseModel):
    funny_scenarios: conlist(str, max_length=8, min_length=2) = Field(
        description="Scenarios that can be used to make light of the news article"
        "only use facts from the news article. Don't make up anything. Be realistic. use proper nouns"
        "it's important to use the exact names of the people, places or company names."
        "Use proper nouns as well as identifying characteristics of the theme of the news article."
    )
