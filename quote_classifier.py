# quote_classifier.py
import sqlite3
import requests
import json
import logging
import time
from typing import List, Dict, Optional
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/quote_classifier.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Quote Categories
CATEGORIES = {
    "Psychology": {
        "description": "Emotions, mindset, behavior, inner life",
        "keywords": ["Love", "Fear", "Happiness", "Anger", "Dreams", "Thoughts", "Sanity", "Stress", "Confidence"]
    },
    "Relationships": {
        "description": "Human connections and social interaction",
        "keywords": ["Family", "Marriage", "Friendship", "Parents", "Children", "Society", "Communication"]
    },
    "Ethics": {
        "description": "Morals, values, character",
        "keywords": ["Honesty", "Integrity", "Morality", "Duty", "Responsibility", "Kindness", "Justice"]
    },
    "Achievement": {
        "description": "Work, success, effort, ambition",
        "keywords": ["Success", "Failure", "Work", "Business", "Leadership", "Goals", "Talent"]
    },
    "Knowledge": {
        "description": "Learning, ideas, creativity, intellect",
        "keywords": ["Education", "Learning", "Science", "Writing", "Art", "Music", "Philosophy"]
    },
    "Spirituality": {
        "description": "Meaning, belief, existence",
        "keywords": ["God", "Faith", "Religion", "Life", "Death", "Destiny", "Truth"]
    },
    "Politics": {
        "description": "Power, governance, systems",
        "keywords": ["Government", "Democracy", "Laws", "Freedom", "Equality", "Authority"]
    },
    "Nature": {
        "description": "Natural world and time",
        "keywords": ["Nature", "Environment", "Seasons", "Weather", "Animals", "Time"]
    },
    "Technology": {
        "description": "Tools, innovation, modern systems",
        "keywords": ["Computers", "Internet", "Engineering", "Invention", "Media"]
    },
    "Lifestyle": {
        "description": "Daily life and experiences",
        "keywords": ["Money", "Health", "Food", "Travel", "Sports", "Entertainment"]
    }
}


