from src.pytgcalls import call  # Import the voice call handler

async def start_bot():
    # Initialize the voice call system
    await call.start()  # Start the voice call client
    print("Voice client started!")

# Start the bot with its initialization logic
start_bot()  # Call it during bot launch.
