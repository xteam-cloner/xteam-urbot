import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytdbot import Client, types

from src.modules.utils.cacher import chat_cache
from src.pytgcalls import call


class InactiveCallManager:
    def __init__(self, bot: Client):
        self.bot = bot
        self.scheduler = AsyncIOScheduler(
            timezone="Asia/Kolkata", event_loop=self.bot.loop
        )

    async def _end_inactive_calls(self, chat_id: int, semaphore: asyncio.Semaphore):
        async with semaphore:
            vc_users = await call.vc_users(chat_id)
            if len(vc_users) > 1:
                self.bot.logger.debug(
                    f"Active users detected in chat {chat_id}. Skipping..."
                )
                return

            # Check if the call has been active for more than 20 seconds
            played_time = await call.played_time(chat_id)
            if played_time < 20:
                self.bot.logger.debug(
                    f"Call in chat {chat_id} has been active for less than 20 seconds. Skipping..."
                )
                return

            # Notify the chat and end the call
            reply = await self.bot.sendTextMessage(
                chat_id, "⚠️ No active listeners detected. ⏹️ Leaving voice chat..."
            )
            if isinstance(reply, types.Error):
                self.bot.logger.warning(f"Error sending message: {reply}")
            await call.end(chat_id)

    async def end_inactive_calls(self):
        active_chats = await chat_cache.get_active_chats()
        self.bot.logger.debug(
            f"Found {len(active_chats)} active chats. Ending inactive calls..."
        )
        if not active_chats:
            return

        # Use a semaphore to limit concurrency
        semaphore = asyncio.Semaphore(3)
        tasks = [
            self._end_inactive_calls(chat_id, semaphore) for chat_id in active_chats
        ]

        # Process tasks in batches of 3 with a 1-second delay between batches
        for i in range(0, len(tasks), 3):
            await asyncio.gather(*tasks[i: i + 3])
            await asyncio.sleep(1)

        self.bot.logger.debug("Inactive call checks completed.")

    async def start_scheduler(self):
        # Schedule the job to run every 50 seconds
        self.scheduler.add_job(self.end_inactive_calls, "interval", seconds=50)
        self.scheduler.start()
        self.bot.logger.info(
            "Scheduler started. Inactive call checks will run every 50 seconds."
        )

    async def stop_scheduler(self):
        self.scheduler.shutdown()
        self.bot.logger.info("Scheduler stopped.")
