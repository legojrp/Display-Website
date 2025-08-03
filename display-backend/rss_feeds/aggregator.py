import json
import feedparser
import logging
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urljoin
import time
import os

from .db_handler import DatabaseHandler

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RSSAggregator:
    """
    RSS Feed Aggregator that fetches articles from RSS feeds and stores them in the database.
    """
    
    def __init__(self, feeds_file: str = "feeds.json", db_path: str = "articles.db"):
        """
        Initialize the RSS aggregator.
        
        Args:
            feeds_file (str): Path to the feeds.json file
            db_path (str): Path to the SQLite database file
        """
        self.feeds_file = feeds_file
        self.db_handler = DatabaseHandler(db_path)
        self.feeds = self._load_feeds()
    
    def _load_feeds(self) -> List[Dict]:
        """
        Load RSS feeds from the feeds.json file.
        
        Returns:
            List[Dict]: List of feed configurations
        """
        try:
            if not os.path.exists(self.feeds_file):
                logger.error(f"Feeds file not found: {self.feeds_file}")
                return []
            
            with open(self.feeds_file, 'r', encoding='utf-8') as f:
                feeds = json.load(f)
            
            logger.info(f"Loaded {len(feeds)} feeds from {self.feeds_file}")
            return feeds
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing feeds.json: {e}")
            return []
        except Exception as e:
            logger.error(f"Error loading feeds: {e}")
            return []
    
    def _parse_published_date(self, entry) -> Optional[datetime]:
        """
        Parse the published date from an RSS entry.
        
        Args:
            entry: RSS entry object from feedparser
            
        Returns:
            datetime or None: Parsed datetime object
        """
        try:
            # Try to get published_parsed first, then updated_parsed
            time_struct = getattr(entry, 'published_parsed', None) or getattr(entry, 'updated_parsed', None)
            
            if time_struct:
                return datetime(*time_struct[:6])
            
            # If no parsed time, try to parse the string
            date_string = getattr(entry, 'published', None) or getattr(entry, 'updated', None)
            if date_string:
                # feedparser usually handles this, but just in case
                return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            
        except Exception as e:
            logger.warning(f"Could not parse date: {e}")
        
        return None
    
    def _get_article_author(self, entry) -> Optional[str]:
        """
        Extract author information from an RSS entry.
        
        Args:
            entry: RSS entry object from feedparser
            
        Returns:
            str or None: Author name
        """
        # Try different author fields
        author = getattr(entry, 'author', None)
        if not author and hasattr(entry, 'authors') and entry.authors:
            author = entry.authors[0].get('name', None)
        
        return author
    
    def _get_article_description(self, entry) -> Optional[str]:
        """
        Extract description from an RSS entry.
        
        Args:
            entry: RSS entry object from feedparser
            
        Returns:
            str or None: Article description
        """
        # Try summary first, then description
        description = getattr(entry, 'summary', None)
        if not description:
            description = getattr(entry, 'description', None)
        
        return description
    
    def fetch_feed_articles(self, feed: Dict) -> List[Dict]:
        """
        Fetch articles from a single RSS feed.
        
        Args:
            feed (Dict): Feed configuration containing url, title, category, etc.
            
        Returns:
            List[Dict]: List of article data dictionaries
        """
        articles = []
        feed_url = feed.get('url')
        feed_title = feed.get('title', 'Unknown Feed')
        
        if not feed_url:
            logger.warning(f"No URL found for feed: {feed_title}")
            return articles
        
        try:
            logger.info(f"Fetching articles from: {feed_title} ({feed_url})")
            
            # Parse the RSS feed
            parsed_feed = feedparser.parse(feed_url)
            
            if parsed_feed.bozo and parsed_feed.bozo_exception:
                logger.warning(f"Feed parsing warning for {feed_title}: {parsed_feed.bozo_exception}")
            
            # Process each entry
            for entry in parsed_feed.entries:
                try:
                    # Extract article data
                    title = getattr(entry, 'title', 'No Title')
                    link = getattr(entry, 'link', '')
                    
                    if not link:
                        logger.warning(f"No link found for article: {title}")
                        continue
                    
                    description = self._get_article_description(entry)
                    author = self._get_article_author(entry)
                    published_date = self._parse_published_date(entry)
                    
                    article_data = {
                        'title': title.strip(),
                        'link': link.strip(),
                        'description': description.strip() if description else None,
                        'author': author.strip() if author else None,
                        'published_date': published_date,
                        'feed_title': feed_title,
                        'feed_category': feed.get('category', 'General'),
                        'feed_language': feed.get('language', 'en')
                    }
                    
                    articles.append(article_data)
                    
                except Exception as e:
                    logger.error(f"Error processing entry from {feed_title}: {e}")
                    continue
            
            logger.info(f"Successfully fetched {len(articles)} articles from {feed_title}")
            
        except Exception as e:
            logger.error(f"Error fetching feed {feed_title}: {e}")
        
        return articles
    
    def store_article(self, article_data: Dict) -> bool:
        """
        Store an article in the database.
        
        Args:
            article_data (Dict): Article data dictionary
            
        Returns:
            bool: True if stored successfully, False otherwise
        """
        try:
            # Check if article already exists
            existing_article = self.db_handler.get_article_by_link(article_data['link'])
            if existing_article:
                logger.debug(f"Article already exists: {article_data['title']}")
                return False
            
            # Insert new article
            article_id = self.db_handler.insert_article(
                title=article_data['title'],
                link=article_data['link'],
                description=article_data['description'],
                author=article_data['author'],
                published_date=article_data['published_date'],
                status='pending',
                ranking_score=0.0
            )
            
            if article_id:
                logger.info(f"Stored article: {article_data['title']} (ID: {article_id})")
                return True
            else:
                logger.warning(f"Failed to store article: {article_data['title']}")
                return False
                
        except Exception as e:
            logger.error(f"Error storing article {article_data['title']}: {e}")
            return False
    
    def aggregate_all_feeds(self) -> Dict[str, int]:
        """
        Aggregate articles from all RSS feeds.
        
        Returns:
            Dict[str, int]: Summary statistics of the aggregation
        """
        stats = {
            'feeds_processed': 0,
            'articles_fetched': 0,
            'articles_stored': 0,
            'articles_skipped': 0
        }
        
        if not self.feeds:
            logger.warning("No feeds to process")
            return stats
        
        logger.info(f"Starting aggregation of {len(self.feeds)} feeds")
        
        for feed in self.feeds:
            try:
                stats['feeds_processed'] += 1
                
                # Fetch articles from this feed
                articles = self.fetch_feed_articles(feed)
                stats['articles_fetched'] += len(articles)
                
                # Store each article
                for article in articles:
                    if self.store_article(article):
                        stats['articles_stored'] += 1
                    else:
                        stats['articles_skipped'] += 1
                
                # Small delay between feeds to be respectful
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error processing feed {feed.get('title', 'Unknown')}: {e}")
                continue
        
        logger.info(f"Aggregation completed. Stats: {stats}")
        return stats
    
    def aggregate_single_feed(self, feed_title: str) -> Dict[str, int]:
        """
        Aggregate articles from a single RSS feed by title.
        
        Args:
            feed_title (str): Title of the feed to process
            
        Returns:
            Dict[str, int]: Summary statistics of the aggregation
        """
        stats = {
            'feeds_processed': 0,
            'articles_fetched': 0,
            'articles_stored': 0,
            'articles_skipped': 0
        }
        
        # Find the feed by title
        target_feed = None
        for feed in self.feeds:
            if feed.get('title') == feed_title:
                target_feed = feed
                break
        
        if not target_feed:
            logger.error(f"Feed not found: {feed_title}")
            return stats
        
        logger.info(f"Processing single feed: {feed_title}")
        
        try:
            stats['feeds_processed'] = 1
            
            # Fetch articles from this feed
            articles = self.fetch_feed_articles(target_feed)
            stats['articles_fetched'] = len(articles)
            
            # Store each article
            for article in articles:
                if self.store_article(article):
                    stats['articles_stored'] += 1
                else:
                    stats['articles_skipped'] += 1
            
        except Exception as e:
            logger.error(f"Error processing feed {feed_title}: {e}")
        
        logger.info(f"Single feed aggregation completed. Stats: {stats}")
        return stats

    def fetch_articles_algorithmically(self, number=20) -> List[Dict]:
        """
        Fetch articles using an algorithmic approach (e.g., AI ranking).
        
        Args:
            number (int): Number of articles to fetch
            
        Returns:
            List[Dict]: List of ranked articles
        """
        try:
            # Get all articles from the database with ranking above 50
            articles = self.db_handler.get_articles(
                min_ranking=50.0,  # Get a reasonable number of candidates
                order_by='ranking_score DESC'
            )
            
            if not articles:
                logger.info("No high-ranking articles found")
                return []
            
            # Calculate a score that balances ranking, times_served, and published_date
            # Higher ranking = more likely to be shown
            # Higher times_served = less likely to be shown
            # Newer articles = more likely to be shown
            current_time = datetime.now()
            ranked_articles = []
            
            for article in articles:
                # Calculate days since publication
                published_date = article['published_date']
                if published_date:
                    # Convert string to datetime if needed
                    if isinstance(published_date, str):
                        try:
                            published_date = datetime.fromisoformat(published_date.replace('Z', '+00:00'))
                        except:
                            published_date = None
                    
                    if published_date:
                        days_since_published = (current_time - published_date).days
                        # Age penalty factor - older articles get penalized more
                        # Add 1 to avoid division by zero for very new articles
                        age_factor = max(1, days_since_published + 1)
                    else:
                        # Default age factor if we couldn't parse the date
                        age_factor = 10  # Assume somewhat old
                else:
                    # Default age factor if no published date
                    age_factor = 10  # Assume somewhat old
                
                # Calculate an adjusted score that considers:
                # - Higher ranking = better
                # - Lower times_served = better
                # - Lower age = better
                adjusted_score = article['ranking_score'] / ((article['times_served'] + 1) * age_factor)
                
                article['adjusted_score'] = adjusted_score
                ranked_articles.append(article)
            
            # Sort by adjusted score
            ranked_articles.sort(key=lambda x: x['adjusted_score'], reverse=True)
            
            # Limit to the requested number
            result_articles = ranked_articles[:number]
            
            # Update times_served for all articles being returned
            for article in result_articles:
                self.db_handler.increment_times_served(article['id'])
            
            logger.info(f"Fetched {len(result_articles)} articles algorithmically")
            return result_articles

        except Exception as e:
            logger.error(f"Error fetching articles algorithmically: {e}")
            return []


# def main():
#     """
#     Main function to run the RSS aggregator.
#     """
#     # Change to the script's directory to ensure relative paths work
#     script_dir = os.path.dirname(os.path.abspath(__file__))
#     os.chdir(script_dir)
    
#     # Initialize aggregator
#     aggregator = RSSAggregator()
    
#     # Run aggregation
#     stats = aggregator.aggregate_all_feeds()
    
#     print("\n" + "="*50)
#     print("RSS AGGREGATION SUMMARY")
#     print("="*50)
#     print(f"Feeds processed: {stats['feeds_processed']}")
#     print(f"Articles fetched: {stats['articles_fetched']}")
#     print(f"Articles stored: {stats['articles_stored']}")
#     print(f"Articles skipped: {stats['articles_skipped']}")
#     print("="*50)


# if __name__ == "__main__":
#     main()
