import cv2
import numpy as np

def extract_features(image_path):
    """
    Reads an image and returns 4 numbers:
    [Mean Hue, Mean Saturation, Mean Value, Texture Score]
    """
    try:
        # 1. Read the image
        img = cv2.imread(image_path)
        if img is None:
            return None
        
        # 2. Resize to speed up processing (300x300 is enough for water)
        img = cv2.resize(img, (300, 300))

        # 3. Color Analysis (Convert to HSV)
        # HSV = Hue (Color), Saturation (Intensity), Value (Brightness)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        
        mean_hue = np.mean(h)
        mean_sat = np.mean(s)
        mean_val = np.mean(v)

        # 4. Texture Analysis (Turbidity Detection)
        # We turn it to Gray and measure "Laplacian Variance"
        # High Variance = Sharp/Rough (Dirty particles)
        # Low Variance = Smooth/Blurry (Clear liquid)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        texture_score = cv2.Laplacian(gray, cv2.CV_64F).var()

        return [mean_hue, mean_sat, mean_val, texture_score]

    except Exception as e:
        print(f"Error reading {image_path}: {e}")
        return None