class QuoteClassifier:
    """Classify quotes using Ollama LLM."""
    
    def __init__(self, db_path='quotes.db', ollama_host='http://localhost:11434', model='llama3.2:3b'):
        """
        Initialize the classifier.
        
        Args:
            db_path: Path to SQLite database
            ollama_host: Ollama API endpoint
            model: Ollama model to use (llama3.2:3b, mistral, etc.)
        """
        self.db_path = db_path
        self.ollama_host = ollama_host.rstrip('/')
        self.model = model
        self.conn = None
        self.cursor = None
        
        # Test Ollama connection
        self._test_ollama_connection()
    
    def _test_ollama_connection(self):
        """Test connection to Ollama API."""
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=5)
            if response.status_code == 200:
                logging.info(f"Successfully connected to Ollama at {self.ollama_host}")
                models = response.json().get('models', [])
                logging.info(f"Available models: {[m['name'] for m in models]}")
            else:
                logging.warning(f"Ollama API returned status {response.status_code}")
        except Exception as e:
            logging.error(f"Failed to connect to Ollama: {str(e)}")
            logging.error("Make sure Ollama is running and accessible")
            raise
    
    def connect_db(self):
        """Connect to the database."""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self._create_classification_table()
        logging.info(f"Connected to database: {self.db_path}")
    
    def _create_classification_table(self):
        """Create table for storing classifications."""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS quote_classifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quote_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                confidence REAL,
                reasoning TEXT,
                classified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (quote_id) REFERENCES quotes(id),
                UNIQUE(quote_id)
            )
        ''')
        
        # Create index for faster lookups
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_classifications_quote_id 
            ON quote_classifications(quote_id)
        ''')
        
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_classifications_category 
            ON quote_classifications(category)
        ''')
        
        self.conn.commit()
        logging.info("Classification table ready")
    
    def _build_classification_prompt(self, quote_text: str, author: str) -> str:
        """Build the prompt for Ollama."""
        categories_text = "\n".join([
            f"{i}. {cat}: {info['description']}" 
            for i, (cat, info) in enumerate(CATEGORIES.items(), 1)
        ])
        
        prompt = f"""You are a quote classification expert. Analyze the following quote and classify it into ONE of these categories:

{categories_text}

Quote: "{quote_text}"
Author: {author}

Respond ONLY in this exact JSON format (no other text):
{{
    "category": "Category Name",
    "confidence": 0.95,
    "reasoning": "Brief explanation of why this category fits best"
}}

Choose the single most relevant category. Confidence should be between 0 and 1."""
        
        return prompt
    
    def classify_with_ollama(self, quote_text: str, author: str) -> Optional[Dict]:
        """
        Classify a quote using Ollama.
        
        Args:
            quote_text: The quote text
            author: The quote author
            
        Returns:
            Dict with category, confidence, and reasoning
        """
        prompt = self._build_classification_prompt(quote_text, author)
        
        try:
            response = requests.post(
                f"{self.ollama_host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.3,  # Lower temperature for more consistent results
                },
                timeout=60
            )
            
            if response.status_code != 200:
                logging.error(f"Ollama API error: {response.status_code}")
                return None
            
            result = response.json()
            response_text = result.get('response', '').strip()
            
            # Parse JSON response
            # Sometimes LLMs add markdown code blocks, so clean it
            response_text = response_text.replace('```json', '').replace('```', '').strip()
            
            classification = json.loads(response_text)
            
            # Validate the response
            category = classification.get('category')
            if category not in CATEGORIES:
                logging.warning(f"Invalid category '{category}', defaulting to closest match")
                # Try to find closest match
                category = self._find_closest_category(category)
                classification['category'] = category
            
            return classification
            
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse Ollama response as JSON: {str(e)}")
            logging.error(f"Response was: {response_text[:200]}")
            return None
        except Exception as e:
            logging.error(f"Error classifying quote: {str(e)}")
            return None
    
    def _find_closest_category(self, invalid_category: str) -> str:
        """Find the closest matching category name."""
        invalid_lower = invalid_category.lower()
        
        for category in CATEGORIES.keys():
            if category.lower() in invalid_lower or invalid_lower in category.lower():
                return category
        
        # Default fallback
        return "Knowledge"
    
    def get_unclassified_quotes(self, limit: Optional[int] = None) -> List[tuple]:
        """Get quotes that haven't been classified yet."""
        query = '''
            SELECT q.id, q.author, q.quote_text
            FROM quotes q
            LEFT JOIN quote_classifications c ON q.id = c.quote_id
            WHERE c.id IS NULL
            ORDER BY q.id
        '''
        
        if limit:
            query += f' LIMIT {limit}'
        
        self.cursor.execute(query)
        return self.cursor.fetchall()
    
    def save_classification(self, quote_id: int, category: str, confidence: float, reasoning: str):
        """Save classification to database."""
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO quote_classifications 
                (quote_id, category, confidence, reasoning)
                VALUES (?, ?, ?, ?)
            ''', (quote_id, category, confidence, reasoning))
            self.conn.commit()
            return True
        except Exception as e:
            logging.error(f"Error saving classification: {str(e)}")
            return False
    
    def classify_all_quotes(self, batch_size: int = 10, delay: float = 1.0):
        """
        Classify all unclassified quotes.
        
        Args:
            batch_size: Number of quotes to classify in one run
            delay: Delay in seconds between classifications to avoid overwhelming Ollama
        """
        unclassified = self.get_unclassified_quotes(batch_size)
        total = len(unclassified)
        
        if total == 0:
            logging.info("No unclassified quotes found")
            return
        
        logging.info(f"Found {total} unclassified quotes to process")
        
        for i, (quote_id, author, quote_text) in enumerate(unclassified, 1):
            logging.info(f"Processing {i}/{total}: {author}")
            logging.info(f"Quote: {quote_text[:100]}...")
            
            classification = self.classify_with_ollama(quote_text, author)
            
            if classification:
                success = self.save_classification(
                    quote_id,
                    classification['category'],
                    classification.get('confidence', 0.0),
                    classification.get('reasoning', '')
                )
                
                if success:
                    logging.info(f"✓ Classified as '{classification['category']}' "
                               f"(confidence: {classification.get('confidence', 0):.2f})")
                    logging.info(f"  Reasoning: {classification.get('reasoning', '')}")
                else:
                    logging.error(f"✗ Failed to save classification")
            else:
                logging.error(f"✗ Failed to classify quote")
            
            # Delay between requests
            if i < total:
                time.sleep(delay)
        
        logging.info(f"Classification complete: {total} quotes processed")
    
    def get_statistics(self) -> Dict:
        """Get classification statistics."""
        stats = {}
        
        # Total quotes
        self.cursor.execute('SELECT COUNT(*) FROM quotes')
        stats['total_quotes'] = self.cursor.fetchone()[0]
        
        # Classified quotes
        self.cursor.execute('SELECT COUNT(*) FROM quote_classifications')
        stats['classified_quotes'] = self.cursor.fetchone()[0]
        
        # Unclassified quotes
        stats['unclassified_quotes'] = stats['total_quotes'] - stats['classified_quotes']
        
        # By category
        self.cursor.execute('''
            SELECT category, COUNT(*) as count
            FROM quote_classifications
            GROUP BY category
            ORDER BY count DESC
        ''')
        stats['by_category'] = dict(self.cursor.fetchall())
        
        # Average confidence
        self.cursor.execute('SELECT AVG(confidence) FROM quote_classifications')
        avg_conf = self.cursor.fetchone()[0]
        stats['average_confidence'] = round(avg_conf, 3) if avg_conf else 0
        
        return stats
    
    def get_quotes_by_category(self, category: str, limit: int = 10) -> List[Dict]:
        """Get quotes for a specific category."""
        self.cursor.execute('''
            SELECT 
                q.id, q.author, q.quote_text, q.pub_date,
                c.category, c.confidence, c.reasoning
            FROM quotes q
            JOIN quote_classifications c ON q.id = c.quote_id
            WHERE c.category = ?
            ORDER BY c.confidence DESC, q.pub_date DESC
            LIMIT ?
        ''', (category, limit))
        
        results = []
        for row in self.cursor.fetchall():
            results.append({
                'id': row[0],
                'author': row[1],
                'quote': row[2],
                'pub_date': row[3],
                'category': row[4],
                'confidence': row[5],
                'reasoning': row[6]
            })
        
        return results
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logging.info("Database connection closed")


