import cv2
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsRegressor, NearestNeighbors
from sklearn.metrics import mean_squared_error

# ----------- Load and Train Models -----------

# Load color dataset (assuming no headers in the CSV)
df = pd.read_csv("c.csv", header=None)
df.columns = ["names", "NAMES_PRETTY", "hex", "R", "G", "B"]

# Prepare input (X) and output (y)
X = df[["R", "G", "B"]]
y = df[["R", "G", "B"]]
color_names = df["names"].values
hex_codes = df["hex"].values

# Train-test split (for evaluation only)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train KNN regressor
knn_model = KNeighborsRegressor(n_neighbors=3)
knn_model.fit(X_train, y_train)

# Train nearest neighbor model to find closest color name
nn_model = NearestNeighbors(n_neighbors=1)
nn_model.fit(X)

# ----------- Live Camera Setup -----------

clicked_info = {"color": (0, 0, 0), "name": "", "hex": ""}

def get_color_name(event, x, y, flags, param):
    global clicked_info, frame
    if event == cv2.EVENT_LBUTTONDOWN:
        b, g, r = frame[y, x]
        input_rgb = np.array([[r, g, b]])

        predicted_rgb = knn_model.predict(input_rgb).astype(int)
        dist, idx = nn_model.kneighbors(predicted_rgb)

        name = color_names[idx[0][0]]
        hexcode = hex_codes[idx[0][0]]
        clean_rgb = tuple(int(x) for x in predicted_rgb[0])

        clicked_info["color"] = clean_rgb
        clicked_info["name"] = name
        clicked_info["hex"] = hexcode

        print(f" Predicted Clean RGB: {clean_rgb}")
        print(f"Closest Color: {name} ({hexcode})")

# OpenCV window setup
cv2.namedWindow("Color Detector")
cv2.setMouseCallback("Color Detector", get_color_name)

cap = cv2.VideoCapture(0)

print("Live camera started. Click anywhere on the video to detect color. Press 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Draw a color box and resize to match frame width
    color_display = np.zeros((100, frame.shape[1], 3), dtype=np.uint8)
    color_display[:] = clicked_info["color"][::-1]  # RGB to BGR

    # Add text on the color box
    cv2.putText(color_display, f"{clicked_info['name']} ({clicked_info['hex']})",
                (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    cv2.putText(color_display, f"Predicted RGB: {clicked_info['color']}", 
                (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    # Stack the video and color info vertically
    combined = np.vstack((frame, color_display))

    cv2.imshow("Color Detector", combined)

    # Exit on 'q'
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
