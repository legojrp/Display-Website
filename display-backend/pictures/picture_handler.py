import os
import base64
from datetime import datetime
from .db_handler import PictureDBHandler
import numpy as np
import uuid


def save_uploaded_picture(base64_image: str, title: str, description: str) -> dict:
    """
    Save an uploaded picture to the system and database.

    Args:
        base64_image: Base64 encoded image string
        title: Title of the picture
        description: Description of the picture

    Returns:
        A dictionary with the result of the operation
    """
    try:
        # Remove data URL prefix if present (e.g., "data:image/png;base64,")
        if base64_image.startswith('data:'):
            base64_image = base64_image.split(',', 1)[1]
        
        # Decode the base64 image
        image_data = base64.b64decode(base64_image)

        # Generate a unique filename with microseconds and UUID to avoid collisions
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')  # Added microseconds
        unique_id = str(uuid.uuid4())[:8]  # Short UUID for extra uniqueness
        filename = f"{title}_{timestamp}_{unique_id}.png"
        file_path = os.path.join("pictures", "uploads", filename)

        # Save the image to filesystem
        with open(file_path, "wb") as f:
            f.write(image_data)
            
        # Save to database using db_handler
        db_handler = PictureDBHandler()
        success = db_handler.add_picture(filename)
        
        if not success:
            # If database insertion fails (very rare with unique filenames), 
            # remove the file and try with a different filename
            print(f"Warning: Picture {filename} already exists in database, generating new filename")
            os.remove(file_path)
            
            # Generate a new filename with additional randomness
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            unique_id = str(uuid.uuid4())[:12]  # Longer UUID for extra uniqueness
            filename = f"{title}_{timestamp}_{unique_id}.png"
            file_path = os.path.join("pictures", "uploads", filename)
            
            # Save the image again with new filename
            with open(file_path, "wb") as f:
                f.write(image_data)
            
            # Try database insertion again
            success = db_handler.add_picture(filename)
            
            if not success:
                # If it still fails, remove the file and return error
                os.remove(file_path)
                return {"success": False, "error": "Failed to save picture to database after multiple attempts"}

        # Return success response
        return {"success": True, "filename": filename}
    except Exception as e:
        print(f"Error saving uploaded picture: {str(e)}")
        return {"success": False, "error": str(e)}
    
def get_pictures(limit: int = 10, offset: int = 0) -> list:
    """
    Retrieve a list of pictures from the system.

    Args:
        limit: Maximum number of pictures to retrieve
        offset: Offset for pagination

    Returns:
        A list of dictionaries containing picture metadata
    """
    try:
        # Get pictures from database using db_handler
        db_handler = PictureDBHandler()
        all_pictures = db_handler.get_visible_pictures()
        
        # Apply pagination
        start_index = offset
        end_index = offset + limit
        pictures = all_pictures[start_index:end_index]
        
        # Add full file path for each picture
        for picture in pictures:
            picture['file_path'] = os.path.join("pictures", "uploads", picture['filename'])
        
        return pictures
    except Exception as e:
        print(f"Error retrieving pictures: {str(e)}")
        return []


def update_picture_likes(filename: str, increment: bool = True) -> dict:
    """
    Update the likes count for a picture.

    Args:
        filename: The filename of the picture
        increment: True to increment likes, False to decrement

    Returns:
        A dictionary with the result of the operation
    """
    try:
        db_handler = PictureDBHandler()
        success = db_handler.update_likes(filename, increment)
        
        if success:
            return {"success": True, "message": "Likes updated successfully"}
        else:
            return {"success": False, "error": "Picture not found"}
    except Exception as e:
        print(f"Error updating picture likes: {str(e)}")
        return {"success": False, "error": str(e)}


def toggle_picture_visibility(filename: str) -> dict:
    """
    Toggle the visibility of a picture.

    Args:
        filename: The filename of the picture

    Returns:
        A dictionary with the result of the operation
    """
    try:
        db_handler = PictureDBHandler()
        success = db_handler.toggle_visibility(filename)
        
        if success:
            return {"success": True, "message": "Visibility toggled successfully"}
        else:
            return {"success": False, "error": "Picture not found"}
    except Exception as e:
        print(f"Error toggling picture visibility: {str(e)}")
        return {"success": False, "error": str(e)}


def delete_picture(filename: str) -> dict:
    """
    Delete a picture from both filesystem and database.

    Args:
        filename: The filename of the picture

    Returns:
        A dictionary with the result of the operation
    """
    try:
        # Delete from filesystem
        file_path = os.path.join("pictures", "uploads", filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Delete from database
        db_handler = PictureDBHandler()
        success = db_handler.delete_picture(filename)
        
        if success:
            return {"success": True, "message": "Picture deleted successfully"}
        else:
            return {"success": False, "error": "Picture not found in database"}
    except Exception as e:
        print(f"Error deleting picture: {str(e)}")
        return {"success": False, "error": str(e)}
    
def get_pictures_algorithmically(limit: int = 10, offset: int = 0) -> list:
    """
    Retrieve a list of pictures using an algorithmic approach, using the likes (which is negative if they disliked images) to then randomly select pictures from db.
    
    Args:
        limit: Maximum number of pictures to retrieve
        offset: Offset for pagination (applied after algorithmic selection)
    
    Returns:
        A list of dictionaries containing picture metadata (same format as get_pictures)
    """
    try:
        db_handler = PictureDBHandler()
        all_pictures = db_handler.get_visible_pictures()  # Use visible pictures like get_pictures
        
        # Filter out pictures with negative likes
        positive_pictures = [pic for pic in all_pictures if pic['likes'] >= 0]
        
        if not positive_pictures:
            return []
            
        # Calculate probabilities based on likes
        # Add 1 to all likes to ensure even pictures with 0 likes have some chance
        likes = np.array([pic['likes'] + 1 for pic in positive_pictures])
        probabilities = likes / likes.sum()
        
        # Calculate total items needed (limit + offset) but cap at available pictures
        total_needed = min(limit + offset, len(positive_pictures))
        
        # Randomly select pictures based on their like probabilities
        indices = np.random.choice(
            len(positive_pictures),
            size=total_needed, 
            replace=False,
            p=probabilities
        )
        
        # Get the selected pictures and apply pagination
        selected_pictures = [positive_pictures[i] for i in indices]
        
        # Apply pagination
        start_index = offset
        end_index = offset + limit
        pictures = selected_pictures[start_index:end_index]
        
        # Add full file path for each picture (same as get_pictures)
        for picture in pictures:
            picture['file_path'] = os.path.join("pictures", "uploads", picture['filename'])
        
        return pictures
    except Exception as e:
        print(f"Error retrieving algorithmic pictures: {str(e)}")
        return []
   