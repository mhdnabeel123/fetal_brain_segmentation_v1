import os
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split

dataset_dir = Path("/Users/nabeel/Desktop/fetal_new/dataset")
img_dir = dataset_dir / "images"
split_file = dataset_dir / "split.npz"

files = [f for f in os.listdir(img_dir) if f.endswith(".png")]
train_files, val_files = train_test_split(files, test_size=0.2, random_state=42)

np.savez(split_file, train=train_files, val=val_files)
print(f"Generated new split.npz with {len(train_files)} train and {len(val_files)} val files.")
