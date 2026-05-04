"""
PyTorch Dataset for Fetal Brain Segmentation.
Implements data loading with augmentation via Albumentations.
"""

import numpy as np
from pathlib import Path
from PIL import Image

import torch
from torch.utils.data import Dataset
import albumentations as A


def _use_pin_memory():
    """Check if pin_memory is supported (not on MPS)."""
    if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        return False
    return torch.cuda.is_available()


class FetalBrainDataset(Dataset):
    """
    Dataset for fetal brain ultrasound segmentation.

    Loads preprocessed 256x256 grayscale images and class-index masks.
    Applies augmentation during training.
    """

    def __init__(self, image_dir, mask_dir, file_list=None, augment=False):
        self.image_dir = Path(image_dir)
        self.mask_dir = Path(mask_dir)

        if file_list is not None:
            self.filenames = sorted(file_list)
        else:
            self.filenames = sorted([f.name for f in self.image_dir.glob("*.png")])

        self.augment = augment
        self.transform = self._build_transforms() if augment else None

    def _build_transforms(self):
        """Advanced augmentation pipeline."""
        return A.Compose([
            A.HorizontalFlip(p=0.5),
            A.VerticalFlip(p=0.3),
            A.Rotate(limit=15, p=0.5, border_mode=0),
            A.RandomBrightnessContrast(
                brightness_limit=0.2,
                contrast_limit=0.2,
                p=0.5
            ),
            A.GaussNoise(std_range=(0.01, 0.05), p=0.3),
            A.ElasticTransform(alpha=50, sigma=5, p=0.2),
        ])

    def __len__(self):
        return len(self.filenames)

    def __getitem__(self, idx):
        fname = self.filenames[idx]

        # Load image (grayscale, already 256x256)
        img = np.array(Image.open(self.image_dir / fname)).astype(np.float32)
        if img.ndim == 3:
            img = img[:, :, 0]

        # Normalize to [0, 1]
        img = img / 255.0

        # Load mask (class indices)
        mask = np.array(Image.open(self.mask_dir / fname)).astype(np.int64)

        # Apply augmentation
        if self.transform is not None:
            augmented = self.transform(image=img, mask=mask)
            img = augmented['image']
            mask = augmented['mask']

        # Convert to tensors
        img_tensor = torch.from_numpy(img).unsqueeze(0).float()  # (1, H, W)
        mask_tensor = torch.from_numpy(mask).long()  # (H, W)

        return img_tensor, mask_tensor


def get_dataloaders(dataset_dir, batch_size=8, num_workers=0):
    """
    Create train and validation dataloaders from the prepared dataset.

    Args:
        dataset_dir: Path to dataset directory containing images/, masks/, split.npz
        batch_size: Batch size for training
        num_workers: Number of data loading workers

    Returns:
        train_loader, val_loader
    """
    from torch.utils.data import DataLoader

    dataset_dir = Path(dataset_dir)
    image_dir = dataset_dir / "images"
    mask_dir = dataset_dir / "masks"
    split_file = dataset_dir / "split.npz"

    # Load split
    split = np.load(split_file, allow_pickle=True)
    train_files = list(split['train'])
    val_files = list(split['val'])

    # Create datasets
    train_dataset = FetalBrainDataset(image_dir, mask_dir, train_files, augment=True)
    val_dataset = FetalBrainDataset(image_dir, mask_dir, val_files, augment=False)

    # Create dataloaders
    pin_mem = _use_pin_memory()
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=pin_mem,
        drop_last=True,
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=pin_mem,
    )

    print(f"📊 Dataset loaded:")
    print(f"   Train: {len(train_dataset)} samples ({len(train_loader)} batches)")
    print(f"   Val:   {len(val_dataset)} samples ({len(val_loader)} batches)")

    return train_loader, val_loader
