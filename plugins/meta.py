import requests
from . import *
from telethon import events

@ultroid_cmd(pattern="metaim")
async def buat_gambar(event):
    if event.text[1:].split():
        prompt = event.text[1:].split(' ', 1)[1]
        response = requests.post(
            url="https://api.llama.com/v1/images/generations",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {os.environ.get('LLAMA_API_KEY')}"
            },
            json={
                "model": "Llama-4-Maverick-17B-128E-Instruct-FP8",
                "prompt": prompt,
                "size": "1024x1024"
            }
        )
        image_url = response.json()["data"][0]["url"]
        await event.respond(file=image_url)
    else:
        await event.respond("Mohon masukkan prompt!")

  import requests
from .. import *
from telethon import events

@ultroid_cmd(pattern="meta")
async def meta_ai(event):
    if event.text[1:].split():
        prompt = event.text[1:].split(' ', 1)[1]
        response = requests.post(
            url="https://api.llama.com/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {os.environ.get('LLAMA_API_KEY')}"
            },
            json={
                "model": "Llama-4-Maverick-17B-128E-Instruct-FP8",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
        )
        await event.respond(response.json()["choices"][0]["message"]["content"])
    else:
        await event.respond("Mohon masukkan prompt!")
      
