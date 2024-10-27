import requests
import json

class RainViewerAPI:
    def __init__(self):
        self.api_url = "https://api.rainviewer.com/public/weather-maps.json"
        self.data = self.fetch_data()

    def fetch_data(self):
        """Fetch the weather maps data from the API."""
        response = requests.get(self.api_url)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error fetching data: {response.status_code}")

    def get_version(self):
        """Return the API version."""
        return self.data.get('version')

    def get_generated_time(self):
        """Return the generated timestamp of the data."""
        return self.data.get('generated')

    def get_host(self):
        """Return the host URL for the images."""
        return self.data.get('host')

    def get_radar_data(self):
        """Return the radar data (past and nowcast)."""
        return self.data.get('radar')

    def get_satellite_data(self):
        """Return the satellite data (infrared)."""
        return self.data.get('satellite')

    def construct_image_url(self, path, size, z, x, y, color, options='0_0'):
        """Construct the URL for the radar image."""
        host = self.get_host()
        return f"{host}{path}/{size}/{z}/{x}/{y}/{color}/{options}.png"

    def construct_coverage_url(self, size, z, x, y):
        """Construct the URL for the radar coverage image."""
        host = self.get_host()
        return f"{host}/v2/coverage/0/{size}/{z}/{x}/{y}/0/0_0.png"
    def calculate_bounds(self, center_lat, center_lng, zoom_level):
        """
        Calculate the bounding box based on center point and zoom level.

        Parameters:
        center_lat (float): Latitude of the center point.
        center_lng (float): Longitude of the center point.
        zoom_level (int): Zoom level of the map.

        Returns:
        dict: A dictionary containing top left (northwest) and bottom right (southeast) coordinates.
        """
    
    # Calculate the size of the tile in degrees
        tile_width = 360 / (2 ** zoom_level)  # Width in degrees
        tile_height = 180 / (2 ** zoom_level)  # Height in degrees

        # Calculate the bounds
        north = center_lat + (tile_height / 1.70)
        south = center_lat - (tile_height / 1.10)
        east = center_lng + (tile_width / 2)
        west = center_lng - (tile_width / 2)

        # Return bounds in a dictionary
        return {
            "top_left": (north, west),        # Northwest corner
            "bottom_right": (south, east)     # Southeast corner
        }

# Example usage


# Example usage:
if __name__ == "__main__":
    rv_api = RainViewerAPI()
    print("API Version:", rv_api.get_version())
    print("Generated Time:", rv_api.get_generated_time())
    print("Host URL:", rv_api.get_host())
    print("Radar Data:", rv_api.get_radar_data())
    print("Satellite Data:", rv_api.get_satellite_data())

    # Construct an example radar image URL
    example_image_url = rv_api.construct_image_url(
        path="/v2/radar/1609401600", 
        size=512, 
        z=5, 
        x=10, 
        y=15, 
        color=0
    )
    print("Example Radar Image URL:", example_image_url)

    # Construct an example coverage URL
    example_coverage_url = rv_api.construct_coverage_url(size=512, z=5, x=10, y=15)
    print("Example Coverage URL:", example_coverage_url)
