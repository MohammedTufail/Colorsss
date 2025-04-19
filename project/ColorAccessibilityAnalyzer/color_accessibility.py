from flask import Flask, request, jsonify, send_from_directory, redirect, url_for
from flask_cors import CORS
import os
import numpy as np
from werkzeug.utils import secure_filename
from PIL import Image
from datetime import datetime
import colorsys

# Create Flask app with explicit static folder configuration
app = Flask(__name__, static_folder='static', static_url_path='/static')

# Configure CORS to allow requests from any origin
CORS(app, resources={r"/*": {"origins": "*"}})

# Configure upload directory
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Ensure upload directory exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # Limit uploads to 10MB

# Colorblindness simulation matrices
color_matrices = {
    'protanopia': np.array([
        [0.567, 0.433, 0.000],
        [0.558, 0.442, 0.000],
        [0.000, 0.242, 0.758]
    ]),
    'deuteranopia': np.array([
        [0.625, 0.375, 0.000],
        [0.700, 0.300, 0.000],
        [0.000, 0.300, 0.700]
    ]),
    'tritanopia': np.array([
        [0.950, 0.050, 0.000],
        [0.000, 0.433, 0.567],
        [0.000, 0.475, 0.525]
    ])
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb):
    return f'#{int(rgb[0]):02x}{int(rgb[1]):02x}{int(rgb[2]):02x}'

def extract_dominant_colors(image, n_colors=5):
    small_image = image.resize((100, 100))
    pixels = np.array(small_image).reshape(-1, 3)
    pixels = (pixels // 16) * 16
    unique_colors, counts = np.unique(pixels, axis=0, return_counts=True)
    sorted_indices = np.argsort(-counts)
    dominant_colors = unique_colors[sorted_indices][:n_colors]
    hex_colors = [rgb_to_hex(color) for color in dominant_colors]
    return hex_colors

def suggest_alternative_colors(colors):
    alternatives = {}
    for color in colors:
        rgb = hex_to_rgb(color)
        h, l, s = colorsys.rgb_to_hls(rgb[0]/255, rgb[1]/255, rgb[2]/255)
        new_h = (h + 0.5) % 1.0
        new_r, new_g, new_b = colorsys.hls_to_rgb(new_h, l, s)
        alt_color = rgb_to_hex((int(new_r*255), int(new_g*255), int(new_b*255)))
        alternatives[color] = alt_color
    return alternatives

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

@app.route('/uploads/<path:filename>')
def serve_upload_direct(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'image' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        base_filename, ext = os.path.splitext(filename)

        # Save original image
        original_filename = f"{base_filename}_original_{timestamp}{ext}"
        original_path = os.path.join(app.config['UPLOAD_FOLDER'], original_filename)
        file.save(original_path)
        
        try:
            pil_image = Image.open(original_path).convert('RGB')
            image_np = np.array(pil_image).astype(float) / 255.0

            # Extract dominant colors and suggestions
            dominant_colors = extract_dominant_colors(pil_image)
            suggested_colors = suggest_alternative_colors(dominant_colors)

            # Use direct path to image
            results = {
                'originalImage': f"/uploads/{original_filename}",
                'simulations': {},
                'dominantColors': dominant_colors,
                'suggestedColors': suggested_colors
            }

            for mode, matrix in color_matrices.items():
                reshaped = image_np.reshape(-1, 3)
                transformed = reshaped @ matrix.T
                transformed = np.clip(transformed, 0, 1)
                transformed_img = (transformed.reshape(image_np.shape) * 255).astype(np.uint8)

                simulated_pil = Image.fromarray(transformed_img)
                simulated_filename = f"{base_filename}_{mode}_simulated_{timestamp}{ext}"
                simulated_path = os.path.join(app.config['UPLOAD_FOLDER'], simulated_filename)
                simulated_pil.save(simulated_path)
                
                # Use direct path for simulations
                results['simulations'][mode] = f"/uploads/{simulated_filename}"

            # Print paths for debugging
            print(f"Original image path: {original_path}")
            print(f"Original image URL: {results['originalImage']}")
            for mode, url in results['simulations'].items():
                print(f"{mode} simulation URL: {url}")
                
            return jsonify(results)
            
        except Exception as e:
            print(f"Error processing image: {str(e)}")
            return jsonify({'error': f'Error processing image: {str(e)}'}), 500

    return jsonify({'error': 'File type not allowed'}), 400

# Debug route to check if files exist
@app.route('/api/check-file/<path:filename>')
def check_file(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(filepath):
        return jsonify({
            'exists': True,
            'size': os.path.getsize(filepath),
            'full_path': os.path.abspath(filepath)
        })
    else:
        return jsonify({
            'exists': False,
            'searched_path': os.path.abspath(filepath)
        }), 404

if __name__ == '__main__':
    # Print important paths for debugging
    print(f"Current working directory: {os.getcwd()}")
    print(f"Static folder path: {app.static_folder}")
    print(f"Upload folder path: {app.config['UPLOAD_FOLDER']}")
    app.run(debug=True, host='0.0.0.0', port=5000)