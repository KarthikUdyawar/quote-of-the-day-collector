# telegram_uploader.py
import sqlite3
import logging
import sys
import os
from typing import Dict, List, Optional
import asyncio
from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError
import time
from dotenv import load_dotenv

load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/telegram_uploader.log"),
        logging.StreamHandler(sys.stdout),
    ],
)


class TelegramQuoteUploader:
    """Upload quote images to Telegram."""

    def __init__(
        self,
        db_path="quotes.db",
        bot_token: Optional[str] = None,
        chat_id: Optional[str] = None,
    ):
        """
        Initialize the Telegram uploader.

        Args:
            db_path: Path to SQLite database
            bot_token: Telegram bot token (or set TELEGRAM_BOT_TOKEN env var)
            chat_id: Your Telegram chat ID (or set TELEGRAM_CHAT_ID env var)
        """
        self.db_path = db_path

        # Get credentials from parameters or environment variables
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")

        if not self.bot_token:
            raise ValueError(
                "Bot token not provided. Set TELEGRAM_BOT_TOKEN environment variable "
                "or pass bot_token parameter"
            )

        if not self.chat_id:
            raise ValueError(
                "Chat ID not provided. Set TELEGRAM_CHAT_ID environment variable "
                "or pass chat_id parameter"
            )

        self.bot = Bot(token=self.bot_token)
        self.conn = None
        self.cursor = None

        logging.info(f"Telegram uploader initialized for chat ID: {self.chat_id}")

    def connect_db(self):
        """Connect to the database."""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self._create_upload_tracking_table()
        logging.info(f"Connected to database: {self.db_path}")

    def _create_upload_tracking_table(self):
        """Create table for tracking uploaded images."""
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS telegram_uploads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quote_id INTEGER NOT NULL,
                image_path TEXT NOT NULL,
                message_id INTEGER,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (quote_id) REFERENCES quotes(id),
                UNIQUE(quote_id)
            )
        """
        )

        self.cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_telegram_uploads_quote_id 
            ON telegram_uploads(quote_id)
        """
        )

        self.conn.commit()
        logging.info("Telegram upload tracking table ready")

    def get_images_to_upload(self, limit: Optional[int] = None) -> List[Dict]:
        """Get images that haven't been uploaded to Telegram yet."""
        query = """
            SELECT 
                q.id,
                q.author,
                q.quote_text,
                c.category,
                i.image_path
            FROM quotes q
            JOIN quote_classifications c ON q.id = c.quote_id
            JOIN quote_images i ON q.id = i.quote_id
            LEFT JOIN telegram_uploads t ON q.id = t.quote_id
            WHERE t.id IS NULL
            ORDER BY i.generated_at DESC
        """

        if limit:
            query += f" LIMIT {limit}"

        self.cursor.execute(query)

        results = []
        for row in self.cursor.fetchall():
            results.append(
                {
                    "id": row[0],
                    "author": row[1],
                    "quote": row[2],
                    "category": row[3],
                    "image_path": row[4],
                }
            )

        return results

    def format_caption(self, quote_text: str, author: str, category: str) -> str:
        """
        Format caption for Telegram message.
        
        Args:
            quote_text: The quote text
            author: Author name
            category: Quote category
            
        Returns:
            Formatted caption with markdown
        """
        # Escape special characters for Markdown V2
        def escape_markdown(text: str) -> str:
            # Characters that need escaping in MarkdownV2
            special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
            for char in special_chars:
                text = text.replace(char, f'\\{char}')
            return text
        
        # Format caption - quote in bold, author in italic
        escaped_quote = escape_markdown(quote_text)
        escaped_author = escape_markdown(author)
        escaped_category = escape_markdown(category)
        
        caption = f"*{escaped_quote}*\n\n"
        caption += f"\\~ _{escaped_author}_\n\n"
        caption += f"\\#{escaped_category}"
        
        return caption

    async def upload_image(
        self, image_path: str, caption: str, quote_id: int
    ) -> Optional[int]:
        """
        Upload image to Telegram.

        Args:
            image_path: Path to the image file
            caption: Caption for the image
            quote_id: Quote ID for tracking

        Returns:
            Message ID if successful, None otherwise
        """
        try:
            # Check if file exists
            if not os.path.exists(image_path):
                logging.error(f"Image file not found: {image_path}")
                return None

            # Open and send image
            with open(image_path, "rb") as image_file:
                message = await self.bot.send_photo(
                    chat_id=self.chat_id,
                    photo=image_file,
                    caption=caption,
                    parse_mode=ParseMode.MARKDOWN_V2,
                )

                logging.info(f"✓ Uploaded: {os.path.basename(image_path)}")
                return message.message_id

        except TelegramError as e:
            logging.error(f"Telegram error uploading {image_path}: {str(e)}")
            return None
        except Exception as e:
            logging.error(f"Error uploading {image_path}: {str(e)}", exc_info=True)
            return None

    def save_upload_record(
        self, quote_id: int, image_path: str, message_id: Optional[int]
    ) -> bool:
        """Save upload record to database."""
        try:
            self.cursor.execute(
                """
                INSERT OR REPLACE INTO telegram_uploads (quote_id, image_path, message_id)
                VALUES (?, ?, ?)
            """,
                (quote_id, image_path, message_id),
            )
            self.conn.commit()
            return True
        except Exception as e:
            logging.error(f"Error saving upload record: {str(e)}")
            return False

    async def upload_all(
        self, batch_size: Optional[int] = None, delay: float = 1.0
    ) -> Dict:
        """
        Upload all pending images to Telegram.

        Args:
            batch_size: Number of images to upload (None for all)
            delay: Delay in seconds between uploads (to avoid rate limits)

        Returns:
            Dictionary with upload statistics
        """
        images = self.get_images_to_upload(batch_size)
        total = len(images)

        if total == 0:
            logging.info("No images to upload")
            return {"total": 0, "success": 0, "failed": 0}

        logging.info(f"Uploading {total} images to Telegram")

        success_count = 0
        failed_count = 0

        for i, image_data in enumerate(images, 1):
            logging.info(f"Processing {i}/{total}: {image_data['author']}")

            # Format caption
            caption = self.format_caption(
                image_data["quote"], image_data["author"], image_data["category"]
            )

            # Upload image
            message_id = await self.upload_image(
                image_data["image_path"], caption, image_data["id"]
            )

            if message_id:
                # Save record
                if self.save_upload_record(
                    image_data["id"], image_data["image_path"], message_id
                ):
                    success_count += 1
                else:
                    failed_count += 1
                    logging.error(
                        f"✗ Failed to save upload record for quote {image_data['id']}"
                    )
            else:
                failed_count += 1
                logging.error(f"✗ Failed to upload image for quote {image_data['id']}")

            # Delay between uploads to avoid hitting rate limits
            if i < total:
                await asyncio.sleep(delay)

        stats = {"total": total, "success": success_count, "failed": failed_count}

        logging.info(f"Upload complete: {success_count} success, {failed_count} failed")
        return stats

    async def test_connection(self) -> bool:
        """Test Telegram bot connection."""
        try:
            bot_info = await self.bot.get_me()
            logging.info(f"Bot connected: @{bot_info.username} ({bot_info.first_name})")

            # Try to send a test message
            test_message = await self.bot.send_message(
                chat_id=self.chat_id,
                text="✅ Bot connection test successful!",
                parse_mode=ParseMode.MARKDOWN_V2,
            )
            logging.info(
                f"Test message sent successfully (ID: {test_message.message_id})"
            )
            return True

        except TelegramError as e:
            logging.error(f"Telegram connection error: {str(e)}")
            return False
        except Exception as e:
            logging.error(f"Connection test failed: {str(e)}", exc_info=True)
            return False

    def get_statistics(self) -> Dict:
        """Get upload statistics."""
        stats = {}

        # Total images
        self.cursor.execute("SELECT COUNT(*) FROM quote_images")
        stats["total_images"] = self.cursor.fetchone()[0]

        # Uploaded images
        self.cursor.execute("SELECT COUNT(*) FROM telegram_uploads")
        stats["uploaded_images"] = self.cursor.fetchone()[0]

        # Pending uploads
        stats["pending_uploads"] = stats["total_images"] - stats["uploaded_images"]

        # By category
        self.cursor.execute(
            """
            SELECT c.category, COUNT(t.id) as count
            FROM quote_classifications c
            JOIN quote_images i ON c.quote_id = i.quote_id
            LEFT JOIN telegram_uploads t ON i.quote_id = t.quote_id
            WHERE t.id IS NOT NULL
            GROUP BY c.category
            ORDER BY count DESC
        """
        )
        stats["by_category"] = dict(self.cursor.fetchall())

        # Recent uploads
        self.cursor.execute(
            """
            SELECT uploaded_at
            FROM telegram_uploads
            ORDER BY uploaded_at DESC
            LIMIT 1
        """
        )
        result = self.cursor.fetchone()
        stats["last_upload"] = result[0] if result else None

        return stats

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logging.info("Database connection closed")


