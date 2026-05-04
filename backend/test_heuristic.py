import io
import numpy as np
from PIL import Image

def is_valid_ultrasound(img_path):
    img = Image.open(img_path)
    rgb = np.array(img.convert('RGB'))
    r, g, b = rgb[:,:,0].astype(int), rgb[:,:,1].astype(int), rgb[:,:,2].astype(int)
    
    color_diff = np.mean(np.abs(r - g)) + np.mean(np.abs(r - b)) + np.mean(np.abs(g - b))
    
    gray = np.array(img.convert('L'))
    dark_ratio = np.sum(gray < 20) / gray.size
    
    print(f"File {img_path}: color={color_diff:.2f}, dark={dark_ratio:.2f}")

is_valid_ultrasound("training_logs/sample_predictions.png")

