import asyncio
from app.scheduler.quote_fetcher import AsyncQuoteFetcherScheduler
from app.services.quote_fetcher import AsyncQuoteFetcher


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Async RSS Quote Fetcher with Scheduler"
    )
    parser.add_argument("--mode", choices=["once", "schedule"], default="schedule")
    parser.add_argument("--interval", type=int, default=24)
    parser.add_argument(
        "--url", default="http://feeds.feedburner.com/quotationspage/qotd"
    )
    args = parser.parse_args()

    if args.mode == "once":
        fetcher = AsyncQuoteFetcher(args.url)
        asyncio.run(fetcher.ensure_tables())
        asyncio.run(fetcher.fetch_and_store())
    else:
        scheduler = AsyncQuoteFetcherScheduler(
            feed_url=args.url, interval_hours=args.interval
        )
        scheduler.run()


if __name__ == "__main__":
    main()
