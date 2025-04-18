import cv2
import pandas as pd
import os
import tkinter as tk
from tkinter import filedialog

# Create a root window but hide it
root = tk.Tk()
root.withdraw()

# Open file dialog to select an image
image_path = filedialog.askopenfilename(title="Select Image",
                                       filetypes=(("Image files", "*.jpg;*.jpeg;*.png"), 
                                                 ("All files", "*.*")))

# If no image is selected, exit
if not image_path:
    print("No image selected. Exiting.")
    exit()

# Load the original image
original_image = cv2.imread(image_path)

# Function to resize image to fit screen
def resize_image_to_fit_screen(image, max_width=1200, max_height=800):
    # Get original dimensions
    height, width = image.shape[:2]
    
    # Calculate the ratio of the width and height
    ratio = min(max_width / width, max_height / height)
    
    # Check if we need to resize (only resize if the image is too large)
    if ratio < 1:
        new_dimensions = (int(width * ratio), int(height * ratio))
        resized_image = cv2.resize(image, new_dimensions, interpolation=cv2.INTER_AREA)
        return resized_image
    return image.copy()  # Return a copy to avoid modifying the original

# Resize the image for display
display_image = resize_image_to_fit_screen(original_image)

# Path to the color CSV file
csv_path = 'c.csv'  

# Initialize variables
clicked = False
r = g = b = x_pos = y_pos = 0

# Read the CSV file with color data
index = ["color", "color_name", "hex", "R", "G", "B"]
csv = pd.read_csv(csv_path, names=index, header=None)

# Function to get color name from RGB values
def get_color_name(R, G, B):
    minimum = 10000
    cname = ""
    for i in range(len(csv)):
        d = abs(R - int(csv.loc[i, "R"])) + abs(G - int(csv.loc[i, "G"])) + abs(B - int(csv.loc[i, "B"]))
        if d < minimum:
            minimum = d
            cname = csv.loc[i, "color_name"]
    return cname

# Mouse callback function
def draw_function(event, x, y, flags, param):
    global b, g, r, x_pos, y_pos, clicked, original_image, display_image
    if event == cv2.EVENT_LBUTTONDBLCLK:
        clicked = True
        x_pos = x
        y_pos = y
        
        # Get the scaling factors
        orig_height, orig_width = original_image.shape[:2]
        disp_height, disp_width = display_image.shape[:2]
        
        # Scale coordinates to match original image
        orig_x = int(x * (orig_width / disp_width))
        orig_y = int(y * (orig_height / disp_height))
        
        # Make sure coordinates are within bounds
        orig_x = max(0, min(orig_x, orig_width - 1))
        orig_y = max(0, min(orig_y, orig_height - 1))
        
        # Get color from original image at scaled coordinates
        b, g, r = original_image[orig_y, orig_x]
        b = int(b)
        g = int(g)
        r = int(r)

# Create a window and set mouse callback
cv2.namedWindow('Color Detection')
cv2.setMouseCallback('Color Detection', draw_function)

# Create a copy of the display image that we can modify
result_image = display_image.copy()

# Main loop
while True:
    # Always show the current result image
    cv2.imshow("Color Detection", result_image)
    
    if clicked:
        # Create a fresh copy of the display image
        result_image = display_image.copy()
        
        # Draw the color rectangle and text
        cv2.rectangle(result_image, (20, 20), (750, 60), (b, g, r), -1)
        text = f"{get_color_name(r, g, b)} R={r} G={g} B={b}"
        
        # Choose text color based on background brightness
        if r + g + b >= 600:
            text_color = (0, 0, 0)  # Black text for light backgrounds
        else:
            text_color = (255, 255, 255)  # White text for dark backgrounds
            
        cv2.putText(result_image, text, (50, 50), 2, 0.8, text_color, 2, cv2.LINE_AA)
        
        clicked = False
    
    # Break the loop when ESC is pressed
    if cv2.waitKey(20) & 0xFF == 27:
        break

cv2.destroyAllWindows()