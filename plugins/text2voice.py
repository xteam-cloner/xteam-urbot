import requests
import base64
import os
from . import *
url = 'https://texttospeech.googleapis.com/v1/text:synthesize'
api_key = 'AIzaSyBrHRq1560psTF4pnWChWGV4G1mgymWb8g'
headers = {
    'x-goog-api-key': api_key,
    'content-type': 'application/json; charset=utf-8',
    'accept-encoding': 'gzip',
    'user-agent': 'okhttp/4.11.0'
}

@ultroid_cmd(pattern="voice ?(.*)")
async def voice_cmd(event):
    input_text = event.pattern_match.group(1)
    previous_message = None
    if not input_text and event.reply_to_msg_id:
        previous_message = await event.get_reply_message()
        if previous_message.media:
            await event.edit("Invalid Syntax. Please reply to a text message.")
            return
        input_text = previous_message.text

    if not input_text:
        await event.edit("Invalid Syntax. Please specify text to convert to speech.")
        return

    data = {
        "audioConfig": {
            "audioEncoding": "MP3",
            "effectsProfileId": [],
            "pitch": 0.0,
            "sampleRateHertz": 0,
            "speakingRate": 1.0,
            "volumeGainDb": 0
        },
        "input": {
            "text": input_text
        },
        "voice": {
            "languageCode": "en-US",
            "name": "en-US-Casual-K",
            "ssmlGender": "SSML_VOICE_GENDER_UNSPECIFIED"
        }
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        audio_content = response.json()["audioContent"]
        audio_data = base64.b64decode(audio_content)
        
        file_name = f"downloads/{event.chat_id}_{event.id}.mp3"
        os.makedirs("downloads", exist_ok=True)
        with open(file_name, "wb") as f:
            f.write(audio_data)
        
        if previous_message:
            await event.client.send_file(
                event.chat_id,
                file_name,
                voice_note=True,
                reply_to=previous_message.id,
            )
        else:
            await event.client.send_file(
                event.chat_id,
                file_name,
                voice_note=True,
                reply_to=event.reply_to_msg_id,
            )
        os.remove(file_name)
        await event.delete()
    else:
        await event.edit("Error: Failed to generate audio file.")

CMD_HELP.update({
    "voice":
    "voice <text>\
    \nUsage: Generate an audio file of the specified text using Google Text-to-Speech API. \
    \n\nExample: voice Hello world"
})

# Code created by Noah (@cat_me_if_you_can2)
