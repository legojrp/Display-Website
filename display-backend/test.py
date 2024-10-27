import requests
from io import BytesIO
from PIL import Image
import matplotlib.pyplot as plt
from RainViewerAPI import RainViewerAPI  # Ensure you have the rainviewer.py in the same directory or adjust the import.

def fetch_static_map(lat, lon, zoom, size=(512, 512)):
    # OpenStreetMap static tile server
    url = f"https://tile.openstreetmap.org/{zoom}/{lat}/{lon}.png"
    response = requests.get(url)

    if response.status_code == 200:
        return Image.open(BytesIO(response.content))
    else:
        print("Error fetching static map:", response.status_code)
        return None

def overlay_radar_on_map(radar_image, background_map):
    # Combine radar image and background map
    radar_image = radar_image.convert("RGBA")
    background_map = background_map.convert("RGBA")
    
    combined = Image.alpha_composite(background_map, radar_image)
    return combined

def main():
    # Fetch radar data
    rv_api = RainViewerAPI()
    radar_data = rv_api.get_radar_data()
    past_frames = radar_data['past']

    if past_frames:
        most_recent_frame = past_frames[0]
        path = most_recent_frame['path']

        # Define parameters for the radar image
        size = 512  # Size of the image
        z = 5  # Zoom level
        x = 10  # X coordinate for the tile (adjust for coverage)
        y = 10  # Y coordinate for the tile (adjust for coverage)
        color = 0  # Color scheme

        # Construct the URL for the radar image
        radar_image_url = rv_api.construct_image_url(path, size, z, x, y, color)

        # Fetch the radar image
        radar_response = requests.get(radar_image_url)

        if radar_response.status_code == 200:
            radar_image = Image.open(BytesIO(radar_response.content))
        else:
            print("Error fetching radar image:", radar_response.status_code)
            return

        # Fetch a static map image of the United States
        lat = 37.1  # Approximate latitude for the USA
        lon = -95.7  # Approximate longitude for the USA
        zoom = 4  # Adjust zoom level to capture the entire US
        background_map = fetch_static_map(lat, lon, zoom)

        if background_map:
            # Overlay the radar image on the background map
            combined_image = overlay_radar_on_map(radar_image, background_map)
            combined_image.show()  # Display the combined image
            combined_image.save("combined_map.png")  # Save the combined image
            print("Combined map saved as combined_map.png")
        else:
            print("Failed to fetch the background map.")

if __name__ == "__main__":
    main()