def print_statistics(stats: Dict):
    """Pretty print statistics."""
    print("\n" + "=" * 70)
    print("TELEGRAM UPLOAD STATISTICS")
    print("=" * 70)
    print(f"Total Images:        {stats['total_images']}")
    print(f"Uploaded:            {stats['uploaded_images']}")
    print(f"Pending:             {stats['pending_uploads']}")

    if stats["last_upload"]:
        print(f"Last Upload:         {stats['last_upload']}")

    if stats["by_category"]:
        print("\n" + "-" * 70)
        print("UPLOADS BY CATEGORY")
        print("-" * 70)

        for category, count in stats["by_category"].items():
            bar = "█" * (count * 2) if count > 0 else ""
            print(f"{category:20} {count:3} {bar}")

    print("=" * 70 + "\n")


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Upload quote images to Telegram")
    parser.add_argument("--db", default="data/quotes.db", help="Database file path")
    parser.add_argument(
        "--bot-token", help="Telegram bot token (or set TELEGRAM_BOT_TOKEN env var)"
    )
    parser.add_argument(
        "--chat-id", help="Your Telegram chat ID (or set TELEGRAM_CHAT_ID env var)"
    )
    parser.add_argument("--batch-size", type=int, help="Number of images to upload")
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay between uploads in seconds (default: 1.0)",
    )
    parser.add_argument(
        "--action",
        choices=["upload", "test", "stats"],
        default="upload",
        help="Action to perform",
    )

    args = parser.parse_args()

    try:
        # Initialize uploader
        uploader = TelegramQuoteUploader(
            db_path=args.db, bot_token=args.bot_token, chat_id=args.chat_id
        )

        uploader.connect_db()

        if args.action == "test":
            # Test connection
            print("\nTesting Telegram connection...")
            success = await uploader.test_connection()

            if success:
                print("✅ Connection test successful!")
                print("You should have received a test message on Telegram.")
            else:
                print("❌ Connection test failed. Check logs for details.")
                sys.exit(1)

        elif args.action == "upload":
            # Upload images
            result = await uploader.upload_all(
                batch_size=args.batch_size, delay=args.delay
            )

            print("\n" + "=" * 70)
            print("UPLOAD RESULTS")
            print("=" * 70)
            print(f"Total Processed: {result['total']}")
            print(f"Success:         {result['success']}")
            print(f"Failed:          {result['failed']}")
            print("=" * 70 + "\n")

            # Show statistics
            stats = uploader.get_statistics()
            print_statistics(stats)

        elif args.action == "stats":
            # Show statistics only
            stats = uploader.get_statistics()
            print_statistics(stats)

        uploader.close()

    except ValueError as e:
        logging.error(str(e))
        print(f"\n❌ Error: {str(e)}")
        print("\nPlease provide bot token and chat ID either as:")
        print("  1. Command line arguments: --bot-token TOKEN --chat-id ID")
        print("  2. Environment variables: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
