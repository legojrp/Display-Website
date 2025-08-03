import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseHandler:
    """
    Database handler for managing RSS feed articles.
    Handles CRUD operations for the articles table.
    """
    
    def __init__(self, db_path: str = "articles.db"):
        """
        Initialize the database handler.
        
        Args:
            db_path (str): Path to the SQLite database file
        """
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self) -> sqlite3.Connection:
        """
        Get a database connection.
        
        Returns:
            sqlite3.Connection: Database connection object
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable accessing columns by name
        return conn
    
    def init_database(self):
        """
        Initialize the database and create the articles table if it doesn't exist.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS articles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        link TEXT UNIQUE NOT NULL,
                        description TEXT,
                        author TEXT,
                        published_date DATETIME,
                        status TEXT DEFAULT 'pending',
                        ranking_score REAL DEFAULT 0.0,
                        ai_summary TEXT,
                        ai_reasoning TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        times_served INTEGER DEFAULT 0
                    )
                ''')
                
                # Create indexes for better performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_status ON articles(status)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_published_date ON articles(published_date)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_ranking_score ON articles(ranking_score)')
                
                conn.commit()
                logger.info("Database initialized successfully")
        except sqlite3.Error as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def insert_article(self, title: str, link: str, description: str = None, 
                      author: str = None, published_date: datetime = None,
                      status: str = 'pending', ranking_score: float = 0.0,
                      ai_summary: str = None, ai_reasoning: str = None, times_served: int = 0) -> Optional[int]:
        """
        Insert a new article into the database.
        
        Args:
            title (str): Article title
            link (str): Article URL (must be unique)
            description (str, optional): Article description
            author (str, optional): Article author
            published_date (datetime, optional): Publication date
            status (str): Article status (default: 'pending')
            ranking_score (float): Article ranking score (default: 0.0)
            ai_summary (str, optional): AI-generated summary
            
        Returns:
            int or None: The ID of the inserted article, or None if insertion failed
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO articles 
                    (title, link, description, author, published_date, status, ranking_score, ai_summary, ai_reasoning, updated_at, times_served)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
                ''', (title, link, description, author, published_date, status, ranking_score, ai_summary, ai_reasoning, times_served))
                
                article_id = cursor.lastrowid
                conn.commit()
                logger.info(f"Article inserted successfully with ID: {article_id}")
                return article_id
        except sqlite3.IntegrityError as e:
            logger.warning(f"Article with link '{link}' already exists: {e}")
            return None
        except sqlite3.Error as e:
            logger.error(f"Error inserting article: {e}")
            return None
    def get_articles(self, status: str = None, min_ranking: float = None, order_by: str = 'published_date') -> List[Dict]:
        """
        Retrieve articles from the database.
        
        Args:
            status (str, optional): Filter by article status
            min_ranking (float, optional): Minimum ranking score to filter by
            order_by (str): Column to order by (default: 'published_date')
            
        Returns:
            list: List of article dictionaries
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                query = 'SELECT * FROM articles'
                params = []
                
                if status:
                    query += ' WHERE status = ?'
                    params.append(status)
                
                if min_ranking is not None:
                    query += ' AND ranking_score >= ?' if 'WHERE' in query else ' WHERE ranking_score >= ?'
                    params.append(min_ranking)
                
                query += f' ORDER BY {order_by}'
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Error retrieving articles: {e}")
            return []
    
    def get_article_by_id(self, article_id: int) -> Optional[Dict]:
        """
        Retrieve an article by its ID.
        
        Args:
            article_id (int): The article ID
            
        Returns:
            dict or None: Article data as dictionary, or None if not found
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM articles WHERE id = ?', (article_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Error retrieving article by ID {article_id}: {e}")
            return None
    
    def get_article_by_link(self, link: str) -> Optional[Dict]:
        """
        Retrieve an article by its link.
        
        Args:
            link (str): The article link
            
        Returns:
            dict or None: Article data as dictionary, or None if not found
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM articles WHERE link = ?', (link,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Error retrieving article by link '{link}': {e}")
            return None
    
    def get_articles_by_status(self, status: str, limit: int = None, 
                              order_by: str = 'published_date', desc: bool = True) -> List[Dict]:
        """
        Retrieve articles by status.
        
        Args:
            status (str): Article status ('pending', 'kept', 'tossed')
            limit (int, optional): Maximum number of articles to retrieve
            order_by (str): Column to order by (default: 'published_date')
            desc (bool): Sort in descending order (default: True)
            
        Returns:
            list: List of article dictionaries
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                order_direction = "DESC" if desc else "ASC"
                query = f'SELECT * FROM articles WHERE status = ? ORDER BY {order_by} {order_direction}'
                
                if limit:
                    query += f' LIMIT {limit}'
                
                cursor.execute(query, (status,))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Error retrieving articles by status '{status}': {e}")
            return []
    
    def get_all_articles(self, limit: int = None, order_by: str = 'published_date', 
                        desc: bool = True) -> List[Dict]:
        """
        Retrieve all articles.
        
        Args:
            limit (int, optional): Maximum number of articles to retrieve
            order_by (str): Column to order by (default: 'published_date')
            desc (bool): Sort in descending order (default: True)
            
        Returns:
            list: List of article dictionaries
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                order_direction = "DESC" if desc else "ASC"
                query = f'SELECT * FROM articles ORDER BY {order_by} {order_direction}'
                
                if limit:
                    query += f' LIMIT {limit}'
                
                cursor.execute(query)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Error retrieving all articles: {e}")
            return []
    
    def update_article(self, article_id: int, **kwargs) -> bool:
        """
        Update an article's fields.
        
        Args:
            article_id (int): The article ID
            **kwargs: Fields to update (title, description, author, published_date, 
                     status, ranking_score, ai_summary)
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        if not kwargs:
            logger.warning("No fields provided for update")
            return False
        
        # Add updated_at timestamp
        kwargs['updated_at'] = datetime.now().isoformat()
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build the UPDATE query dynamically
                set_clause = ', '.join([f"{key} = ?" for key in kwargs.keys()])
                query = f'UPDATE articles SET {set_clause} WHERE id = ?'
                values = list(kwargs.values()) + [article_id]
                
                cursor.execute(query, values)
                conn.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"Article {article_id} updated successfully")
                    return True
                else:
                    logger.warning(f"No article found with ID {article_id}")
                    return False
        except sqlite3.Error as e:
            logger.error(f"Error updating article {article_id}: {e}")
            return False
    
    def update_article_status(self, article_id: int, status: str) -> bool:
        """
        Update an article's status.
        
        Args:
            article_id (int): The article ID
            status (str): New status ('pending', 'kept', 'tossed')
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        return self.update_article(article_id, status=status)
    
    def update_article_ranking(self, article_id: int, ranking_score: float) -> bool:
        """
        Update an article's ranking score.
        
        Args:
            article_id (int): The article ID
            ranking_score (float): New ranking score
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        return self.update_article(article_id, ranking_score=ranking_score)
    
    def update_article_summary(self, article_id: int, ai_summary: str) -> bool:
        """
        Update an article's AI summary.
        
        Args:
            article_id (int): The article ID
            ai_summary (str): New AI summary
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        return self.update_article(article_id, ai_summary=ai_summary)
    
    def delete_article(self, article_id: int) -> bool:
        """
        Delete an article by ID.
        
        Args:
            article_id (int): The article ID
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM articles WHERE id = ?', (article_id,))
                conn.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"Article {article_id} deleted successfully")
                    return True
                else:
                    logger.warning(f"No article found with ID {article_id}")
                    return False
        except sqlite3.Error as e:
            logger.error(f"Error deleting article {article_id}: {e}")
            return False
    
    def get_articles_count(self, status: str = None) -> int:
        """
        Get the count of articles, optionally filtered by status.
        
        Args:
            status (str, optional): Article status to filter by
            
        Returns:
            int: Number of articles
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if status:
                    cursor.execute('SELECT COUNT(*) FROM articles WHERE status = ?', (status,))
                else:
                    cursor.execute('SELECT COUNT(*) FROM articles')
                return cursor.fetchone()[0]
        except sqlite3.Error as e:
            logger.error(f"Error counting articles: {e}")
            return 0
    
    def get_top_ranked_articles(self, limit: int = 10, status: str = None) -> List[Dict]:
        """
        Get the top-ranked articles.
        
        Args:
            limit (int): Maximum number of articles to retrieve
            status (str, optional): Filter by status
            
        Returns:
            list: List of top-ranked article dictionaries
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if status:
                    query = 'SELECT * FROM articles WHERE status = ? ORDER BY ranking_score DESC LIMIT ?'
                    cursor.execute(query, (status, limit))
                else:
                    query = 'SELECT * FROM articles ORDER BY ranking_score DESC LIMIT ?'
                    cursor.execute(query, (limit,))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Error retrieving top-ranked articles: {e}")
            return []
    
    def search_articles(self, search_term: str, fields: List[str] = None) -> List[Dict]:
        """
        Search articles by a term in specified fields.
        
        Args:
            search_term (str): Term to search for
            fields (list, optional): Fields to search in (default: ['title', 'description', 'author'])
            
        Returns:
            list: List of matching article dictionaries
        """
        if fields is None:
            fields = ['title', 'description', 'author']
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build WHERE clause for searching in multiple fields
                conditions = [f"{field} LIKE ?" for field in fields]
                where_clause = " OR ".join(conditions)
                query = f'SELECT * FROM articles WHERE {where_clause} ORDER BY ranking_score DESC'
                
                # Prepare search parameters
                search_params = [f'%{search_term}%' for _ in fields]
                
                cursor.execute(query, search_params)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Error searching articles: {e}")
            return []
    
    def bulk_update_status(self, article_ids: List[int], status: str) -> int:
        """
        Update the status of multiple articles.
        
        Args:
            article_ids (list): List of article IDs
            status (str): New status
            
        Returns:
            int: Number of articles updated
        """
        if not article_ids:
            return 0
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                placeholders = ','.join(['?' for _ in article_ids])
                query = f'UPDATE articles SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id IN ({placeholders})'
                params = [status] + article_ids
                
                cursor.execute(query, params)
                conn.commit()
                
                updated_count = cursor.rowcount
                logger.info(f"Updated status for {updated_count} articles")
                return updated_count
        except sqlite3.Error as e:
            logger.error(f"Error bulk updating article status: {e}")
            return 0
    
    def get_articles_with_summaries(self, limit: int = 10, min_score: float = None) -> List[Dict]:
        """
        Get articles that have AI summaries, optionally filtered by minimum score.
        
        Args:
            limit (int): Maximum number of articles to retrieve
            min_score (float, optional): Minimum ranking score to filter by
            
        Returns:
            list: List of article dictionaries with AI summaries
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if min_score is not None:
                    query = '''SELECT * FROM articles 
                              WHERE ai_summary IS NOT NULL AND ai_summary != '' 
                              AND ranking_score >= ?
                              ORDER BY ranking_score DESC LIMIT ?'''
                    cursor.execute(query, (min_score, limit))
                else:
                    query = '''SELECT * FROM articles 
                              WHERE ai_summary IS NOT NULL AND ai_summary != ''
                              ORDER BY ranking_score DESC LIMIT ?'''
                    cursor.execute(query, (limit,))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Error retrieving articles with summaries: {e}")
            return []
    def increment_times_served(self, article_id: int) -> bool:
        """
        Increment the times served count for an article.
        
        Args:
            article_id (int): The article ID
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE articles SET times_served = times_served + 1 WHERE id = ?', (article_id,))
                conn.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"Incremented times served for article {article_id}")
                    return True
                else:
                    logger.warning(f"No article found with ID {article_id} to increment times served")
                    return False
        except sqlite3.Error as e:
            logger.error(f"Error incrementing times served for article {article_id}: {e}")
            return False

    def close(self):
        """
        Close the database connection (if using persistent connections).
        Currently not needed since we use context managers.
        """
        pass
