#!/usr/bin/env python3
"""
Training Script for Fetal Head Segmentation U-Net++.
Supports MPS (Apple Silicon), CUDA, and CPU training with early stopping.
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime

import numpy as np
import torch
import torch.optim as optim
from tqdm import tqdm
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Add parent dir
sys.path.insert(0, str(Path(__file__).parent))

from model import UNetPlusPlus, count_parameters
from losses import HybridLoss, dice_coefficient
from dataset import get_dataloaders


def get_device():
    """Auto-detect best available device."""
    if torch.cuda.is_available():
        device = torch.device('cuda')
        print(f"🖥️  Using CUDA: {torch.cuda.get_device_name(0)}")
    elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        device = torch.device('mps')
        print("🍎 Using MPS (Apple Silicon GPU)")
    else:
        device = torch.device('cpu')
        print("💻 Using CPU")
    return device


def train_one_epoch(model, loader, criterion, optimizer, device):
    """Train for one epoch."""
    model.train()
    total_loss = 0.0
    total_dice = 0.0
    num_batches = 0

    for images, masks in loader:
        images = images.to(device)
        masks = masks.to(device)

        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, masks)
        loss.backward()
        optimizer.step()

        # Metrics
        total_loss += loss.item()
        with torch.no_grad():
            dice = dice_coefficient(outputs, masks)
            total_dice += dice['Mean']
        num_batches += 1

    return total_loss / num_batches, total_dice / num_batches


@torch.no_grad()
def validate(model, loader, criterion, device):
    """Validate model."""
    model.eval()
    total_loss = 0.0
    total_dice = {'Background': 0, 'Head': 0, 'Mean': 0}
    num_batches = 0

    for images, masks in loader:
        images = images.to(device)
        masks = masks.to(device)

        outputs = model(images)
        loss = criterion(outputs, masks)

        total_loss += loss.item()
        dice = dice_coefficient(outputs, masks)
        for k in total_dice:
            total_dice[k] += dice[k]
        num_batches += 1

    avg_loss = total_loss / num_batches
    avg_dice = {k: v / num_batches for k, v in total_dice.items()}

    return avg_loss, avg_dice


def save_training_plots(history, save_dir):
    """Generate and save training progress plots."""
    save_dir = Path(save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)

    epochs_range = range(1, len(history['train_loss']) + 1)

    # --- Loss plot ---
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    ax.plot(epochs_range, history['train_loss'], 'b-', linewidth=2, label='Train Loss')
    ax.plot(epochs_range, history['val_loss'], 'r-', linewidth=2, label='Val Loss')
    ax.set_xlabel('Epoch', fontsize=12)
    ax.set_ylabel('Loss', fontsize=12)
    ax.set_title('Training & Validation Loss', fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(save_dir / 'loss_curve.png', dpi=150)
    plt.close(fig)

    # --- Dice score plot ---
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    ax.plot(epochs_range, history['train_dice'], 'b-', linewidth=2, label='Train Dice')
    ax.plot(epochs_range, history['val_dice'], 'r-', linewidth=2, label='Val Dice')
    ax.set_xlabel('Epoch', fontsize=12)
    ax.set_ylabel('Dice Score', fontsize=12)
    ax.set_title('Training & Validation Dice Score', fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 1)
    fig.tight_layout()
    fig.savefig(save_dir / 'dice_curve.png', dpi=150)
    plt.close(fig)

    # --- Per-class Dice (just Head) ---
    if 'val_dice_classes' in history and history['val_dice_classes']:
        fig, ax = plt.subplots(1, 1, figsize=(10, 6))
        for cls_name in ['Head']:
            values = [d[cls_name] for d in history['val_dice_classes']]
            ax.plot(epochs_range, values, linewidth=2, label=cls_name, color='#ef4444')
        ax.set_xlabel('Epoch', fontsize=12)
        ax.set_ylabel('Dice Score', fontsize=12)
        ax.set_title('Validation Dice Score (Head)', fontsize=14, fontweight='bold')
        ax.legend(fontsize=11)
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, 1)
        fig.tight_layout()
        fig.savefig(save_dir / 'dice_per_class.png', dpi=150)
        plt.close(fig)

    print(f"  📈 Training plots saved to {save_dir}")


def main():
    parser = argparse.ArgumentParser(description='Train U-Net++ for Fetal Head Segmentation')
    parser.add_argument('--epochs', type=int, default=50, help='Number of training epochs')
    parser.add_argument('--batch-size', type=int, default=8, help='Batch size')
    parser.add_argument('--lr', type=float, default=1e-3, help='Learning rate')
    parser.add_argument('--patience', type=int, default=10, help='Early stopping patience')
    parser.add_argument('--dataset-dir', type=str, default=None, help='Dataset directory')
    parser.add_argument('--save-dir', type=str, default=None, help='Model save directory')
    args = parser.parse_args()

    # Paths
    backend_dir = Path(__file__).parent
    project_root = backend_dir.parent
    dataset_dir = Path(args.dataset_dir) if args.dataset_dir else project_root / "dataset"
    save_dir = Path(args.save_dir) if args.save_dir else backend_dir / "saved_models"
    log_dir = backend_dir / "training_logs"

    save_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("🧠 U-Net++ Training — Fetal Head Segmentation")
    print("=" * 60)

    # Device
    device = get_device()

    # Data
    train_loader, val_loader = get_dataloaders(
        dataset_dir,
        batch_size=args.batch_size,
        num_workers=0,  # MPS doesn't support multi-worker well
    )

    # Model
    model = UNetPlusPlus(in_channels=1, num_classes=2, deep_supervision=True)
    model = model.to(device)
    print(f"📐 Model parameters: {count_parameters(model):,}")

    # Loss & Optimizer
    criterion = HybridLoss(num_classes=2, dice_weight=0.5, ce_weight=0.5)
    optimizer = optim.Adam(model.parameters(), lr=args.lr, weight_decay=1e-5)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='min', factor=0.5, patience=5
    )

    # Training history
    history = {
        'train_loss': [], 'val_loss': [],
        'train_dice': [], 'val_dice': [],
        'val_dice_classes': [],
        'lr': [],
    }

    best_val_dice = 0.0
    patience_counter = 0
    start_time = time.time()

    print(f"\n🚀 Starting training: {args.epochs} epochs, batch_size={args.batch_size}, lr={args.lr}")
    print(f"   Early stopping patience: {args.patience}")
    print("-" * 60)

    for epoch in range(1, args.epochs + 1):
        epoch_start = time.time()

        # Train
        train_loss, train_dice = train_one_epoch(model, train_loader, criterion, optimizer, device)

        # Validate
        val_loss, val_dice = validate(model, val_loader, criterion, device)

        # Learning rate scheduling
        scheduler.step(val_loss)
        current_lr = optimizer.param_groups[0]['lr']

        # Record history
        history['train_loss'].append(train_loss)
        history['val_loss'].append(val_loss)
        history['train_dice'].append(train_dice)
        history['val_dice'].append(val_dice['Mean'])
        history['val_dice_classes'].append(val_dice)
        history['lr'].append(current_lr)

        epoch_time = time.time() - epoch_start

        # Print progress
        print(
            f"  Epoch {epoch:3d}/{args.epochs} | "
            f"Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | "
            f"Val Dice: {val_dice['Mean']:.4f} | "
            f"Head: {val_dice['Head']:.3f} | "
            f"LR: {current_lr:.2e} | {epoch_time:.1f}s"
        )

        # Model checkpointing
        if val_dice['Mean'] > best_val_dice:
            best_val_dice = val_dice['Mean']
            patience_counter = 0

            checkpoint = {
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'val_dice': val_dice,
                'val_loss': val_loss,
                'args': vars(args),
            }
            torch.save(checkpoint, save_dir / 'model.pth')
            print(f"  💾 Best model saved (Dice: {best_val_dice:.4f})")
        else:
            patience_counter += 1

        # Early stopping
        if patience_counter >= args.patience:
            print(f"\n⏹️  Early stopping at epoch {epoch} (patience={args.patience})")
            break

    total_time = time.time() - start_time
    print("-" * 60)
    print(f"✅ Training complete in {total_time / 60:.1f} minutes")
    print(f"   Best Val Dice: {best_val_dice:.4f}")

    # Save plots
    save_training_plots(history, log_dir)

    # Save training metrics
    metrics = {
        'best_val_dice': best_val_dice,
        'total_epochs': len(history['train_loss']),
        'total_time_minutes': round(total_time / 60, 2),
        'final_train_loss': history['train_loss'][-1],
        'final_val_loss': history['val_loss'][-1],
        'best_val_dice_classes': history['val_dice_classes'][-1] if history['val_dice_classes'] else {},
        'hyperparameters': vars(args),
        'timestamp': datetime.now().isoformat(),
    }

    with open(log_dir / 'training_metrics.json', 'w') as f:
        json.dump(metrics, f, indent=2)

    with open(log_dir / 'history.json', 'w') as f:
        json.dump(history, f, indent=2)

    print(f"  📄 Metrics saved to {log_dir / 'training_metrics.json'}")
    print(f"  📄 History saved to {log_dir / 'history.json'}")
    print(f"  📊 Plots saved to {log_dir}")


if __name__ == "__main__":
    main()
