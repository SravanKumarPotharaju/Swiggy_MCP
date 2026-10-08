import asyncio
import logging

logger = logging.getLogger(__name__)


class TrackingWorker:
    def __init__(self):
        self.is_running = False

    async def start(self):
        self.is_running = True
        logger.info("TrackingWorker started.")
        while self.is_running:
            # Poll order status updates or consume from queue
            await asyncio.sleep(10)

    async def stop(self):
        self.is_running = False
        logger.info("TrackingWorker stopped.")


tracking_worker = TrackingWorker()
