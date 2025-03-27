import logging

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(filename)s:%(lineno)d - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[logging.StreamHandler()],
)

# Reduce logging verbosity for third-party libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("pyrogram").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.WARNING)
logging.getLogger("youtube").setLevel(logging.WARNING)
# logging.getLogger("ntgcalls").setLevel(logging.DEBUG)
# logging.getLogger("pytgcalls").setLevel(logging.DEBUG)

LOGGER = logging.getLogger("Bot")
