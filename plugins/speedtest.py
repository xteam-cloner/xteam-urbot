from telethon import Button, events

from . import *

import asyncio
import speedtest

# Commands

def testspeed(m):
    try:
        test = speedtest.Speedtest()
        test.get_best_server()
        test.download()
        test.upload()
        test.results.share()
        result = test.results.dict()
    except Exception as e:
        return
    return result

@ultroid_cmd(pattern="speedtest")
async def speedtest_function(message):
    m = await message.reply("Running Speed test")
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, testspeed, m)
    output = f"""**<blockquote>✯ sᴩᴇᴇᴅᴛᴇsᴛ ʀᴇsᴜʟᴛs ✯
    
❍ Client:
» ISP: {result['client']['isp']}
» Country: {result['client']['country']}
  
❍ Server:
» Name: {result['server']['name']}
» Country: {result['server']['country']}, {result['server']['cc']}
» Sponsor: {result['server']['sponsor']}
» Latency: {result['server']['latency']}  
» Ping: {result['ping']}</blockquote>"""
    await ultroid_bot.send_file(message.chat.id, result["share"], caption=output, parse_mode="html")
    await m.delete()