def print_statistics(stats: Dict):
    """Pretty print statistics."""
    print("\n" + "=" * 70)
    print("CLASSIFICATION STATISTICS")
    print("=" * 70)
    print(f"Total Quotes:        {stats['total_quotes']}")
    print(f"Classified:          {stats['classified_quotes']}")
    print(f"Unclassified:        {stats['unclassified_quotes']}")
    print(f"Average Confidence:  {stats['average_confidence']:.2%}")
    
    print("\n" + "-" * 70)
    print("QUOTES BY CATEGORY")
    print("-" * 70)
    
    for category in CATEGORIES.keys():
        count = stats['by_category'].get(category, 0)
        bar = "█" * (count * 2) if count > 0 else ""
        print(f"{category:20} {count:3} {bar}")
    
    print("=" * 70 + "\n")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Classify quotes using Ollama')
    parser.add_argument('--db', default='data/quotes.db', help='Database file path')
    parser.add_argument('--ollama-host', default='http://localhost:11434', 
                        help='Ollama API host')
    parser.add_argument('--model', default='llama3.2:3b', 
                        help='Ollama model to use (llama3.2:3b, mistral, etc.)')
    parser.add_argument('--batch-size', type=int, default=10,
                        help='Number of quotes to classify per run')
    parser.add_argument('--delay', type=float, default=1.0,
                        help='Delay between classifications (seconds)')
    parser.add_argument('--action', choices=['classify', 'stats', 'view'], 
                        default='classify',
                        help='Action to perform')
    parser.add_argument('--category', type=str,
                        help='Category to view (use with --action view)')
    
    args = parser.parse_args()
    
    # Initialize classifier
    classifier = QuoteClassifier(
        db_path=args.db,
        ollama_host=args.ollama_host,
        model=args.model
    )
    
    try:
        classifier.connect_db()
        
        if args.action == 'classify':
            # Classify unclassified quotes
            classifier.classify_all_quotes(
                batch_size=args.batch_size,
                delay=args.delay
            )
            
            # Show statistics after classification
            stats = classifier.get_statistics()
            print_statistics(stats)
            
        elif args.action == 'stats':
            # Show statistics only
            stats = classifier.get_statistics()
            print_statistics(stats)
            
        elif args.action == 'view':
            # View quotes by category
            if not args.category:
                print("Available categories:")
                for i, cat in enumerate(CATEGORIES.keys(), 1):
                    print(f"{i}. {cat}")
                print("\nUse --category <name> to view quotes")
            else:
                quotes = classifier.get_quotes_by_category(args.category, limit=10)
                
                print("\n" + "=" * 70)
                print(f"QUOTES IN CATEGORY: {args.category}")
                print("=" * 70)
                
                for quote in quotes:
                    print(f"\n{quote['author']}")
                    print(f'"{quote["quote"]}"')
                    print(f"Confidence: {quote['confidence']:.2%}")
                    print(f"Reasoning: {quote['reasoning']}")
                    print("-" * 70)
                
                if not quotes:
                    print(f"No quotes found in category '{args.category}'")
    
    finally:
        classifier.close()


if __name__ == '__main__':
    main()