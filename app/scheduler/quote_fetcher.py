# quote_fetcher.py
import signal
import asyncio
from typing import Optional

from app.core.logging import log
from app.controllers.quote_fetcher import AsyncQuoteFetcher


class AsyncQuoteFetcherScheduler:
    """Fully async scheduler for periodic RSS fetching."""

    def __init__(self, feed_url: str, interval_hours: int = 24):
        """
        Create a scheduler configured to poll an RSS feed at a given interval and register OS signal handlers for graceful shutdown.

        Parameters:
            feed_url (str): RSS feed URL to fetch.
            interval_hours (int): Polling interval in hours; converted to seconds and stored on `self.interval_seconds`.

        Notes:
            This initializer also sets `self.running` to True, initializes `self.loop` to None, and registers handlers for SIGINT and SIGTERM that invoke `self.signal_handler`.
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
        Mark the scheduler for shutdown and cancel all asyncio tasks on the stored event loop.

        Sets the scheduler's running flag to False so the scheduler loop will exit and cancels every task associated with self.loop to expedite shutdown.

        Parameters:
            signum (int): Signal number received (e.g., SIGINT, SIGTERM).
            frame (frame): Current stack frame supplied by the signal handler.
        """
        log.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
        if self.loop:
            for task in asyncio.all_tasks(self.loop):
                task.cancel()

    async def fetch_job(self):
        """
        Run a single fetch cycle for the configured feed, store any fetched quotes, and update the stored total.

        Retrieves quotes from the configured RSS feed, persists any new or updated quotes to the database, and logs the resulting total number of quotes.
        """
        fetcher = AsyncQuoteFetcher(self.feed_url)
        # Note: For conditional GET, fetch last etag/last_modified from DB here
        # etag, last_modified = await fetcher.fetch_repo.get_last_successful_etag()  # Implement if needed
        await fetcher.fetch_and_store()  # Pass etag, last_modified if implemented
        total = await fetcher.get_total_quotes()
        log.info(f"Total quotes in database after fetch: {total}")

    async def scheduler_loop(self):
        """
        Periodically execute quote fetch jobs and sleep between runs until the scheduler is stopped.

        Ensures database tables exist once at startup. While running, starts a fetch job, logs completion, and sleeps for the configured interval. If cancelled, stops promptly; on other exceptions, logs the error and sleeps before retrying.
        """
        fetcher = AsyncQuoteFetcher(self.feed_url)  # Temp instance for table creation
        await fetcher.ensure_tables()  # Ensure tables once at startup

        while self.running:
            try:
                log.info("Starting scheduled quote fetch job...")
                await self.fetch_job()
                log.info(
                    f"Job completed. Sleeping for {self.interval_seconds} seconds..."
                )
                await asyncio.sleep(self.interval_seconds)
            except asyncio.CancelledError:
                log.info("Scheduler loop cancelled, shutting down...")
                break
            except Exception as e:
                log.error(f"Error in scheduler loop: {e}", exc_info=True)
                await asyncio.sleep(self.interval_seconds)

    def run(self):
        """
        Start the scheduler and run its main loop until shutdown.

        Blocks the current thread while the scheduler runs and returns when the scheduler stops (for example, in response to a signal or task cancellation).
        """
        log.info(f"Starting Async Quote Fetcher Scheduler for {self.feed_url}")
        asyncio.run(self.scheduler_loop())
        log.info("Async scheduler stopped.")
