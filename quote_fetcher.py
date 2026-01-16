# quote_fetcher.py

import sqlite3
import feedparser
import logging
import sys
import time
import schedule
import signal

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/quote_fetcher.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class QuoteRSSStorage:
    def __init__(self, db_name='quotes.db'):
        """Initialize database connection and create tables if they don't exist."""
        self.db_name = db_name
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()
        logging.info(f"Database initialized: {db_name}")
    
    def create_tables(self):
        """Create the necessary tables for storing RSS feed data."""
        # Channel/Feed information table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS feed_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                link TEXT,
                description TEXT,
                language TEXT,
                last_build_date TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Quotes/Items table with UNIQUE constraint on guid to prevent duplicates
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS quotes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                author TEXT NOT NULL,
                quote_text TEXT NOT NULL,
                guid TEXT UNIQUE NOT NULL,
                pub_date TEXT,
                link TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create index on guid for faster duplicate checking
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_quotes_guid ON quotes(guid)
        ''')
        
        # Create index on author for faster searches
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_quotes_author ON quotes(author)
        ''')
        
        # Fetch history table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS fetch_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fetch_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                quotes_added INTEGER,
                duplicates_skipped INTEGER,
                total_processed INTEGER,
                status TEXT
            )
        ''')
        
        self.conn.commit()
    
    def quote_exists(self, guid):
        """Check if a quote with given guid already exists."""
        self.cursor.execute('SELECT COUNT(*) FROM quotes WHERE guid = ?', (guid,))
        count = self.cursor.fetchone()[0]
        return count > 0
    
    def fetch_and_store(self, feed_url):
        """Fetch RSS feed from URL and store in database."""
        logging.info(f"Fetching feed from: {feed_url}")
        
        new_quotes = 0
        duplicates = 0
        total_processed = 0
        
        try:
            feed = feedparser.parse(feed_url)
            
            if feed.bozo:
                logging.warning(f"Feed parsing warning: {feed.bozo_exception}")
            
            if not feed.entries:
                logging.warning("No entries found in feed")
                self.log_fetch(0, 0, 0, 'warning: no entries')
                return 0
            
            # Store feed information
            self.store_feed_info(feed)
            
            # Store individual quotes
            for entry in feed.entries:
                total_processed += 1
                guid = entry.get('guid', '')
                
                if not guid:
                    logging.warning(f"Entry missing guid, skipping: {entry.get('title', 'Unknown')}")
                    continue
                
                # Check for duplicates before attempting insert
                if self.quote_exists(guid):
                    duplicates += 1
                    logging.debug(f"Duplicate quote skipped: {entry.get('title', 'Unknown')}")
                    continue
                
                if self.store_quote(entry):
                    new_quotes += 1
                    logging.info(f"New quote added: {entry.get('title', 'Unknown')}")
            
            # Log fetch history
            self.log_fetch(new_quotes, duplicates, total_processed, 'success')
            
            logging.info(f"Fetch completed - New: {new_quotes}, Duplicates: {duplicates}, Total: {total_processed}")
            return new_quotes
            
        except Exception as e:
            logging.error(f"Error fetching feed: {str(e)}", exc_info=True)
            self.log_fetch(new_quotes, duplicates, total_processed, f'error: {str(e)}')
            raise
    
    def store_feed_info(self, feed):
        """Store or update feed metadata."""
        self.cursor.execute('''
            INSERT INTO feed_info (title, link, description, language, last_build_date)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            feed.feed.get('title', ''),
            feed.feed.get('link', ''),
            feed.feed.get('description', ''),
            feed.feed.get('language', ''),
            feed.feed.get('updated', '')
        ))
        self.conn.commit()
    
    def store_quote(self, entry):
        """Store individual quote. Returns True if new quote was added."""
        try:
            author = entry.get('title', '').strip()
            quote_text = entry.get('description', '').strip()
            guid = entry.get('guid', '').strip()
            
            if not author or not quote_text or not guid:
                logging.warning("Incomplete quote data, skipping")
                return False
            
            self.cursor.execute('''
                INSERT INTO quotes (author, quote_text, guid, pub_date, link)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                author,
                quote_text,
                guid,
                entry.get('published', ''),
                entry.get('link', '')
            ))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError as e:
            # Quote already exists (duplicate guid)
            logging.debug(f"Duplicate quote (IntegrityError): {entry.get('title', 'Unknown')}")
            return False
        except Exception as e:
            logging.error(f"Error storing quote: {str(e)}", exc_info=True)
            return False
    
    def log_fetch(self, quotes_added, duplicates_skipped, total_processed, status):
        """Log fetch attempt in history."""
        self.cursor.execute('''
            INSERT INTO fetch_history (quotes_added, duplicates_skipped, total_processed, status)
            VALUES (?, ?, ?, ?)
        ''', (quotes_added, duplicates_skipped, total_processed, status))
        self.conn.commit()
    
    def get_all_quotes(self):
        """Retrieve all quotes from database."""
        self.cursor.execute('SELECT * FROM quotes ORDER BY pub_date DESC')
        return self.cursor.fetchall()
    
    def get_quotes_by_author(self, author):
        """Retrieve quotes by specific author."""
        self.cursor.execute('SELECT * FROM quotes WHERE author = ? ORDER BY pub_date DESC', (author,))
        return self.cursor.fetchall()
    
    def search_quotes(self, keyword):
        """Search quotes containing specific keyword."""
        self.cursor.execute(
            'SELECT * FROM quotes WHERE quote_text LIKE ? ORDER BY pub_date DESC',
            (f'%{keyword}%',)
        )
        return self.cursor.fetchall()
    
    def get_recent_quotes(self, limit=10):
        """Get most recent quotes."""
        self.cursor.execute('SELECT * FROM quotes ORDER BY pub_date DESC LIMIT ?', (limit,))
        return self.cursor.fetchall()
    
    def get_fetch_history(self, limit=10):
        """Get recent fetch history."""
        self.cursor.execute('SELECT * FROM fetch_history ORDER BY fetch_date DESC LIMIT ?', (limit,))
        return self.cursor.fetchall()
    
    def get_total_quotes(self):
        """Get total number of quotes in database."""
        self.cursor.execute('SELECT COUNT(*) FROM quotes')
        return self.cursor.fetchone()[0]
    
    def close(self):
        """Close database connection."""
        self.conn.close()
        logging.info("Database connection closed")


class QuoteFetcherScheduler:
    """Scheduler class to manage periodic RSS feed fetching."""
    
    def __init__(self, feed_url, db_path='quotes.db', interval_hours=24):
        self.feed_url = feed_url
        self.db_path = db_path
        self.interval_hours = interval_hours
        self.running = True
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logging.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    def fetch_job(self):
        """Job to be executed on schedule."""
        logging.info("=" * 60)
        logging.info("Starting scheduled quote fetch job")
        logging.info("=" * 60)
        
        storage = QuoteRSSStorage(self.db_path)
        
        try:
            new_quotes = storage.fetch_and_store(self.feed_url)
            total_quotes = storage.get_total_quotes()
            logging.info(f"Job completed. Total quotes in database: {total_quotes}")
            
        except Exception as e:
            logging.error(f"Job failed: {str(e)}", exc_info=True)
        
        finally:
            storage.close()
        
        logging.info("=" * 60)
    
    def run(self):
        """Start the scheduler."""
        logging.info(f"Starting Quote Fetcher Scheduler")
        logging.info(f"Feed URL: {self.feed_url}")
        logging.info(f"Database: {self.db_path}")
        logging.info(f"Interval: Every {self.interval_hours} hours")
        
        # Run immediately on startup
        logging.info("Running initial fetch...")
        self.fetch_job()
        
        # Schedule the job
        schedule.every(self.interval_hours).hours.do(self.fetch_job)
        
        # Alternative scheduling options (uncomment as needed):
        # schedule.every().day.at("09:00").do(self.fetch_job)  # Daily at 9 AM
        # schedule.every().monday.at("10:00").do(self.fetch_job)  # Every Monday at 10 AM
        # schedule.every(30).minutes.do(self.fetch_job)  # Every 30 minutes (for testing)
        
        logging.info(f"Scheduler started. Next run in {self.interval_hours} hours.")
        logging.info("Press Ctrl+C to stop")
        
        # Keep the scheduler running
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
        
        logging.info("Scheduler stopped")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='RSS Quote Fetcher with Built-in Scheduler')
    parser.add_argument('--mode', choices=['once', 'schedule'], default='schedule',
                        help='Run once or start scheduler (default: schedule)')
    parser.add_argument('--interval', type=int, default=24,
                        help='Fetch interval in hours (default: 24)')
    parser.add_argument('--db', default='data/quotes.db',
                        help='Database file path (default: data/quotes.db)')
    parser.add_argument('--url', default='http://feeds.feedburner.com/quotationspage/qotd',
                        help='RSS feed URL')
    
    args = parser.parse_args()
    
    if args.mode == 'once':
        # Run once and exit
        logging.info("Running in single-fetch mode")
        storage = QuoteRSSStorage(args.db)
        try:
            storage.fetch_and_store(args.url)
            
            # Display statistics
            print("\n" + "=" * 60)
            print("DATABASE STATISTICS")
            print("=" * 60)
            print(f"Total quotes: {storage.get_total_quotes()}")
            
            print("\n" + "=" * 60)
            print("RECENT QUOTES")
            print("=" * 60)
            recent = storage.get_recent_quotes(5)
            for quote in recent:
                print(f"\nAuthor: {quote[1]}")
                print(f"Quote: {quote[2]}")
                print(f"Date: {quote[4]}")
                print("-" * 60)
            
            print("\n" + "=" * 60)
            print("FETCH HISTORY")
            print("=" * 60)
            history = storage.get_fetch_history(5)
            for record in history:
                print(f"{record[1]} | New: {record[2]} | Duplicates: {record[3]} | Total: {record[4]} | Status: {record[5]}")
            
        finally:
            storage.close()
    
    else:
        # Start scheduler
        scheduler = QuoteFetcherScheduler(
            feed_url=args.url,
            db_path=args.db,
            interval_hours=args.interval
        )
        scheduler.run()


if __name__ == '__main__':
    main()