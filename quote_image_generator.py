# quote_image_generator.py
import sqlite3
from PIL import Image, ImageDraw, ImageFont
import textwrap
import os
from datetime import datetime
import logging
import sys
from typing import Dict, List, Tuple, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/quote_image_generator.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Category color scheme
CATEGORY_COLORS = {
    "Psychology": {"bg": "#7B61FF", "text": "#FFFFFF"},
    "Relationships": {"bg": "#E91E63", "text": "#FFFFFF"},
    "Ethics": {"bg": "#2E7D32", "text": "#FFFFFF"},
    "Achievement": {"bg": "#FB8C00", "text": "#1F1F1F"},
    "Knowledge": {"bg": "#1E88E5", "text": "#FFFFFF"},
    "Spirituality": {"bg": "#3F51B5", "text": "#FFFFFF"},
    "Politics": {"bg": "#D32F2F", "text": "#FFFFFF"},
    "Nature": {"bg": "#4CAF50", "text": "#1B1B1B"},
    "Technology": {"bg": "#00ACC1", "text": "#00363A"},
    "Lifestyle": {"bg": "#00897B", "text": "#FFFFFF"}
}

# Image specifications
IMAGE_SIZE = (1080, 1080)
MARGIN = 80
CONTENT_WIDTH = IMAGE_SIZE[0] - (MARGIN * 2)
CONTENT_HEIGHT = IMAGE_SIZE[1] - (MARGIN * 2)

# Font sizes
MAX_QUOTE_FONT_SIZE = 72
MIN_QUOTE_FONT_SIZE = 36
AUTHOR_FONT_SIZE_RATIO = 0.7  # 70% of quote font size
BADGE_FONT_SIZE = 24

# Text settings
LINE_HEIGHT_RATIO = 1.4
MAX_CHARS_PER_LINE = 40


