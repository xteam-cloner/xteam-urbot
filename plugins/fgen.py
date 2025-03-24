from telethon import events
from . import *

@ultroid_cmd(pattern="fontgen (.+)")
async def fontgen(event):
    """Mengubah teks menjadi berbagai gaya font."""
    text = event.pattern_match.group(1)
    if not text:
        return await event.reply("Silakan berikan teks yang ingin Anda ubah.")

    fonts = {
        "bold": "\U0001D401",  # Contoh: A Bold
        "italic": "\U0001D43C", # Contoh: a Italic
        "monospace": "\U0001D5BE", # Contoh: a Monospace
        # Tambahkan lebih banyak gaya font di sini
    }

    result = ""
    for char in text:
        if char.isalpha():
            for font_name, font_char in fonts.items():
                if font_name == "bold":
                    result += chr(ord(font_char) + ord(char) - ord('A')) if char.isupper() else chr(ord(font_char) + ord(char) - ord('a'))
                elif font_name == "italic":
                    result += chr(ord(font_char) + ord(char) - ord('A')) if char.isupper() else chr(ord(font_char) + ord(char) - ord('a'))
                elif font_name == "monospace":
                    result += chr(ord(font_char) + ord(char) - ord('A')) if char.isupper() else chr(ord(font_char) + ord(char) - ord('a'))
                # Tambahkan logika untuk gaya font lainnya
            result += " "  # Tambahkan spasi antar karakter
        else:
            result += char

    await event.reply(result)

def sanitize_text(text):
    """Membersihkan teks dari karakter yang tidak diinginkan."""
    sanitized_text = ''.join(c for c in text if ord(c) >= 32)
    return sanitized_text

async def main(ultroid):
    ultroid.add_event_handler(fontgen)
                  
