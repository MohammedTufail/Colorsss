from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
import numpy as np
from sklearn.cluster import KMeans

app = Flask(__name__)
CORS(app)

@app.route("/extract_palette", methods=["POST"])
def extract_palette():
    file = request.files['image']
    x = int(float(request.form['x']))
    y = int(float(request.form['y']))
    width = int(float(request.form['width']))
    height = int(float(request.form['height']))

    image = Image.open(file).convert("RGB")
    cropped = image.crop((x, y, x + width, y + height))
    img_data = np.array(cropped).reshape((-1, 3))

    kmeans = KMeans(n_clusters=10, random_state=0).fit(img_data)
    unique, counts = np.unique(kmeans.labels_, return_counts=True)

    total = sum(counts)
    result = []
    for cluster_index, count in zip(unique, counts):
        r, g, b = kmeans.cluster_centers_[cluster_index].astype(int)
        hex_color = "#{:02x}{:02x}{:02x}".format(r, g, b)
        proportion = count / total
        result.append({"color": hex_color, "proportion": proportion})

    result = sorted(result, key=lambda c: c["proportion"], reverse=True)[:10]
    return jsonify(result)

if __name__ == "__main__":
    app.run(port=5003)
