#!/usr/bin/env python3
"""
Dataset Preparation Pipeline for Fetal head Segmentation.
Automatically extracts, organizes, validates, and preprocesses the dataset.
"""

import os
import io
import sys
import zipfile
import shutil
from pathlib import Path

import numpy as np
from PIL import Image
from tqdm import tqdm

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATASET_DIR = PROJECT_ROOT / "dataset"
IMAGES_DIR = DATASET_DIR / "images"
MASKS_DIR = DATASET_DIR / "masks"

# Dataset ZIPs
TV_ZIP = PROJECT_ROOT / "Trans-ventricular.zip"
DIVERSE_ZIP = PROJECT_ROOT / "Diverse Fetal Head Images-orginal-image.zip"

# Preprocessing config
IMG_SIZE = 256
LABEL_MAP = {
    (0, 0, 0): 0,      # background
    (255, 0, 0): 1,     # Head (previously Brain)
    (0, 255, 0): 1,     # Head (previously CSP)
    (0, 0, 255): 1,     # Head (previously LV)
}


def extract_trans_ventricular():
    """Extract Trans-ventricular images and segmentation masks."""
    print("\n📦 Extracting Trans-ventricular dataset...")

    if not TV_ZIP.exists():
        print(f"  ⚠️  ZIP not found: {TV_ZIP}")
        return [], []

    images = []
    masks = []

    with zipfile.ZipFile(TV_ZIP, 'r') as outer_zip:
        # Extract images
        image_files = [
            f for f in outer_zip.namelist()
            if f.startswith("Trans-ventricular/Trans-ventricular/")
            and f.lower().endswith('.png')
        ]
        print(f"  Found {len(image_files)} ultrasound images")

        for img_path in tqdm(image_files, desc="  Extracting images"):
            basename = os.path.basename(img_path)
            data = outer_zip.read(img_path)
            try:
                img = Image.open(io.BytesIO(data))
                img.verify()
                images.append((basename, data))
            except Exception as e:
                print(f"  ⚠️  Skipping corrupt image: {basename} ({e})")

        # Extract masks from nested ZIP
        mask_zip_path = "Trans-ventricular/Trans-ventricular-segmentation-mask.zip"
        mask_data = outer_zip.read(mask_zip_path)

        with zipfile.ZipFile(io.BytesIO(mask_data), 'r') as mask_zip:
            mask_files = [
                f for f in mask_zip.namelist()
                if f.startswith("SegmentationClass/") and f.lower().endswith('.png')
            ]
            print(f"  Found {len(mask_files)} segmentation masks")

            for mask_path in tqdm(mask_files, desc="  Extracting masks"):
                basename = os.path.basename(mask_path)
                data = mask_zip.read(mask_path)
                try:
                    img = Image.open(io.BytesIO(data))
                    img.verify()
                    masks.append((basename, data))
                except Exception as e:
                    print(f"  ⚠️  Skipping corrupt mask: {basename} ({e})")

    return images, masks


def convert_mask_to_class_indices(mask_rgb: Image.Image) -> np.ndarray:
    """Convert RGB mask to single-channel class index mask."""
    mask_np = np.array(mask_rgb.convert('RGB'))
    class_mask = np.zeros(mask_np.shape[:2], dtype=np.uint8)

    for color, idx in LABEL_MAP.items():
        match = np.all(mask_np == np.array(color), axis=-1)
        class_mask[match] = idx

    return class_mask


