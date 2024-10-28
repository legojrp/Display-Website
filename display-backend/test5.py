from FlightRadar24 import FlightRadar24API
import matplotlib.pyplot as plt
import numpy as np
import os
import time
from datetime import datetime, timedelta

# Initialize the API
fr_api = FlightRadar24API()

# Define the geographic boundaries of the United States
y1, y2, x1, x2 = 49, 24, -125, -60  # (max_lat, min_lat, min_lon, max_lon)

# Create folders to save heatmap images
output_folder_accum = "flight_heatmaps_accum"
output_folder_reset = "flight_heatmaps_reset"
os.makedirs(output_folder_accum, exist_ok=True)
os.makedirs(output_folder_reset, exist_ok=True)

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

    # Create and save the accumulating heatmap
    plt.figure(figsize=(12, 8))  # Set figure size for better quality
    plt.imshow(heatmap_grid_accum, cmap='hot', interpolation='nearest', origin='lower',
               extent=[x1, x2, y2, y1], aspect='auto')  # Use aspect='auto' for proper scaling
    plt.axis('off')  # Turn off the axis
    plt.savefig(os.path.join(output_folder_accum, f"heatmap_accum_{int(time.time())}.png"), bbox_inches='tight', pad_inches=0, dpi=300)  # Set dpi for better quality
    plt.close()

    # Reset the resetting heatmap if the current time is divisible by 30 minutes
    if current_time.minute % 30 == 0 and current_time.second == 0:  # Check if it's the start of a new 30-minute interval
        heatmap_grid_reset.fill(0)  # Reset the grid
        print("Resetting the 30-minute heatmap")

    # Create and save the resetting heatmap
    plt.figure(figsize=(12, 8))  # Set figure size for better quality
    plt.imshow(heatmap_grid_reset, cmap='hot', interpolation='nearest', origin='lower',
               extent=[x1, x2, y2, y1], aspect='auto')  # Use aspect='auto' for proper scaling
    plt.axis('off')  # Turn off the axis
    plt.savefig(os.path.join(output_folder_reset, f"heatmap_reset_{int(time.time())}.png"), bbox_inches='tight', pad_inches=0, dpi=300)  # Set dpi for better quality
    plt.close()

# Main loop: update every 2 minutes
while True:
    fetch_flights_and_update_heatmaps()  # Fetch flights and update heatmaps
    
    # Wait for 2 minutes before the next iteration
    print("Updated heatmaps")
    time.sleep(120)  # Sleep for 2 minutes (120 seconds)
