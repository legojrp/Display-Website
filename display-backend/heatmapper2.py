import numpy as np
import os
import time
from datetime import datetime, timedelta
import sqlite3
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from FlightRadar24 import FlightRadar24API

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
grid_resolution = 200
heatmap_grid_rolling = np.zeros((grid_resolution, grid_resolution))  # Rolling accumulation grid
heatmap_grid_reset_30min = np.zeros((grid_resolution, grid_resolution))  # 30-min resetting grid
heatmap_grid_reset_hour = np.zeros((grid_resolution, grid_resolution))  # Hourly resetting grid
flight_history = []  # Store flight data and timestamps

# Initialize reset timestamps
last_30min_reset = datetime.now()
last_hour_reset = datetime.now()

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

def save_heatmap(file_name, grid_data, heatmap_type, cmap_max=50):
    daily_folder = create_daily_folder()
    file_path = os.path.join(daily_folder, file_name)
    
    # Set colormap and normalization to cap maximum intensity
    cmap = plt.cm.hot
    cmap.set_under(color='none')
    norm = mcolors.Normalize(vmin=0.1, vmax=cmap_max)

    # Create figure with a dark background
    plt.figure(figsize=(12, 8), facecolor='none')
    ax = plt.gca()
    ax.set_facecolor('none')
    
    # Plot heatmap with density cap
    plt.imshow(grid_data, cmap=cmap, norm=norm, interpolation='nearest', origin='lower',
               extent=[x1, x2, y2, y1], aspect='auto')
    plt.axis('off')
    plt.savefig(file_path, bbox_inches='tight', pad_inches=0, dpi=300, transparent=True)
    plt.close()

    # Log the heatmap in the database
    db_cursor.execute('INSERT INTO heatmap_logs (file_path, timestamp, heatmap_type) VALUES (?, ?, ?)', 
                      (file_path, int(datetime.now().timestamp()), heatmap_type))
    db_connection.commit()

def fetch_flights_and_update_heatmaps():
    current_time = datetime.now()
    global last_30min_reset, last_hour_reset
    
    if current_time - last_30min_reset >= timedelta(minutes=30):
        heatmap_grid_reset_30min.fill(0)
        last_30min_reset = current_time

    if current_time - last_hour_reset >= timedelta(hours=1):
        heatmap_grid_reset_hour.fill(0)
        last_hour_reset = current_time


    flights = fr_api.get_flights(bounds=f"{y1},{y2},{x1},{x2}")

    if flights:
        for flight in flights:
            lats = flight.latitude
            lons = flight.longitude
            if y2 <= lats <= y1 and x1 <= lons <= x2:
                lat_index, lon_index = get_grid_indices(lats, lons)
                
                # Update rolling accumulation
                heatmap_grid_rolling[lat_index, lon_index] += 1
                
                # Update 30-min and hourly grids
                heatmap_grid_reset_30min[lat_index, lon_index] += 1
                heatmap_grid_reset_hour[lat_index, lon_index] += 1
                
                # Store flight data with timestamp for rolling window removal
                flight_history.append((current_time, lat_index, lon_index))

    # Check for 30-min and hourly resets

    # Save heatmaps every 2 minutes
    save_heatmap(f"heatmap_rolling_{int(time.time())}.png", heatmap_grid_rolling, "rolling", cmap_max=10)
    save_heatmap(f"heatmap_reset_30min_{int(time.time())}.png", heatmap_grid_reset_30min, "reset_30min", cmap_max=10)
    save_heatmap(f"heatmap_reset_hour_{int(time.time())}.png", heatmap_grid_reset_hour, "reset_hour", cmap_max=10)

# Main loop: update every 2 minutes
while True:
    fetch_flights_and_update_heatmaps()
    print("Updated heatmaps")
    time.sleep(120)

# Close the database connection (this line will not be reached in this infinite loop)
db_connection.close()
