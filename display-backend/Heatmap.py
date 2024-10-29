import sqlite3
from datetime import datetime, timedelta

class HeatmapAnimation:
    def __init__(self, db_path='heatmaps.db'):
        self.db_connection = sqlite3.connect(db_path)
        self.db_cursor = self.db_connection.cursor()

    def fetch_frames(self, animation_type, heatmap_type):
        print(animation_type, heatmap_type)
        """Fetch heatmap frames based on animation type and current time."""
        target_time = datetime.now()  # Current time
        start_time = self.calculate_start_time(animation_type, target_time)
        print(start_time)
        
        # Fetch frames based on the calculated time range
        frames = []
        query = '''
        SELECT file_path, timestamp FROM heatmap_logs
        WHERE timestamp BETWEEN ? AND ? 
        AND heatmap_type = ?  -- Filter by heatmap type (accum or reset)
        ORDER BY timestamp
        '''
        self.db_cursor.execute(query, (start_time.timestamp(), target_time.timestamp(), heatmap_type))
        results = self.db_cursor.fetchall()

        # Filter results based on the frame interval
        for row in results:
            file_path, frame_time = row
            frames.append((file_path, frame_time))

        return frames

    def calculate_start_time(self, animation_type, target_time):
        """Calculate the start time based on the animation type."""
        if animation_type == 30:
            return target_time - timedelta(minutes=30)
        elif animation_type == 60:
            return target_time - timedelta(hours=1)
        elif animation_type == 360:
            return target_time - timedelta(minutes=360)
        elif animation_type == 1440:
            return target_time - timedelta(days=1)
        else:
            raise ValueError("Invalid animation type. Choose from ['past_30_minutes', 'past_6_hours', 'past_24_hours', 'past_28_days']")


    # Get the heatmap file name from the database
    def get_heatmap_path(self,frame_type, timestamp):  # frame_type: 'accum' or 'reset'
# Convert from Unix time to SQLite datetime format if needed
        print("Timestamp:", timestamp)
        self.db_cursor.execute("SELECT file_path FROM heatmap_logs WHERE timestamp = ? AND heatmap_type = ?", (timestamp, frame_type))
        result = self.db_cursor.fetchone()
        if result is None:
            print("No heatmap found")
            return None
        else:
            return result[0]
        

    def close(self):
        """Close the database connection."""
        self.db_connection.close()

# Usage Example
if __name__ == "__main__":
    animation = HeatmapAnimation()
    try:
        frames_30_minutes_accum = animation.fetch_frames('past_30_minutes', 'accum')
        frames_30_minutes_reset = animation.fetch_frames('past_30_minutes', 'reset')
        frames_6_hours_accum = animation.fetch_frames('past_6_hours', 'accum')
        frames_6_hours_reset = animation.fetch_frames('past_6_hours', 'reset')
    except Exception as e:
        print(f"An error occurred: {e}")

    print("Frames for past 30 minutes (accum):")
    for frame in frames_30_minutes_accum:
        print(f"Frame: {frame[0]}, Timestamp: {frame[1]}")

    print("\nFrames for past 30 minutes (reset):")
    for frame in frames_30_minutes_reset:
        print(f"Frame: {frame[0]}, Timestamp: {frame[1]}")

    print("\nFrames for past 6 hours (accum):")
    for frame in frames_6_hours_accum:
        print(f"Frame: {frame[0]}, Timestamp: {frame[1]}")

    print("\nFrames for past 6 hours (reset):")
    for frame in frames_6_hours_reset:
        print(f"Frame: {frame[0]}, Timestamp: {frame[1]}")

    animation.close()
