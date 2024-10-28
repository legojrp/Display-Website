from flask import Flask
from flask_cors import CORS
from flask import jsonify
from RainViewerAPI import RainViewerAPI
from flask import request, send_file, abort
import os
from Heatmap import HeatmapAnimation

rv_api = RainViewerAPI()

app = Flask(__name__)
CORS(app, resources={r"*": {"origins": "*"}})

BASE_PATH_ACCUM = os.path.join(os.path.dirname(__file__))
BASE_PATH_RESET = os.path.join(os.path.dirname(__file__))

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    if not request.path.startswith('/heatmap/'):
        response.headers.add("Content-Type", "application/json")
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    response.headers.add('Access-Control-Max-Age', '0')
    return response

@app.route('/', methods=['POST'])
def hello():
    ip_addr = request.remote_addr
    if ip_addr == "192.168.0.154":
        return jsonify({'screen': 'flights', "theme": "dark"}), 200
    elif ip_addr == "192.168.0.170":
        return jsonify({'screen': 'weather', "theme": "dark"}), 200
    elif ip_addr == "127.0.0.1":
        return jsonify({'screen': 'display', "theme": "dark"}), 200
@app.route('/ipad1', methods=['POST'])
def ipad1():
    data = request.get_json()
    print(data)
    return jsonify({'screen': 'weather', "theme": "dark"}), 200
@app.route('/ipad2', methods=['POST'])
def ipad2():
    data = request.get_json()
    print(data)
    return jsonify({'screen': 'flights', "theme": "dark"}), 200

@app.route("/weather")
def weather():
    """Return the radar and satellite frames as JSON."""
    # Get radar data
    radar_data = rv_api.get_radar_data()
    # Get satellite data
    satellite_data = rv_api.get_satellite_data()

    # Construct the response
    response = {
        'radar': radar_data,
        'satellite': satellite_data
    }
    # zoom = 2
    # lat = 38.07869920252731
    # lon = -91.88596798893897

    zoom = 2
    lat = 38.42745317167635 
    lon =  -96.99083870738689

    for radar in response['radar']["past"]:
        radar['url'] = rv_api.construct_image_url(radar['path'], 1024, zoom, lat, lon, 1, "0_0")

    response["bounds"] = rv_api.calculate_bounds(lat, lon, zoom)
    response["coords"] = {
        "lat": lat,
        "lon": lon,
        "zoom": zoom
    }
    return jsonify(response)


@app.route("/flights")
def flights():
    ani = HeatmapAnimation()
    frames = ani.fetch_frames("past_6_hours", "accum")
    print(frames)
    return jsonify(frames)


@app.route('/heatmap/<frame_type>/<int:timestamp>.png')
def serve_heatmap(frame_type, timestamp):
    """
    Serve heatmap image based on frame type and timestamp.
    :param frame_type: Type of heatmap ('accum' or 'reset').
    :param timestamp: Timestamp of the heatmap image.
    :return: The heatmap image file or 404 if not found.
    """
    if frame_type not in ['accum', 'reset']:
        abort(402)  # Invalid frame type

    # Get the heatmap file name from the database
    file_name = HeatmapAnimation().get_heatmap_path(frame_type, timestamp)
    if file_name is None:
        abort(403)  # Not found in database

    # Determine the base path based on the frame type
    if frame_type == 'accum':
        folder_path = BASE_PATH_ACCUM
    else:  # frame_type == 'reset'
        folder_path = BASE_PATH_RESET

    # Construct the full file path
    full_path = os.path.join(folder_path, file_name)

    print(full_path)
    # Serve the file
    if os.path.exists(full_path):
        
        return send_file(full_path, mimetype='image/png')
    else:
        abort(404) 


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=True)

