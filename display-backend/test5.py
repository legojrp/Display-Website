from FlightRadar24 import FlightRadar24API
import matplotlib.pyplot as plt
import numpy as np
import os
import time
from datetime import datetime, timedelta

# Initialize the API
fr_api = FlightRadar24API()

# Define the geographic boundaries of the United States
min_lat = 25    # Southern boundary of the U.S.
max_lat = 49    # Northern boundary of the U.S.
min_lon = -125  # Western boundary of the U.S.
max_lon = -75   # Eastern boundary of the U.S.

# Create a folder to save heatmap images
output_folder = "flight_heatmaps"
os.makedirs(output_folder, exist_ok=True)

# Create a grid to accumulate flight counts
grid_resolution = 100
heatmap_grid = np.zeros((grid_resolution, grid_resolution))  # Initialize heatmap grid
flight_history = []  # Store flight data and timestamps

# Function to get grid indices
def get_grid_indices(lat, lon):
    lat_index = int((lat - min_lat) / (max_lat - min_lat) * (grid_resolution - 1))
    lon_index = int((lon - min_lon) / (max_lon - min_lon) * (grid_resolution - 1))
    return lat_index, lon_index

def fetch_flights_and_update_heatmap():
    # Get the current time
    current_time = datetime.now()

    # Fetch flights currently in the air
    flights = fr_api.get_flights(bounds=f"{max_lat},{min_lat},{min_lon},{max_lon}")

    # Update heatmap grid and track flight history
    if flights:
        for flight in flights:
            lats = flight.latitude
            lons = flight.longitude
            
            # Check if the flight's coordinates are within the bounds of the U.S.
            if min_lat <= lats <= max_lat and min_lon <= lons <= max_lon:
                lat_index, lon_index = get_grid_indices(lats, lons)
                heatmap_grid[lat_index, lon_index] += 1  # Increment the count in the grid
                
                # Store flight data with its timestamp
                flight_history.append((current_time, lat_index, lon_index))

    # Remove contributions older than one hour from the heatmap grid
    one_hour_ago = current_time - timedelta(hours=0.5)
    
    # Decrement counts in the grid for old flights
    for timestamp, lat_index, lon_index in flight_history:
        if timestamp < one_hour_ago:
            heatmap_grid[lat_index, lon_index] -= 1  # Decrement count for old data
    
    # Filter out old flight history entries
    flight_history[:] = [entry for entry in flight_history if entry[0] >= one_hour_ago]

    # Apply logarithmic transformation to the heatmap grid
    heatmap_log = np.log1p(heatmap_grid)  # log1p is used to handle zero values

    # Create the heatmap
    plt.imshow(heatmap_log, cmap='hot', interpolation='nearest', origin='lower',
               extent=[min_lon, max_lon, min_lat, max_lat])
    
    plt.colorbar(label="Log Flight Density")
    plt.title(f"Flight Density Heatmap at {current_time.strftime('%Y-%m-%d %H:%M')}")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    
    # Save the figure
    filename = os.path.join(output_folder, f"heatmap_{current_time.strftime('%Y%m%d_%H%M')}.png")
    plt.savefig(filename)
    plt.close()  # Close the figure to avoid memory issues

# Main loop: update every 2 minutes
while True:
    fetch_flights_and_update_heatmap()  # Fetch flights and update heatmap
    
    # Wait for 2 minutes before the next iteration
    print("Updated heatmap")
    time.sleep(120)  # Sleep for 2 minutes (120 seconds)
