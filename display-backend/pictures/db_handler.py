import sqlite3
import os
from pathlib import Path

class PictureDBHandler:
    def __init__(self, db_path="pictures/pictures.db"):
        """Initialize the database handler."""
        self.db_path = db_path
        self._create_table_if_not_exists()
    
    def _create_table_if_not_exists(self):
        """Create the pictures table if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pictures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT UNIQUE NOT NULL,
                likes INTEGER DEFAULT 0,
                show_picture BOOLEAN DEFAULT 1
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_picture(self, filename):
        """Add a new picture to the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO pictures (filename, likes, show_picture) VALUES (?, 0, 1)",
                (filename,)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            # Picture already exists
            return False
        finally:
            conn.close()
    
    def get_all_pictures(self):
        """Get all pictures from the database."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM pictures")
        pictures = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return pictures
    
    def get_visible_pictures(self):
        """Get only pictures marked as visible."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM pictures WHERE show_picture = 1")
        pictures = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return pictures
    
    def update_likes(self, filename, increment=True):
        """Increase or decrease the likes for a picture."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        delta = 1 if increment else -1
        
        cursor.execute(
            "UPDATE pictures SET likes = likes + ? WHERE filename = ?",
            (delta, filename)
        )
        
        if cursor.rowcount == 0:
            conn.close()
            return False
            
        conn.commit()
        conn.close()
        return True
    
    def toggle_visibility(self, filename):
        """Toggle the visibility of a picture."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE pictures SET show_picture = NOT show_picture WHERE filename = ?",
            (filename,)
        )
        
        if cursor.rowcount == 0:
            conn.close()
            return False
            
        conn.commit()
        conn.close()
        return True
    
    def delete_picture(self, filename):
        """Delete a picture from the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM pictures WHERE filename = ?", (filename,))
        
        if cursor.rowcount == 0:
            conn.close()
            return False
            
        conn.commit()
        conn.close()
        return True
    
    def get_picture_info(self, filename):
        """Get information about a specific picture."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM pictures WHERE filename = ?", (filename,))
        picture = cursor.fetchone()
        
        conn.close()
        
        if picture:
            return dict(picture)
        return None