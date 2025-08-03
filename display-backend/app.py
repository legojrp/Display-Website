from urllib import response
from flask import Flask
from flask_cors import CORS
from flask import jsonify
from RainViewerAPI import RainViewerAPI
from flask import request, send_file, abort
import os
import requests
from goesdata import get_goes19_image_base64
from rss_feeds.ai_interaction import GeminiArticleRanker
from rss_feeds.db_handler import DatabaseHandler
from rss_feeds.aggregator import RSSAggregator
import threading
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


app = Flask(__name__)
CORS(app, resources={r"*": {"origins": "*"}})

BASE_PATH = os.path.join(os.path.dirname(__file__))

def rss_aggregate_and_rank():
    agg = RSSAggregator(feeds_file="rss_feeds/feeds.json", db_path="rss_feeds/articles.db")
    agg.aggregate_all_feeds()
    ranker = GeminiArticleRanker(db_path="rss_feeds/articles.db", api_key=os.getenv("GEMINI_API_KEY"))
    ranker.rank_pending_articles()

def schedule_task(interval_seconds=1800):  # 1800 seconds = 30 minutes
    while True:
        rss_aggregate_and_rank()
        time.sleep(interval_seconds)

scheduler_thread = threading.Thread(target=schedule_task, daemon=True)
scheduler_thread.start()


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
    else: 
        return jsonify({'screen': 'weather', "theme": "dark"}), 200
@app.route('/weather', methods=['POST'])
def ipad1():
    data = request.get_json()
    return jsonify({'screen': 'weather', "theme": "dark"}), 200
@app.route('/earth', methods=['POST'])
def ipad2():
    data = request.get_json()
    return jsonify({'screen': 'earth', "theme": "dark"}), 200
@app.route("/radar", methods=['POST'])
def ipad3():
    data = request.get_json()
    return jsonify({'screen': 'radar', "theme": "dark"}), 200
@app.route("/news", methods=['POST'])
def ipad4():
    data = request.get_json()
    return jsonify({'screen': 'news', "theme": "dark"}), 200

@app.route("/weather")
def weather():
    """Return the radar and satellite frames as JSON."""
    rv_api = RainViewerAPI()
    # Get radar data
    radar_data = rv_api.get_radar_data()
    print(radar_data)
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


# @app.route("/flightsdata", methods=['POST'])
# def flightdata():
#     data = request.get_json()
#     type= data["type"]
#     duration = data["duration"]
#     if type == "reset_30_mins":
#         type = "reset_30min"
#     elif type == "reset_hour":
#         type = "reset_hour"

#     print(type, duration)
#     ani = HeatmapAnimation()
#     frames = ani.fetch_frames(duration, type)
#     return jsonify(frames)


@app.route("/radar-json", methods=['POST'])
def radar_json():
    try:
        response = requests.get("http://192.168.0.105:8754/flights.json", timeout=5)
        response.raise_for_status()

        return jsonify(response.json())
    except Exception as e:
        print("Error:", e)
        return jsonify({'error': str(e)}), 500
    
@app.route('/goes-image', methods=['GET'])
def goes_image():
    """
    Endpoint to get the latest GOES-16 CONUS image as a Base64 encoded PNG.
    """
    base64_image = get_goes19_image_base64()
    
    if base64_image is None:
        return jsonify({'error': 'Failed to fetch GOES image'}), 500
    
    return jsonify({'image': base64_image}), 200

@app.route('/get_news', methods=['GET'])
def get_news():
    agg = RSSAggregator(feeds_file="rss_feeds/feeds.json", db_path="rss_feeds/articles.db")
    articles = agg.fetch_articles_algorithmically()
    return jsonify(articles)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=True)

