from flask import Flask, render_template, jsonify, request, Response 
from flask_cors import CORS
import cv2
import numpy as np
import pandas as pd
from sklearn.neighbors import KNeighborsRegressor
from datetime import datetime
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*", "methods": ["GET", "POST", "OPTIONS"], "allow_headers": ["Content-Type"]}})

# Load color database
index = ["color", "color_name", "hex", "R", "G", "B"]
color_csv_path = 'c.csv'

if not os.path.exists(color_csv_path):
    print(f"Warning: {color_csv_path} not found. Using sample data.")
    sample_data = [
        [1, "red", "#FF0000", 255, 0, 0],
        [2, "green", "#00FF00", 0, 255, 0],
        [3, "blue", "#0000FF", 0, 0, 255],
    ]
    csv = pd.DataFrame(sample_data, columns=index)
else:
    csv = pd.read_csv(color_csv_path, names=index, header=None)

X = csv[["R", "G", "B"]]
y = csv[["R", "G", "B"]]

# Train KNN model
knn_model = KNeighborsRegressor(n_neighbors=3)
knn_model.fit(X, y)

# Camera state
video_capture = None
camera_running = False

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

def initialize_camera():
    global video_capture, camera_running
    if not camera_running:
        video_capture = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        if not video_capture.isOpened():
            raise RuntimeError("Could not start camera")
        camera_running = True
    return video_capture

def release_camera():
    global video_capture, camera_running
    if video_capture is not None and video_capture.isOpened():
        video_capture.release()
    cv2.destroyAllWindows()
    cv2.waitKey(1)
    video_capture = None
    camera_running = False

def gen_frames():
    global video_capture, camera_running
    try:
        initialize_camera()
        while camera_running:
            success, frame = video_capture.read()
            if not success:
                print("Failed to capture frame")
                break
            else:
                ret, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
    except Exception as e:
        print(f"Error in gen_frames: {e}")
        yield (b'--frame\r\n'
               b'Content-Type: text/plain\r\n\r\n' + str(e).encode() + b'\r\n\r\n')

@app.route('/')
def index():
    return "Color Detection API is running"

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/live_color_data', methods=['GET', 'POST', 'OPTIONS'])
def live_color_data():
    if request.method == 'OPTIONS':
        response = app.make_default_options_response()
        return response

    if request.method == 'POST':
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data received'}), 400

            x = int(data.get('x', 0))
            y = int(data.get('y', 0))

            cam = initialize_camera()
            success, frame = cam.read()
            if not success:
                return jsonify({'error': 'Failed to capture frame'}), 500

            height, width = frame.shape[:2]
            if not (0 <= x < width) or not (0 <= y < height):
                return jsonify({'error': f'Coordinates ({x}, {y}) are out of bounds'}), 400

            b, g, r = frame[y, x]
            input_rgb = np.array([[r, g, b]])

            predicted_rgb = knn_model.predict(input_rgb).astype(int)[0]
            r_pred, g_pred, b_pred = predicted_rgb

            color_name, hex_code = get_closest_color_name(r_pred, g_pred, b_pred)

            result = {
                'name': color_name,
                'hex': hex_code,
                'rgb': {'r': int(r_pred), 'g': int(g_pred), 'b': int(b_pred)},
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            return jsonify(result)
        except Exception as e:
            print(f"Error in live_color_data: {e}")
            return jsonify({'error': str(e)}), 500

    return jsonify({'error': 'Method not allowed'}), 405

@app.route('/setup', methods=['GET', 'POST', 'OPTIONS'])
def setup():
    if request.method == 'OPTIONS':
        response = app.make_default_options_response()
        return response
    try:
        initialize_camera()
        return jsonify({'status': 'Camera initialized successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/teardown', methods=['GET', 'POST', 'OPTIONS'])
def teardown():
    if request.method == 'OPTIONS':
        response = app.make_default_options_response()
        return response
    try:
        release_camera()
        return jsonify({'status': 'Camera released successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/camera_status', methods=['GET'])
def camera_status():
    return jsonify({'camera_running': camera_running})

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    try:
        print("Starting Flask server...")
        app.run(debug=True, port=5000, host='0.0.0.0')
    finally:
        release_camera()
