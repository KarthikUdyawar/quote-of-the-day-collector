# quote_fetcher.py
import feedparser
from typing import Any, Optional
import requests
from dateutil import parser as date_parser

from app.core.logging import log
from app.db.engine import engine
from app.services.quote import QuoteService
from app.services.feed_info import FeedInfoService
from app.services.fetch_history import FetchHistoryService
from app.db.models import Quote, FeedInfo, FetchHistory
from app.db.models import Base
from app.utils.string_utils import get_text


class AsyncQuoteFetcher:
    """
    Async version of the RSS Quote Fetcher using services.
    """

    def __init__(self, feed_url: str):
        """
        Create an AsyncQuoteFetcher bound to a specific RSS feed and initialize its services and HTTP timeout.

        Parameters:
            feed_url (str): The RSS feed URL this fetcher will request. The instance initializes QuoteService, FeedInfoService, and FetchHistoryService and sets an HTTP request timeout of 15 seconds.
        """
        self.feed_url = feed_url
        self.quote_repo = QuoteService()
        self.feed_repo = FeedInfoService()
        self.fetch_repo = FetchHistoryService()
        self.session_timeout = 15  # seconds for HTTP request timeout

    async def ensure_tables(self):
        """Ensure database tables exist. Call this once at application startup."""
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def fetch_and_store(
        self, etag: Optional[str] = None, last_modified: Optional[str] = None
    ) -> int:
        """
        Fetch the RSS feed using conditional GET, persist feed metadata and any new quote entries, and record the fetch in history.

        Parameters:
            etag (Optional[str]): ETag value to send as If-None-Match for conditional requests.
            last_modified (Optional[str]): Last-Modified value to send as If-Modified-Since for conditional requests.

        Returns:
            int: Number of new quotes added to the service.
        """
        log.info(
            f"Fetching feed from: {self.feed_url} (etag: {etag}, last_modified: {last_modified})"
        )
        new_quotes = 0
        duplicates = 0
        total_processed = 0
        status = "success"
        feed_record_id: Optional[int] = None

        try:
            # Fetch with timeout and conditional headers
            headers = {}
            if etag:
                headers["If-None-Match"] = etag
            if last_modified:
                headers["If-Modified-Since"] = last_modified

            response = requests.get(
                self.feed_url, headers=headers, timeout=self.session_timeout
            )
            response.raise_for_status()

            if response.status_code == 304:
                log.info("Feed not modified since last fetch")
                status = "not modified"
                await self.log_fetch(
                    None, new_quotes, duplicates, total_processed, status
                )
                return 0

            feed = feedparser.parse(response.content)

            # Improved bozo handling
            if feed.bozo:
                exc = feed.bozo_exception
                if isinstance(exc, feedparser.CharacterEncodingOverride):
                    log.info("Character encoding overridden – continuing to parse")
                elif isinstance(exc, feedparser.NonXMLContentType):
                    log.error("Feed served non-XML content type – likely broken")
                    status = "error: non-xml content"
                    await self.log_fetch(
                        None, new_quotes, duplicates, total_processed, status
                    )
                    return 0
                else:
                    log.error(f"Serious feed parse error: {exc}")
                    status = f"error: {type(exc).__name__}"
                    await self.log_fetch(
                        None, new_quotes, duplicates, total_processed, status
                    )
                    return 0

            if not feed.entries:
                log.warning("No entries found in feed")
                status = "warning: no entries"
                await self.log_fetch(
                    None, new_quotes, duplicates, total_processed, status
                )
                return 0

            # Store feed information
            feed_record = await self.store_feed_info(feed)
            feed_record_id = feed_record.id

            # Update etag and last_modified for next fetch (store in DB or cache)
            # Note: For full implementation, add etag and last_modified to FeedInfo model and update here

            # Store individual quotes
            for entry in feed.entries:
                total_processed += 1
                guid = get_text(entry.get("guid"))
                if not guid:
                    log.warning(
                        f"Entry missing guid, skipping: {entry.get('title', 'Unknown')}"
                    )
                    continue

                if await self.quote_repo.exists_by_guid(guid):
                    duplicates += 1
                    log.debug(
                        f"Duplicate quote skipped: {entry.get('title', 'Unknown')}"
                    )
                    continue

                if await self.store_quote(entry):
                    new_quotes += 1
                    log.info(f"New quote added: {entry.get('title', 'Unknown')}")

            await self.log_fetch(
                feed_record_id, new_quotes, duplicates, total_processed, status
            )
            log.info(
                f"Fetch completed - New: {new_quotes}, Duplicates: {duplicates}, Total: {total_processed}"
            )
            return new_quotes

        except requests.RequestException as e:
            log.error(f"Network error fetching feed: {str(e)}", exc_info=True)
            status = f"error: {str(e)}"
            await self.log_fetch(
                feed_record_id, new_quotes, duplicates, total_processed, status
            )
            raise
        except Exception as e:
            log.error(f"Error fetching feed: {str(e)}", exc_info=True)
            status = f"error: {str(e)}"
            await self.log_fetch(
                feed_record_id, new_quotes, duplicates, total_processed, status
            )
            raise

    async def store_feed_info(self, feed) -> FeedInfo:
        """
        Persist metadata extracted from a parsed feed.

        Parameters:
            feed: Parsed feed object (e.g., result from feedparser) whose `feed` mapping provides keys like "title", "link", "description", "language", and "updated".

        Returns:
            FeedInfo: The persisted FeedInfo instance containing the stored metadata; its database-generated `id` will be populated after storage.
        """
        feed_info = FeedInfo(
            title=feed.feed.get("title", ""),
            link=feed.feed.get("link", ""),
            description=feed.feed.get("description", ""),
            language=feed.feed.get("language", ""),
            last_build_date=feed.feed.get("updated", ""),
        )
        await self.feed_repo.add(feed_info)
        # Assuming add() commits and refreshes ID
        return feed_info

    async def store_quote(self, entry) -> bool:
        """
        Persist a single feed entry as a Quote record.

        Parses author from `entry["title"]`, quote text from `entry["description"]`, and GUID from `entry["guid"]`; parses `entry["published"]` into a datetime if present, and uses `entry["link"]` for the quote link. Requires author, quote text, and GUID to be present; if any are missing or storage fails, the entry is not stored.

        Parameters:
            entry (Mapping): A feedparser entry or mapping-like object with keys such as "title", "description", "guid", "published", and "link".

        Returns:
            bool: `True` if the quote was stored successfully, `False` otherwise.
        """
        author = get_text(entry.get("title"))
        quote_text = get_text(entry.get("description"))
        guid = get_text(entry.get("guid"))
        pub_date_str = entry.get("published", "")
        pub_date = None
        if pub_date_str:
            try:
                pub_date = date_parser.parse(pub_date_str)
            except ValueError:
                log.warning(f"Invalid pub_date format: {pub_date_str}")

        if not author or not quote_text or not guid:
            log.warning("Incomplete quote data, skipping")
            return False

        try:
            quote = Quote(
                author=author,
                quote_text=quote_text,
                guid=guid,
                pub_date=pub_date,  # Now datetime or None
                link=entry.get("link", ""),
            )
            await self.quote_repo.add(quote)
            return True
        except Exception as e:
            log.debug(f"Failed to store quote {guid}: {str(e)}")
            return False

    async def log_fetch(
        self,
        feed_id: Optional[int],
        quotes_added: int,
        duplicates_skipped: int,
        total_processed: int,
        status: str,
    ):
        """
        Record a feed fetch attempt and its outcome in the fetch history.

        Parameters:
            feed_id (Optional[int]): ID of the feed record or `None` if unknown.
            quotes_added (int): Number of new quotes persisted from this fetch.
            duplicates_skipped (int): Number of entries skipped because they were duplicates.
            total_processed (int): Total number of feed entries processed.
            status (str): Human-readable status or error description for the fetch.
        """
        fetch_record = FetchHistory(
            feed_id=feed_id,
            quotes_added=quotes_added,
            duplicates_skipped=duplicates_skipped,
            total_processed=total_processed,
            status=status,
        )
        await self.fetch_repo.add(fetch_record)

    async def get_total_quotes(self) -> int:
        """
        Get the total number of stored quotes.

        Returns:
            total (int): The total number of stored quotes.
        """
        return await self.quote_repo.total_count()

    async def get_recent_quotes(self, limit: int = 10):
        """
        Retrieve the most recent stored quotes.

        Parameters:
            limit (int): Maximum number of quotes to return (default 10).

        Returns:
            list: Stored Quote objects ordered from newest to oldest.
        """
        return await self.quote_repo.get_recent(limit)
