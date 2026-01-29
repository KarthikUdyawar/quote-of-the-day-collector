import asyncio
from app.scheduler.quote_fetcher import AsyncQuoteFetcherScheduler
from app.controllers.quote_fetcher import AsyncQuoteFetcher


async def run_once(url: str):
    fetcher = AsyncQuoteFetcher(url)
    await fetcher.ensure_tables()
    await fetcher.fetch_and_store()


def main():
    """
    Command-line entry point for the Async RSS Quote Fetcher.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Async RSS Quote Fetcher with Scheduler"
    )
    parser.add_argument("--mode", choices=["once", "schedule"], default="once")
    parser.add_argument("--interval", type=int, default=24)
    parser.add_argument(
        "--url", default="http://feeds.feedburner.com/quotationspage/qotd"
    )
    args = parser.parse_args()

    try:
        if args.mode == "once":
            asyncio.run(run_once(args.url))
        else:
            scheduler = AsyncQuoteFetcherScheduler(
                feed_url=args.url,
                interval_hours=args.interval
            )
            scheduler.run()

    except KeyboardInterrupt:
        print("\n👋 Shutdown requested. Exiting cleanly.")


if __name__ == "__main__":
    main()