class QuoteImageGenerator:
    """Generate Instagram-ready images from classified quotes."""
    
    def __init__(self, db_path='quotes.db', output_base_dir='images'):
        """
        Initialize the image generator.
        
        Args:
            db_path: Path to SQLite database
            output_base_dir: Base directory for generated images
        """
        self.db_path = db_path
        self.output_base_dir = output_base_dir
        self.conn = None
        self.cursor = None
        
        # Create output directory
        os.makedirs(output_base_dir, exist_ok=True)
    
    def connect_db(self):
        """Connect to the database."""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self._create_image_tracking_table()
        logging.info(f"Connected to database: {self.db_path}")
    
    def _create_image_tracking_table(self):
        """Create table for tracking generated images."""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS quote_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quote_id INTEGER NOT NULL,
                image_path TEXT NOT NULL,
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (quote_id) REFERENCES quotes(id),
                UNIQUE(quote_id)
            )
        ''')
        
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_images_quote_id 
            ON quote_images(quote_id)
        ''')
        
        self.conn.commit()
        logging.info("Image tracking table ready")
    
    def hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def get_font(self, size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
        """
        Get font with fallback options.
        
        Args:
            size: Font size
            bold: Whether to use bold font
            
        Returns:
            ImageFont object
        """
        # Try different font paths for different systems
        font_paths = [
            # Linux
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            # macOS
            "/System/Library/Fonts/Helvetica.ttc",
            "/Library/Fonts/Arial.ttf",
            # Windows
            "C:\\Windows\\Fonts\\arial.ttf",
            "C:\\Windows\\Fonts\\calibri.ttf",
        ]
        
        for font_path in font_paths:
            try:
                return ImageFont.truetype(font_path, size)
            except:
                continue
        
        # Fallback to default font
        logging.warning(f"Could not load custom font, using default")
        return ImageFont.load_default()
    
    def wrap_text(self, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
        """
        Wrap text to fit within max_width, breaking at word boundaries.
        
        Args:
            text: Text to wrap
            font: Font to use for measuring
            max_width: Maximum width in pixels
            
        Returns:
            List of wrapped lines
        """
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            # Test if adding this word exceeds max width
            test_line = ' '.join(current_line + [word])
            bbox = font.getbbox(test_line)
            text_width = bbox[2] - bbox[0]
            
            if text_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    # Single word is too long, force it
                    lines.append(word)
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def calculate_optimal_font_size(self, quote_text: str, author: str) -> Tuple[int, int]:
        """
        Calculate optimal font size based on text length.
        
        Args:
            quote_text: The quote text
            author: Author name
            
        Returns:
            Tuple of (quote_font_size, author_font_size)
        """
        text_length = len(quote_text)
        
        # Dynamic font size based on length
        if text_length < 50:
            quote_size = MAX_QUOTE_FONT_SIZE
        elif text_length < 100:
            quote_size = 64
        elif text_length < 150:
            quote_size = 56
        elif text_length < 200:
            quote_size = 48
        elif text_length < 300:
            quote_size = 42
        else:
            quote_size = MIN_QUOTE_FONT_SIZE
        
        author_size = int(quote_size * AUTHOR_FONT_SIZE_RATIO)
        
        return quote_size, author_size
    
    def create_quote_image(
        self, 
        quote_text: str, 
        author: str, 
        category: str,
        output_path: str
    ) -> bool:
        """
        Create an Instagram-ready quote image.
        
        Args:
            quote_text: The quote text
            author: Author name
            category: Quote category
            output_path: Path to save the image
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get colors for category
            colors = CATEGORY_COLORS.get(category, CATEGORY_COLORS["Knowledge"])
            bg_color = self.hex_to_rgb(colors["bg"])
            text_color = self.hex_to_rgb(colors["text"])
            
            # Create image with background color
            img = Image.new('RGB', IMAGE_SIZE, bg_color)
            draw = ImageDraw.Draw(img)
            
            # Calculate font sizes
            quote_font_size, author_font_size = self.calculate_optimal_font_size(quote_text, author)
            
            # Load fonts
            quote_font = self.get_font(quote_font_size, bold=True)
            author_font = self.get_font(author_font_size, bold=False)
            badge_font = self.get_font(BADGE_FONT_SIZE, bold=True)
            
            # Draw category badge (top-left corner)
            badge_text = category.upper()
            badge_bbox = badge_font.getbbox(badge_text)
            badge_width = badge_bbox[2] - badge_bbox[0]
            badge_height = badge_bbox[3] - badge_bbox[1]
            
            badge_padding = 15
            badge_x = MARGIN
            badge_y = MARGIN
            
            # Draw semi-transparent badge background
            badge_bg_color = tuple(int(c * 0.8) for c in text_color)
            draw.rectangle(
                [
                    badge_x - badge_padding,
                    badge_y - badge_padding,
                    badge_x + badge_width + badge_padding,
                    badge_y + badge_height + badge_padding
                ],
                fill=badge_bg_color,
                outline=None
            )
            
            draw.text(
                (badge_x, badge_y),
                badge_text,
                font=badge_font,
                fill=bg_color
            )
            
            # Add decorative opening quote
            decorative_quote = '❝'
            deco_font = self.get_font(quote_font_size + 20, bold=True)
            
            # Wrap quote text
            wrapped_lines = self.wrap_text(quote_text, quote_font, CONTENT_WIDTH - 100)
            
            # Calculate total text height for centering
            line_height = int(quote_font_size * LINE_HEIGHT_RATIO)
            quote_block_height = len(wrapped_lines) * line_height
            
            # Author text
            author_text = f"~ {author}"
            author_bbox = author_font.getbbox(author_text)
            author_height = author_bbox[3] - author_bbox[1]
            
            # Space between quote and author
            quote_author_spacing = 60
            
            # Total content height
            total_content_height = quote_block_height + quote_author_spacing + author_height
            
            # Starting Y position (centered)
            start_y = (IMAGE_SIZE[1] - total_content_height) // 2
            
            # Draw quote text
            current_y = start_y
            for line in wrapped_lines:
                # Get text dimensions for centering
                bbox = quote_font.getbbox(line)
                text_width = bbox[2] - bbox[0]
                text_x = (IMAGE_SIZE[0] - text_width) // 2
                
                draw.text(
                    (text_x, current_y),
                    line,
                    font=quote_font,
                    fill=text_color
                )
                current_y += line_height
            
            # Draw author name
            author_bbox = author_font.getbbox(author_text)
            author_width = author_bbox[2] - author_bbox[0]
            author_x = (IMAGE_SIZE[0] - author_width) // 2
            author_y = start_y + quote_block_height + quote_author_spacing
            
            draw.text(
                (author_x, author_y),
                author_text,
                font=author_font,
                fill=text_color
            )
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save image
            img.save(output_path, 'PNG', quality=95, optimize=True)
            logging.info(f"Image saved: {output_path}")
            
            return True
            
        except Exception as e:
            logging.error(f"Error creating image: {str(e)}", exc_info=True)
            return False
    
    def get_quotes_needing_images(self, limit: Optional[int] = None) -> List[Dict]:
        """Get classified quotes that don't have images yet."""
        query = '''
            SELECT 
                q.id,
                q.author,
                q.quote_text,
                q.pub_date,
                c.category
            FROM quotes q
            JOIN quote_classifications c ON q.id = c.quote_id
            LEFT JOIN quote_images i ON q.id = i.quote_id
            WHERE i.id IS NULL
            ORDER BY q.pub_date DESC
        '''
        
        if limit:
            query += f' LIMIT {limit}'
        
        self.cursor.execute(query)
        
        results = []
        for row in self.cursor.fetchall():
            results.append({
                'id': row[0],
                'author': row[1],
                'quote': row[2],
                'pub_date': row[3],
                'category': row[4]
            })
        
        return results
    
    def save_image_record(self, quote_id: int, image_path: str) -> bool:
        """Save image generation record to database."""
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO quote_images (quote_id, image_path)
                VALUES (?, ?)
            ''', (quote_id, image_path))
            self.conn.commit()
            return True
        except Exception as e:
            logging.error(f"Error saving image record: {str(e)}")
            return False
    
    def generate_image_path(self, quote_id: int, author: str, category: str, pub_date: str) -> str:
        """
        Generate file path for the image.
        Format: images/<category>/<date>/quote_<id>_<author>.png
        
        Args:
            quote_id: Quote ID
            author: Author name
            category: Quote category
            pub_date: Publication date
            
        Returns:
            Full path for the image file
        """
        # Parse date - handle different formats
        try:
            # Try parsing common RSS date formats
            for fmt in ['%a, %d %b %Y %H:%M:%S %Z', '%Y-%m-%d', '%d %b %Y']:
                try:
                    date_obj = datetime.strptime(pub_date, fmt)
                    break
                except:
                    continue
            else:
                # If all parsing fails, use current date
                date_obj = datetime.now()
        except:
            date_obj = datetime.now()
        
        date_str = date_obj.strftime('%d-%m-%Y')
        
        # Sanitize author name for filename
        safe_author = "".join(c for c in author if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_author = safe_author.replace(' ', '_')
        
        # Create path
        filename = f"quote_{quote_id}_{safe_author}.png"
        path = os.path.join(
            self.output_base_dir,
            category,
            date_str,
            filename
        )
        
        return path
    
    def generate_all_images(self, batch_size: Optional[int] = None) -> Dict:
        """
        Generate images for all quotes that don't have them yet.
        
        Args:
            batch_size: Number of images to generate (None for all)
            
        Returns:
            Dictionary with statistics
        """
        quotes = self.get_quotes_needing_images(batch_size)
        total = len(quotes)
        
        if total == 0:
            logging.info("No quotes need images")
            return {'total': 0, 'success': 0, 'failed': 0}
        
        logging.info(f"Generating images for {total} quotes")
        
        success_count = 0
        failed_count = 0
        
        for i, quote_data in enumerate(quotes, 1):
            logging.info(f"Processing {i}/{total}: {quote_data['author']}")
            
            # Generate image path
            image_path = self.generate_image_path(
                quote_data['id'],
                quote_data['author'],
                quote_data['category'],
                quote_data['pub_date']
            )
            
            # Create image
            success = self.create_quote_image(
                quote_data['quote'],
                quote_data['author'],
                quote_data['category'],
                image_path
            )
            
            if success:
                # Save record
                if self.save_image_record(quote_data['id'], image_path):
                    success_count += 1
                    logging.info(f"✓ Generated: {image_path}")
                else:
                    failed_count += 1
                    logging.error(f"✗ Failed to save record for quote {quote_data['id']}")
            else:
                failed_count += 1
                logging.error(f"✗ Failed to generate image for quote {quote_data['id']}")
        
        stats = {
            'total': total,
            'success': success_count,
            'failed': failed_count
        }
        
        logging.info(f"Generation complete: {success_count} success, {failed_count} failed")
        return stats
    
    def get_statistics(self) -> Dict:
        """Get image generation statistics."""
        stats = {}
        
        # Total quotes
        self.cursor.execute('SELECT COUNT(*) FROM quotes')
        stats['total_quotes'] = self.cursor.fetchone()[0]
        
        # Classified quotes
        self.cursor.execute('SELECT COUNT(*) FROM quote_classifications')
        stats['classified_quotes'] = self.cursor.fetchone()[0]
        
        # Images generated
        self.cursor.execute('SELECT COUNT(*) FROM quote_images')
        stats['images_generated'] = self.cursor.fetchone()[0]
        
        # Pending images
        stats['pending_images'] = stats['classified_quotes'] - stats['images_generated']
        
        # By category
        self.cursor.execute('''
            SELECT c.category, COUNT(i.id) as count
            FROM quote_classifications c
            LEFT JOIN quote_images i ON c.quote_id = i.quote_id
            WHERE i.id IS NOT NULL
            GROUP BY c.category
            ORDER BY count DESC
        ''')
        stats['by_category'] = dict(self.cursor.fetchall())
        
        return stats
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logging.info("Database connection closed")


def print_statistics(stats: Dict):
    """Pretty print statistics."""
    print("\n" + "=" * 70)
    print("IMAGE GENERATION STATISTICS")
    print("=" * 70)
    print(f"Total Quotes:        {stats['total_quotes']}")
    print(f"Classified:          {stats['classified_quotes']}")
    print(f"Images Generated:    {stats['images_generated']}")
    print(f"Pending:             {stats['pending_images']}")
    
    print("\n" + "-" * 70)
    print("IMAGES BY CATEGORY")
    print("-" * 70)
    
    for category in CATEGORY_COLORS.keys():
        count = stats['by_category'].get(category, 0)
        bar = "█" * (count * 2) if count > 0 else ""
        print(f"{category:20} {count:3} {bar}")
    
    print("=" * 70 + "\n")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate Instagram images from quotes')
    parser.add_argument('--db', default='data/quotes.db', help='Database file path')
    parser.add_argument('--output-dir', default='images', help='Output directory for images')
    parser.add_argument('--batch-size', type=int, help='Number of images to generate')
    parser.add_argument('--action', choices=['generate', 'stats'], default='generate',
                        help='Action to perform')
    
    args = parser.parse_args()
    
    # Initialize generator
    generator = QuoteImageGenerator(
        db_path=args.db,
        output_base_dir=args.output_dir
    )
    
    try:
        generator.connect_db()
        
        if args.action == 'generate':
            # Generate images
            result = generator.generate_all_images(batch_size=args.batch_size)
            
            print("\n" + "=" * 70)
            print("GENERATION RESULTS")
            print("=" * 70)
            print(f"Total Processed: {result['total']}")
            print(f"Success:         {result['success']}")
            print(f"Failed:          {result['failed']}")
            print("=" * 70 + "\n")
            
            # Show statistics
            stats = generator.get_statistics()
            print_statistics(stats)
            
        elif args.action == 'stats':
            # Show statistics only
            stats = generator.get_statistics()
            print_statistics(stats)
    
    finally:
        generator.close()


if __name__ == '__main__':
    main()