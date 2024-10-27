from flask import Flask
from flask_cors import CORS
from flask import jsonify
from RainViewerAPI import RainViewerAPI
from flask import request

rv_api = RainViewerAPI()

app = Flask(__name__)
CORS(app, resources={r"*": {"origins": "*"}})

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add("Content-Type", "application/json")
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    response.headers.add('Access-Control-Max-Age', '0')
    return response

@app.route('/', methods=['POST'])
def hello():
    data = request.get_json()
    print(data)
    if data["ipad"] == "1":
        return jsonify({'screen': 'weather', "theme": "dark"}), 200
    else :
        return jsonify({'screen': 'flights', "theme": "light"}), 200

    return jsonify({'screen': 'weather', "theme": "dark"}), 200

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
        radar['url'] = rv_api.construct_image_url(radar['path'], 1024, zoom, lat, lon, 4, "0_0")

    response["bounds"] = rv_api.calculate_bounds(lat, lon, zoom)
    response["coords"] = {
        "lat": lat,
        "lon": lon,
        "zoom": zoom
    }
    return jsonify(response)


@app.route("/flights")
def flights():

    return jsonify("Hello, World!")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=True)

