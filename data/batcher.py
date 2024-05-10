import json
from dotenv import load_dotenv

load_dotenv()
import os

# {"custom_id": "request-1", "method": "POST", "url": "/v1/chat/completions", "body": {"model": "gpt-3.5-turbo-0125", "messages": [{"role": "system", "content": "You are a helpful assistant."},{"role": "user", "content": "Hello world!"}],"max_tokens": 1000}}
# {"custom_id": "request-2", "method": "POST", "url": "/v1/chat/completions", "body": {"model": "gpt-3.5-turbo-0125", "messages": [{"role": "system", "content": "You are an unhelpful assistant."},{"role": "user", "content": "Hello world!"}],"max_tokens": 1000}}

with open("meme_templates_azure.json") as f:
    memes = json.load(f)

batched_memes = []

for meme in memes:
    batched_memes.append({
        "custom_id": meme['id'],
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": "gpt-4-turbo",
            "messages": [
                {
                    "role": "system",
                    "content": "You are looking at memes. You need to describe the meme in as much detail as possible "
                               "and explain why it is funny. Explain also what is in the picture in great detail. "
                               "Also read out what the meme says if text is on screen."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Please explain this meme in as much detail as possible. Why is it considered funny? "
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                 "url": f"{meme['photo_url']}?{os.getenv('AZURE_BLOB_SAS_TOKEN')}"
                            }
                         }
                    ]
                }
            ]
        }
    })


# save as jsonl
with open("batched_memes.jsonl", "w") as f:
    for meme in batched_memes:
        f.write(json.dumps(meme))
        f.write("\n")
