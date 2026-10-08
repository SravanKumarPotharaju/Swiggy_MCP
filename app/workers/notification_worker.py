import asyncio
import logging

logger = logging.getLogger(__name__)


class NotificationWorker:
    def __init__(self):
        self.is_running = False

    async def start(self):
        self.is_running = True
        logger.info("NotificationWorker started.")
        while self.is_running:
            # Process pending notification events
            await asyncio.sleep(5)

    async def stop(self):
        self.is_running = False
        logger.info("NotificationWorker stopped.")


notification_worker = NotificationWorker()
