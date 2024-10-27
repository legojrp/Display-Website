from FlightRadar24 import FlightRadar24API
import time
import matplotlib.pyplot as plt
import numpy as np

# Initialize the API
fr_api = FlightRadar24API()

# Define the geographic boundaries of the United States
min_lat = 25    # Southern boundary of the U.S.
max_lat = 49    # Northern boundary of the U.S.
min_lon = -125  # Western boundary of the U.S.
max_lon = -75   # Eastern boundary of the U.S.

# Number of strips and grid resolution
num_strips = 10
grid_resolution = 100

# Calculate the height of each strip
strip_height = (max_lat - min_lat) / num_strips

# Create a figure for the heatmap
plt.figure(figsize=(12, 8))
plt.title("Flight Density Heatmap Across the United States")
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.grid()

# Create a grid to accumulate flight counts
heatmap_grid = np.zeros((grid_resolution, grid_resolution))

# Function to get grid indices
def get_grid_indices(lat, lon):
    lat_index = int((lat - min_lat) / (max_lat - min_lat) * (grid_resolution - 1))
    lon_index = int((lon - min_lon) / (max_lon - min_lon) * (grid_resolution - 1))
    return lat_index, lon_index

def accumulate_flight_data():
    # Plot flights for each strip
    for i in range(num_strips):
        lat_bottom = min_lat + i * strip_height
        lat_top = lat_bottom + strip_height
        
        # Fetch flights in the current strip
        flights = fr_api.get_flights(bounds=f"{lat_top},{lat_bottom},{min_lon},{max_lon}")
        
        if flights:
            for flight in flights:
                lats = flight.latitude
                lons = flight.longitude
                
                # Check if the flight's coordinates are within the bounds of the U.S.
                if min_lat <= lats <= max_lat and min_lon <= lons <= max_lon:
                    lat_index, lon_index = get_grid_indices(lats, lons)
                    heatmap_grid[lat_index, lon_index] += 1  # Increment the count in the grid

# Main loop: update the flight data periodically
while True:
    plt.clf()  # Clear the current plot
    accumulate_flight_data()  # Accumulate flight data for the heatmap

    # Apply logarithmic transformation to the heatmap grid
    heatmap_log = np.log1p(heatmap_grid)  # log1p is used to handle zero values

    # Create the heatmap
    plt.imshow(heatmap_log, cmap='hot', interpolation='nearest', origin='lower',
               extent=[min_lon, max_lon, min_lat, max_lat])
    
    plt.colorbar(label="Log Flight Density")
    plt.title("Flight Density Heatmap Across the United States")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    print("Updated heatmap")
    plt.pause(60)  # Wait for 1 minute before refreshing

# Show the final plot
plt.show()
