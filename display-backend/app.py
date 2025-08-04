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
from pictures.picture_handler import save_uploaded_picture
from pictures.picture_handler import get_pictures_algorithmically
from pictures.picture_handler import update_picture_likes
from pictures.picture_handler import toggle_picture_visibility

# Load environment variables from .env file
load_dotenv()


app = Flask(__name__)
CORS(app, resources={r"*": {"origins": "*"}})

BASE_PATH = os.path.join(os.path.dirname(__file__))

def rss_aggregate_and_rank():
    if (os.getenv("run_rss_aggregator", "False").lower() != "true"):
        print("RSS Aggregation and Ranking is disabled.")
        return
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
@app.route("/pictures", methods=['POST'])
def ipad5():
    data = request.get_json()
    return jsonify({'screen': 'pictures', "theme": "dark"}), 200

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

@app.route('/pictures/get_pictures', methods=['GET'])
def get_pictures_endpoint():
    """
    Endpoint to retrieve pictures from the system
    """
    try:
        
        # Get optional parameters if any
        limit = request.args.get('limit', default=10, type=int)
        
        # Get pictures from the handler
        pictures = get_pictures_algorithmically(limit=limit)

        return jsonify({
            'success': True,
            'pictures': pictures
        })
    except Exception as e:
        print(f"Error retrieving pictures: {str(e)}")
        return jsonify({'error': f'Failed to retrieve pictures: {str(e)}'}), 500

@app.route("/pictures/upload_picture", methods=['POST'])
def upload_picture():
    """
    Endpoint to receive uploaded pictures in base64 format
    """
    if 'picture' not in request.json:
        return jsonify({'error': 'No picture provided'}), 400
    
    try:
        # Get base64 encoded image from request
        base64_image = request.json['picture']
        
        # Extract metadata if available
        title = request.json.get('title', 'Untitled')
        description = request.json.get('description', '')
        
        # Import the picture handler function (to be implemented)
        
        # Save the picture and get result
        result = save_uploaded_picture(base64_image, title, description)
        
        return jsonify({'success': True, 'message': 'Picture uploaded successfully', 'data': result}), 200
    
    except Exception as e:
        print(f"Error handling picture upload: {str(e)}")
        return jsonify({'error': f'Failed to process uploaded picture: {str(e)}'}), 500

@app.route("/pictures/like_picture", methods=['POST'])
def like_picture():
    """
    Endpoint to like a picture.
    """
    if 'filename' not in request.json:
        return jsonify({'error': 'No filename provided'}), 400

    filename = request.json['filename']
    result = update_picture_likes(filename, increment=True)

    return jsonify(result)

@app.route("/pictures/toggle_picture_visibility", methods=['POST'])
def toggle_picture_visibility():
    """
    Endpoint to toggle the visibility of a picture.
    """
    if 'filename' not in request.json:
        return jsonify({'error': 'No filename provided'}), 400

    filename = request.json['filename']
    result = toggle_picture_visibility(filename)

    return jsonify(result)

@app.route("/pictures/<filename>", methods=['GET'])
def serve_picture(filename):
    """
    Endpoint to serve picture files.
    """
    try:
        # Construct the file path - now looking in uploads subfolder
        file_path = os.path.join(BASE_PATH, "pictures", "uploads", filename)
        
        # Check if file exists
        if not os.path.exists(file_path):
            abort(404)
        
        # Serve the file
        return send_file(file_path, mimetype='image/png')
    except Exception as e:
        print(f"Error serving picture {filename}: {str(e)}")
        abort(500)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=True)

