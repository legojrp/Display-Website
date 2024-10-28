from FlightRadar24 import FlightRadar24API
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import os
import time
from datetime import datetime, timedelta
import sqlite3

# Initialize the API
fr_api = FlightRadar24API()

# Define the geographic boundaries of the United States
y1, y2, x1, x2 = 49, 24, -125, -60  # (max_lat, min_lat, min_lon, max_lon)

# Create a database connection
db_connection = sqlite3.connect('heatmaps.db')
db_cursor = db_connection.cursor()

# Create the heatmap logs table if it doesn't exist
db_cursor.execute('''
CREATE TABLE IF NOT EXISTS heatmap_logs (
    id INTEGER PRIMARY KEY,
    file_path TEXT,
    timestamp DATETIME,
    heatmap_type TEXT
)
''')
db_connection.commit()

# Create folders to save heatmap images
base_output_folder = "flight_heatmaps"
os.makedirs(base_output_folder, exist_ok=True)

# Create grids for heatmap accumulation and resetting
grid_resolution = 200  # Increase grid resolution for better detail
heatmap_grid_accum = np.zeros((grid_resolution, grid_resolution))  # For the accumulating heatmap
heatmap_grid_reset = np.zeros((grid_resolution, grid_resolution))  # For the 30-minute resetting heatmap
flight_history = []  # Store flight data and timestamps for the accumulating heatmap

# Function to get grid indices
def get_grid_indices(lat, lon):
    lat_index = int((lat - y2) / (y1 - y2) * (grid_resolution - 1))
    lon_index = int((lon - x1) / (x2 - x1) * (grid_resolution - 1))
    return lat_index, lon_index

def create_daily_folder():
    current_date = datetime.now().strftime('%Y-%m-%d')
    daily_folder = os.path.join(base_output_folder, current_date)
    os.makedirs(daily_folder, exist_ok=True)
    return daily_folder

import matplotlib.colors as mcolors

def save_heatmap(file_name, grid_data, heatmap_type):
    daily_folder = create_daily_folder()  # Create/get daily folder
    file_path = os.path.join(daily_folder, file_name)
    
    # Create a colormap where zero values are transparent
    cmap = plt.cm.hot  # Use the 'hot' colormap
    cmap.set_under(color='none')  # Set values below the minimum color threshold as transparent
    
    # Define the norm so that 0 values are fully transparent
    norm = mcolors.Normalize(vmin=0.1, vmax=np.max(grid_data))  # Adjust vmin slightly above 0 for transparency

    # Create the figure with a transparent background
    plt.figure(figsize=(12, 8), facecolor='none')  # Set figure background to none for transparency
    ax = plt.gca()
    ax.set_facecolor('none')  # Set axis background to none for transparency
    
    # Plot heatmap
    plt.imshow(grid_data, cmap=cmap, norm=norm, interpolation='nearest', origin='lower',
               extent=[x1, x2, y2, y1], aspect='auto')
    plt.axis('off')  # Turn off the axis
    plt.savefig(file_path, bbox_inches='tight', pad_inches=0, dpi=300, transparent=True)  # transparent=True
    plt.close()

    # Log the heatmap in the database
    db_cursor.execute('INSERT INTO heatmap_logs (file_path, timestamp, heatmap_type) VALUES (?, ?, ?)', 
                      (file_path, int(datetime.now().timestamp()), heatmap_type))
    db_connection.commit()




def fetch_flights_and_update_heatmaps():
    # Get the current time
    current_time = datetime.now()

    # Fetch flights currently in the air
    flights = fr_api.get_flights(bounds=f"{y1},{y2},{x1},{x2}")

    # Update the accumulating heatmap and track flight history
    if flights:
        for flight in flights:
            lats = flight.latitude
            lons = flight.longitude
            
            # Check if the flight's coordinates are within the bounds of the U.S.
            if y2 <= lats <= y1 and x1 <= lons <= x2:
                lat_index, lon_index = get_grid_indices(lats, lons)
                heatmap_grid_accum[lat_index, lon_index] += 1  # Increment the accumulating heatmap count
                heatmap_grid_reset[lat_index, lon_index] += 1  # Increment the resetting heatmap count
                
                # Store flight data with its timestamp
                flight_history.append((current_time, lat_index, lon_index))

    # Remove contributions older than 30 minutes from the accumulating heatmap grid
    thirty_minutes_ago = current_time - timedelta(minutes=30)
    flight_history[:] = [entry for entry in flight_history if entry[0] >= thirty_minutes_ago]

    # Save the accumulating heatmap
    save_heatmap(f"heatmap_accum_{int(time.time())}.png", heatmap_grid_accum, "accum")

    # Reset the resetting heatmap if the current time is divisible by 30 minutes
    if current_time.minute % 30 == 0 and current_time.second == 0:  # Check if it's the start of a new 30-minute interval
        heatmap_grid_reset.fill(0)  # Reset the grid
        print("Resetting the 30-minute heatmap")

    # Save the resetting heatmap
    save_heatmap(f"heatmap_reset_{int(time.time())}.png", heatmap_grid_reset, "reset")

# Main loop: update every 2 minutes
while True:
    fetch_flights_and_update_heatmaps()  # Fetch flights and update heatmaps
    
    # Wait for 2 minutes before the next iteration
    print("Updated heatmaps")
    time.sleep(120)  # Sleep for 2 minutes (120 seconds)

# Close the database connection (this line will not be reached in this infinite loop)
db_connection.close()
