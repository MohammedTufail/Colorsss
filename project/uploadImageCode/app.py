from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS
import cv2
import numpy as np
import pandas as pd
import os
import base64
from io import BytesIO
from PIL import Image
import uuid
from datetime import datetime
from pymongo import MongoClient
from bson.binary import Binary
from bson import json_util
import tempfile  # Ensure this is at the top

# ML Imports
from sklearn.neighbors import KNeighborsRegressor

app = Flask(__name__)
CORS(app)

# MongoDB Setup
client = MongoClient('mongodb+srv://hyderabadwalamohammed:hyderabadwala17@cluster0.tvyjhoo.mongodb.net/') 
db = client['color_detector']
images_collection = db['images']
results_collection = db['results']

# Load color database from c.csv
index = ["color", "color_name", "hex", "R", "G", "B"]
color_csv_path = os.path.join(os.path.dirname(__file__), 'c.csv')
csv = pd.read_csv(color_csv_path, names=index, header=None)

X = csv[["R", "G", "B"]]
y = csv[["R", "G", "B"]]

# Train KNN model
knn_model = KNeighborsRegressor(n_neighbors=3)
knn_model.fit(X, y)

# Helper: find closest color name
def get_closest_color_name(R, G, B):
    minimum = float('inf')
    cname = ""
    hex_code = ""
    for i in range(len(csv)):
        d = abs(R - int(csv.loc[i, "R"])) + abs(G - int(csv.loc[i, "G"])) + abs(B - int(csv.loc[i, "B"]))
        if d < minimum:
            minimum = d
            cname = csv.loc[i, "color_name"]
            hex_code = csv.loc[i, "hex"]
    return cname, hex_code

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_media():
    if 'media' not in request.files:
        return jsonify({'error': 'No media uploaded'}), 400

    file = request.files['media']
    filename = file.filename

    if filename == '':
        return jsonify({'error': 'No file selected'}), 400

    file_content = file.read()
    extension = filename.split('.')[-1].lower()

    if extension in ['jpg', 'jpeg', 'png']:
        img = cv2.imdecode(np.frombuffer(file_content, np.uint8), cv2.IMREAD_COLOR)
        success = True
    elif extension in ['mp4', 'avi', 'mov']:
        # Create temp file safely across OS
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f".{extension}")
        temp_path = temp_file.name
        temp_file.write(file_content)
        temp_file.close()

        cap = cv2.VideoCapture(temp_path)
        success, img = cap.read()
        cap.release()
        os.remove(temp_path)

    else:
        return jsonify({'error': 'Unsupported file type'}), 400

    if not success or img is None:
        return jsonify({'error': 'Failed to extract frame from video'}), 500

    image_id = str(uuid.uuid4())
    _, buffer = cv2.imencode('.jpg', img)
    image_binary = Binary(buffer.tobytes())

    image_doc = {
        '_id': image_id,
        'filename': filename,
        'image': image_binary,
        'processed': False,
        'timestamp': datetime.now()
    }

    images_collection.insert_one(image_doc)
    return jsonify({'image_id': image_id})

@app.route('/detect/<image_id>/<int:x>/<int:y>', methods=['GET'])
def detect_color(image_id, x, y):
    try:
        image_doc = images_collection.find_one({'_id': image_id})
        if not image_doc:
            return jsonify({'error': 'Image not found'}), 404
        
        nparr = np.frombuffer(image_doc['image'], np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return jsonify({'error': 'Image could not be decoded'}), 500
        
        height, width = img.shape[:2]
        if not (0 <= x < width) or not (0 <= y < height):
            return jsonify({'error': f'Coordinates ({x}, {y}) are out of bounds'}), 400
        
        b, g, r = img[y, x]
        input_rgb = np.array([[r, g, b]])
        predicted_rgb = knn_model.predict(input_rgb).astype(int)[0]
        r_pred, g_pred, b_pred = predicted_rgb

        color_name, hex_code = get_closest_color_name(r_pred, g_pred, b_pred)

        result = {
            'image_id': image_doc['_id'],
            'x': x,
            'y': y,
            'color_name': color_name,
            'r': int(r_pred),
            'g': int(g_pred),
            'b': int(b_pred),
            'hex': hex_code,
            'timestamp': datetime.now()
        }

        return jsonify(result)

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'An error occurred while processing the image'}), 500

@app.route('/image/<image_id>')
def get_image(image_id):
    image_doc = images_collection.find_one({'_id': image_id})
    
    if not image_doc:
        return jsonify({'error': 'Image not found'}), 404
    
    binary_data = bytes(image_doc['image'])
    base64_data = base64.b64encode(binary_data).decode('utf-8')
    
    return jsonify({'image_data': f'data:image/jpeg;base64,{base64_data}'})

if __name__ == '__main__':
    app.run(debug=True)
