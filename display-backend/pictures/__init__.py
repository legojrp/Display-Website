"""
Pictures module for the Display-Website backend.

This module handles picture-related functionality such as storage, retrieval,
and manipulation for the display website.
"""

# Import database handler class
from .db_handler import PictureDBHandler

# Import picture handling functions
from .picture_handler import (
    save_uploaded_picture,
    get_pictures,
    update_picture_likes,
    toggle_picture_visibility,
    delete_picture,
    get_pictures_algorithmically
)

# Define public API
__all__ = [
    # Database handler
    'PictureDBHandler',
    
    # Picture operations
    'save_uploaded_picture',
    'get_pictures',
    'update_picture_likes',
    'toggle_picture_visibility',
    'delete_picture',
    'get_pictures_algorithmically'
]