def preprocess_and_save(images: list, masks: list):
    """Match images to masks, preprocess, and save."""
    print("\n🔧 Preprocessing dataset...")

    # Create output directories
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    MASKS_DIR.mkdir(parents=True, exist_ok=True)

    # Build lookup dicts
    img_dict = {name: data for name, data in images}
    mask_dict = {name: data for name, data in masks}

    # Find matching pairs
    matched = set(img_dict.keys()) & set(mask_dict.keys())
    print(f"  Matched image-mask pairs: {len(matched)}")

    unmatched_imgs = set(img_dict.keys()) - matched
    unmatched_masks = set(mask_dict.keys()) - matched
    if unmatched_imgs:
        print(f"  ⚠️  {len(unmatched_imgs)} images without masks (skipped)")
    if unmatched_masks:
        print(f"  ⚠️  {len(unmatched_masks)} masks without images (skipped)")

    saved = 0
    skipped = 0

    for name in tqdm(sorted(matched), desc="  Processing"):
        try:
            # Load image
            img = Image.open(io.BytesIO(img_dict[name]))
            img = img.convert('L')  # Grayscale
            img = img.resize((IMG_SIZE, IMG_SIZE), Image.BILINEAR)

            # Load and convert mask
            mask_rgb = Image.open(io.BytesIO(mask_dict[name]))
            mask_rgb = mask_rgb.resize((IMG_SIZE, IMG_SIZE), Image.NEAREST)
            class_mask = convert_mask_to_class_indices(mask_rgb)

            # Save
            img.save(IMAGES_DIR / name)
            Image.fromarray(class_mask).save(MASKS_DIR / name)
            saved += 1

        except Exception as e:
            print(f"  ⚠️  Error processing {name}: {e}")
            skipped += 1

    print(f"\n✅ Dataset prepared: {saved} pairs saved, {skipped} skipped")
    return saved


def create_split_file(total: int, val_ratio: float = 0.2):
    """Create train/val split file."""
    print("\n📋 Creating train/val split...")

    all_files = sorted([f.name for f in IMAGES_DIR.glob("*.png")])
    np.random.seed(42)
    indices = np.random.permutation(len(all_files))
    val_size = int(len(all_files) * val_ratio)

    val_files = [all_files[i] for i in indices[:val_size]]
    train_files = [all_files[i] for i in indices[val_size:]]

    split_path = DATASET_DIR / "split.npz"
    np.savez(split_path, train=train_files, val=val_files)

    print(f"  Train: {len(train_files)} | Val: {len(val_files)}")
    print(f"  Saved to: {split_path}")


def validate_dataset():
    """Validate dataset integrity."""
    print("\n🔍 Validating dataset...")

    images = sorted(IMAGES_DIR.glob("*.png"))
    masks = sorted(MASKS_DIR.glob("*.png"))

    img_names = {f.name for f in images}
    mask_names = {f.name for f in masks}

    assert img_names == mask_names, "Image-mask mismatch detected!"

    # Spot check a few samples
    for img_path in images[:5]:
        img = np.array(Image.open(img_path))
        mask = np.array(Image.open(MASKS_DIR / img_path.name))

        assert img.shape == (IMG_SIZE, IMG_SIZE), f"Bad image shape: {img.shape}"
        assert mask.shape == (IMG_SIZE, IMG_SIZE), f"Bad mask shape: {mask.shape}"
        assert mask.max() <= 1, f"Invalid mask values: max={mask.max()}"

    print(f"  ✅ {len(images)} image-mask pairs validated successfully")
    print(f"  Image shape: {IMG_SIZE}x{IMG_SIZE} grayscale")
    print(f"  Mask classes: 0=background, 1=Head")


def main():
    print("=" * 60)
    print("🧠 Fetal Brain Segmentation — Dataset Preparation")
    print("=" * 60)

    # Step 1: Extract
    images, masks = extract_trans_ventricular()

    if not images or not masks:
        print("❌ No data extracted. Check ZIP files.")
        sys.exit(1)

    # Step 2: Preprocess and save
    saved = preprocess_and_save(images, masks)

    if saved == 0:
        print("❌ No valid pairs processed.")
        sys.exit(1)

    # Step 3: Create split
    create_split_file(saved)

    # Step 4: Validate
    validate_dataset()

    print("\n" + "=" * 60)
    print("🎉 Dataset pipeline complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
