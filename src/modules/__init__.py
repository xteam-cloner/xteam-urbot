from src.pytgcalls import call  # Import the voice call handler
from src.logger import LOGGER

async def start_bot():
    # Initialize the voice call system
    await call.start()  # Start the voice call client
    LOGGER.info("Voice client started!")

# Start the bot with its initialization logic
start_bot()  # Call it during bot launch.

# Debug: Print all loaded modules
import os
import importlib
import sys

def load_modules():
    LOGGER.info("Loading modules...")
    modules_dir = os.path.dirname(__file__)
    for filename in os.listdir(modules_dir):
        if filename.endswith('.py') and not filename.startswith('__'):
            module_name = filename[:-3]
            try:
                importlib.import_module(f'src.modules.{module_name}')
                LOGGER.info(f"Loaded module: {module_name}")
            except Exception as e:
                LOGGER.error(f"Failed to load module {module_name}: {e}")

load_modules()
