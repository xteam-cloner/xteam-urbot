from deep_translator import GoogleTranslator
from . import *

@ultroid_cmd(pattern="tr (.*)")
async def translate_text(event):
    args = event.pattern_match.group(1).strip().split(" | ")

    if len(args) != 2:
        await eor(event, "`Usage: .translate <text> | <target_language>`")
        return

    text, target_language = args
    xx = await eor(event, "`Translating...`")

    try:
        translated = GoogleTranslator(source='auto', target=target_language).translate(text)
        await xx.edit(f"**Translated:**\n{translated}")

    except Exception as e:
        await xx.edit(f"**Error:** `{e}`")
      
