import os
import cv2
import numpy as np
from pathlib import Path
from tqdm import tqdm

def main():
    print("🚀 Starting data validation and ingestion...")
    ROOT_DIR = Path("/Users/nabeel/Desktop/fetal_new")
    IMAGES_DIR = ROOT_DIR / "dataset/images"
    MASKS_DIR = ROOT_DIR / "dataset/masks"
    NEW_IMGS_DIR = ROOT_DIR / "Diverse Fetal Head Images" / "Orginal_train_images_to_959_661"
    NEW_MASKS_DIR = ROOT_DIR / "Diverse Fetal Head Images" / "Test-Dataset-Segmentation" / "SegmentationClass"

    import glob
    img_files = glob.glob(str(NEW_IMGS_DIR / "*.png"))
    print(f"📦 Found {len(img_files)} new images to process.")

    # Colors defined in labelmap.txt (RGB)
    TARGET_COLORS = [
        (255, 0, 0),    # Brain
        (0, 0, 255),    # LV
        (255, 255, 0),  # CSP
    ]

    added_count = 0
    for img_path in tqdm(img_files, desc="Processing and Resizing"):
        basename = os.path.basename(img_path)
        mask_path = NEW_MASKS_DIR / basename
        
        if not mask_path.exists():
            continue
            
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        mask = cv2.imread(str(mask_path), cv2.IMREAD_COLOR) # OpenCV reads BGR
        
        if mask is None or img is None:
            continue
            
        # Convert BGR (OpenCV) to RGB (for checking logic)
        mask_rgb = cv2.cvtColor(mask, cv2.COLOR_BGR2RGB)
        
        # Initialize an empty 1D mask (Background = 0)
        processed_mask = np.zeros(mask_rgb.shape[:2], dtype=np.uint8)
        
        # Map target classes to 1 (Head circumfrence)
        for color in TARGET_COLORS:
            matches = np.all(mask_rgb == color, axis=-1)
            processed_mask[matches] = 1
            
        # Resize all new images to 256x256 medical standard
        img_resized = cv2.resize(img, (256, 256), interpolation=cv2.INTER_AREA)
        mask_resized = cv2.resize(processed_mask, (256, 256), interpolation=cv2.INTER_NEAREST)
        
        # Save to main dataset folder with "Diverse_" prefix to prevent overwriting
        cv2.imwrite(str(IMAGES_DIR / f"Diverse_{basename}"), img_resized)
        cv2.imwrite(str(MASKS_DIR / f"Diverse_{basename}"), mask_resized)
        added_count += 1
        
    print(f"\n✅ SUCCESSFULLY ADDED {added_count} new images!")
    print(f"📊 Total Raw Images in project: {len(os.listdir(IMAGES_DIR))}")
    print(f"📊 Total Masks in project: {len(os.listdir(MASKS_DIR))}")

if __name__ == '__main__':
    main()
