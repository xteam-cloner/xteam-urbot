import asyncio
import platform
import subprocess
from telethon import TelegramClient, events
from . import *

# --- Ping Function ---
def ping(host):
    """Pings a host and returns the output. Handles different OSs."""
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '3', host]  # Ping 3 times
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error: {e}"
    except FileNotFoundError:
        return "Error: Ping command not found. (Check your system's ping utility)"
    except Exception as e:
        return f"An unexpected error occurred: {e}"


# --- Telethon Handlers ---

@ultroid_bot.on(events.NewMessage(pattern='/Aping'))  # Bot command
async def ping_handler(event):
    try:
        message_parts = event.message.text.split()
        if len(message_parts) < 2:
            await event.reply("Please provide a hostname or IP address to ping.")
            return

        host = message_parts[1]
        await event.reply(f"Pinging {host}...")

        ping_output = ping(host)

        # --- React to the message with the ping output ---
        sent_message = await event.reply(f"```\n{ping_output}\n```", parse_mode='markdown')
        await sent_message.react('✅') # React with a checkmark.  You can use other emojis.

    except Exception as e:
        await event.reply(f"An error occurred: {e}")


async def main():
    await bot.start()
    print("Bot started. Listening for /ping commands...")
    await bot.run_until_disconnected()


if __name__ == '__main__':
    asyncio.run(main())

