# quote_fetcher.py
import signal
import asyncio
from typing import Optional

from app.core.logging import log
from app.services.quote_fetcher import AsyncQuoteFetcher


class AsyncQuoteFetcherScheduler:
    """Fully async scheduler for periodic RSS fetching."""

    def __init__(self, feed_url: str, interval_hours: int = 24):
        """
        Initialize the scheduler with a feed URL and polling interval, and register OS signal handlers for graceful shutdown.
        
        Parameters:
            feed_url (str): URL of the RSS feed to fetch.
            interval_hours (int): Polling interval in hours; converted to seconds and stored as `interval_seconds`.
        """
        self.feed_url = feed_url
        self.interval_seconds = interval_hours * 3600
        self.running = True
        self.loop: Optional[asyncio.AbstractEventLoop] = None

        # Graceful shutdown signals
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signum, frame):
        """
        Handle an OS shutdown signal and initiate a graceful shutdown.
        
        Sets the scheduler's running flag to False and cancels all asyncio tasks associated with the stored event loop so the scheduler can stop cleanly.
        
        Parameters:
            signum (int): The signal number received (e.g., SIGINT, SIGTERM).
            frame (frame): The current stack frame as provided to signal handlers.
        """
        log.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
        if self.loop:
            for task in asyncio.all_tasks(self.loop):
                task.cancel()

    async def fetch_job(self):
        """
        Run a single fetch cycle that retrieves quotes from the configured feed and stores them.
        
        Performs a fetch using AsyncQuoteFetcher, persists any fetched quotes to the database, and logs the total number of quotes after the operation.
        """
        fetcher = AsyncQuoteFetcher(self.feed_url)
        # Note: For conditional GET, fetch last etag/last_modified from DB here
        # etag, last_modified = await fetcher.fetch_repo.get_last_successful_etag()  # Implement if needed
        await fetcher.fetch_and_store()  # Pass etag, last_modified if implemented
        total = await fetcher.get_total_quotes()
        log.info(f"Total quotes in database after fetch: {total}")

    async def scheduler_loop(self):
        """
        Run the scheduler loop to periodically execute quote fetch jobs until shutdown.
        
        Ensures database tables once at startup, then repeatedly runs fetch_job and sleeps for the configured interval. If the loop is cancelled it stops promptly; on other errors it logs the exception and sleeps before retrying.
        """
        fetcher = AsyncQuoteFetcher(self.feed_url)  # Temp instance for table creation
        await fetcher.ensure_tables()  # Ensure tables once at startup

        while self.running:
            try:
                log.info("Starting scheduled quote fetch job...")
                await self.fetch_job()
                log.info(f"Job completed. Sleeping for {self.interval_seconds} seconds...")
                await asyncio.sleep(self.interval_seconds)
            except asyncio.CancelledError:
                log.info("Scheduler loop cancelled, shutting down...")
                break
            except Exception as e:
                log.error(f"Error in scheduler loop: {e}", exc_info=True)
                await asyncio.sleep(self.interval_seconds)

    def run(self):
        """Start the async scheduler."""
        log.info(f"Starting Async Quote Fetcher Scheduler for {self.feed_url}")
        asyncio.run(self.scheduler_loop())
        log.info("Async scheduler stopped.")

