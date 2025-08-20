import io
import datetime
import xarray as xr
import matplotlib
# Use the 'Agg' backend for non-interactive environments to prevent crashes.
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import numpy as np
import base64

# NOTE: In a real environment, you would need to install the following libraries:
# pip install goes2go
# pip install s3fs
#
# Since this environment does not have external library access, this code
# is a demonstration of how a programmer would implement the functionality.
import goes2go.data

goes2go.data.cache = None

def get_goes19_image_base64():
    """
    Fetches the latest GOES-19 satellite True Color data using the `goes2go`
    library, plots it with the correct geostationary projection, and returns
    the image as a Base64 encoded string. The image is cropped to the CONUS
    region, and all titles and extra whitespace are removed.

    Returns:
        str: A Base64 encoded string of the PNG image data if successful,
             otherwise None.
    """
    try:
        print(f"[{datetime.datetime.now()}] Attempting to fetch the latest GOES-19 data.")
        
        # --- Fetch the real data using goes2go ---
        # The 'ABI-L2-MCMIP' product contains all channels needed for True Color.
        # 'domain='C'' fetches a CONUS (Contiguous United States) image.
        goes_data = goes2go.data.goes_latest(
            satellite=19,
            product='ABI-L2-MCMIP',
            domain='C'
        )

        if goes_data is None:
            print(f"[{datetime.datetime.now()}] Error: goes_latest() returned None. Data retrieval failed.")
            return None
        
        print(f"[{datetime.datetime.now()}] Data successfully retrieved for GOES-19.")
        
        # --- Create the True Color composite using the built-in accessor ---
        # The `goes2go` library provides a convenient method to handle the
        # creation of the TrueColor composite, which includes applying
        # gamma correction and other necessary steps.
        rgb_composite = goes_data.rgb.TrueColor()
        
        # --- Plotting and encoding logic ---
        print(f"[{datetime.datetime.now()}] Starting image generation for GOES-19.")

        geostationary_projection = goes_data.goes_imager_projection
        sat_height = geostationary_projection.perspective_point_height
        sat_lon = geostationary_projection.longitude_of_projection_origin
        sat_sweep = geostationary_projection.sweep_angle_axis
        
        crs = ccrs.Geostationary(
            central_longitude=sat_lon,
            satellite_height=sat_height,
            sweep_axis=sat_sweep
        )

        latest_time = goes_data.t.dt.strftime('%Y-%m-%d %H:%M:%S').item()

        # Adjust figsize and dpi for iPad Pro resolution (e.g., 2048x1536)
        # We use a dpi of 256 and a figsize of (6, 8) to get a 1536x2048 pixel image.
        fig = plt.figure(figsize=(6, 8), dpi=256)
        ax = fig.add_subplot(1, 1, 1, projection=crs)
        
        # Plot the real data from the `goes2go` library
        # The data is now a single DataArray with a color dimension
        ax.imshow(
            rgb_composite.values,
            origin='upper',
            extent=(
                goes_data.x.min().item(), goes_data.x.max().item(),
                goes_data.y.min().item(), goes_data.y.max().item()
            ),
            transform=crs
        )

        # Add coastlines for context within the zoomed-in view
        ax.coastlines(resolution='50m', color='white', linewidth=1)

        # Remove axes and ticks to clean up the display
        ax.axis('off')

        img_buffer = io.BytesIO()
        
        # Save the figure with no padding and tight bounding box
        # The `transparent=True` argument makes the background pixels invisible.
        fig.tight_layout(pad=0)
        plt.savefig(img_buffer, format='png', bbox_inches='tight', pad_inches=0, dpi=256, transparent=True)
        plt.close(fig)

        img_buffer.seek(0)
        
        base64_image = base64.b64encode(img_buffer.getvalue()).decode('utf-8')

        print(f"[{datetime.datetime.now()}] Image data generated and base64 encoded for GOES-19.")
        return base64_image
        
    except Exception as e:
        print(f"[{datetime.datetime.now()}] An error occurred: {e}")
        return None
