#!/usr/bin/env python3
"""
Evaluation Script for Fetal Brain Segmentation Model.
Computes Dice, IoU, Precision, Recall per class and generates reports.
"""

import sys
import json
from pathlib import Path

import numpy as np
import torch
from tqdm import tqdm
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).parent))

from sklearn.metrics import confusion_matrix
import itertools

from model import UNetPlusPlus
from dataset import get_dataloaders


def compute_metrics(pred, target, num_classes=2, smooth=1e-6):
    """
    Compute per-class Dice, IoU, Precision, Recall.

    Args:
        pred: (B, C, H, W) logits
        target: (B, H, W) class indices
    """
    pred_classes = pred.argmax(dim=1)  # (B, H, W)
    class_names = ['Background', 'Head']
    metrics = {}

    for c in range(num_classes):
        pred_c = (pred_classes == c).float()
        target_c = (target == c).float()

        tp = (pred_c * target_c).sum().item()
        fp = (pred_c * (1 - target_c)).sum().item()
        fn = ((1 - pred_c) * target_c).sum().item()

        dice = (2 * tp + smooth) / (2 * tp + fp + fn + smooth)
        precision = (tp + smooth) / (tp + fp + smooth)
        recall = (tp + smooth) / (tp + fn + smooth)
        f1 = (2 * precision * recall) / (precision + recall + smooth)
        accuracy = (tp + (target.nelement() - (tp + fp + fn))) / target.nelement()
        iou = (tp + smooth) / (tp + fp + fn + smooth)

        metrics[class_names[c]] = {
            'dice': round(dice, 4),
            'iou': round(iou, 4),
            'precision': round(precision, 4),
            'recall': round(recall, 4),
            'f1': round(f1, 4),
            'accuracy': round(accuracy, 4),
        }

    # Mean (excluding background)
    fg_classes = ['Head']
    metrics['Mean'] = {
        'dice': round(np.mean([metrics[c]['dice'] for c in fg_classes]), 4),
        'iou': round(np.mean([metrics[c]['iou'] for c in fg_classes]), 4),
        'precision': round(np.mean([metrics[c]['precision'] for c in fg_classes]), 4),
        'recall': round(np.mean([metrics[c]['recall'] for c in fg_classes]), 4),
        'f1': round(np.mean([metrics[c]['f1'] for c in fg_classes]), 4),
        'accuracy': round(np.mean([metrics[c]['accuracy'] for c in fg_classes]), 4),
    }

    return metrics


def plot_evaluation_results(metrics, save_dir):
    """Generate evaluation bar charts."""
    save_dir = Path(save_dir)

    classes = ['Head', 'Mean']
    metric_names = ['dice', 'f1', 'accuracy', 'iou']
    colors = ['#ef4444', '#a78bfa', '#10b981', '#3b82f6']

    fig, axes = plt.subplots(1, 4, figsize=(20, 5))

    for i, metric in enumerate(metric_names):
        values = [metrics[c][metric] for c in classes]
        bars = axes[i].bar(classes, values, color=colors[i], alpha=0.85, edgecolor='white')
        axes[i].set_title(metric.upper(), fontsize=14, fontweight='bold')
        axes[i].set_ylim(0, 1)
        axes[i].grid(axis='y', alpha=0.3)

        for bar, val in zip(bars, values):
            axes[i].text(
                bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
                f'{val:.3f}', ha='center', fontsize=10, fontweight='bold'
            )

    fig.suptitle('Model Evaluation Results', fontsize=16, fontweight='bold', y=1.02)
    fig.tight_layout()
    fig.savefig(save_dir / 'evaluation_results.png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  📊 Evaluation plot saved to {save_dir / 'evaluation_results.png'}")


def plot_confusion_matrix(cm, classes, save_dir):
    """Plot and save the confusion matrix."""
    save_dir = Path(save_dir)
    
    # Normalize CM
    cm_norm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
    
    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(cm_norm, interpolation='nearest', cmap=plt.cm.Blues)
    ax.set_title('Normalized Confusion Matrix', fontsize=16, fontweight='bold')
    fig.colorbar(im)
    
    tick_marks = np.arange(len(classes))
    ax.set_xticks(tick_marks)
    ax.set_xticklabels(classes, rotation=45, ha='right')
    ax.set_yticks(tick_marks)
    ax.set_yticklabels(classes)
    
    # Text annotations
    fmt = '.2f'
    thresh = cm_norm.max() / 2.
    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        ax.text(j, i, format(cm_norm[i, j], fmt),
                ha="center", va="center",
                color="white" if cm_norm[i, j] > thresh else "black",
                fontweight='bold')
    
    ax.set_ylabel('True Label', fontsize=12, fontweight='bold')
    ax.set_xlabel('Predicted Label', fontsize=12, fontweight='bold')
    plt.tight_layout()
    
    fig.savefig(save_dir / 'confusion_matrix.png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  📊 Confusion matrix saved to {save_dir / 'confusion_matrix.png'}")


def visualize_predictions(model, val_loader, device, save_dir, n_samples=6):
    """Generate sample prediction visualizations."""
    save_dir = Path(save_dir)
    model.eval()

    # Color map for classes
    color_map = np.array([
        [0, 0, 0],       # Background - black
        [255, 50, 50],    # Head - red
    ], dtype=np.uint8)

    images, masks, preds = [], [], []

    with torch.no_grad():
        for batch_imgs, batch_masks in val_loader:
            batch_imgs = batch_imgs.to(device)
            outputs = model(batch_imgs)
            pred_classes = outputs.argmax(dim=1).cpu().numpy()

            for i in range(batch_imgs.shape[0]):
                if len(images) >= n_samples:
                    break
                images.append(batch_imgs[i, 0].cpu().numpy())
                masks.append(batch_masks[i].numpy())
                preds.append(pred_classes[i])

            if len(images) >= n_samples:
                break

    fig, axes = plt.subplots(n_samples, 3, figsize=(12, 4 * n_samples))
    if n_samples == 1:
        axes = axes[np.newaxis, :]

    for i in range(n_samples):
        # Original
        axes[i, 0].imshow(images[i], cmap='gray')
        axes[i, 0].set_title('Ultrasound Image', fontsize=11)
        axes[i, 0].axis('off')

        # Ground truth
        gt_rgb = color_map[masks[i]]
        axes[i, 1].imshow(gt_rgb)
        axes[i, 1].set_title('Ground Truth', fontsize=11)
        axes[i, 1].axis('off')

        # Prediction
        pred_rgb = color_map[preds[i]]
        axes[i, 2].imshow(pred_rgb)
        axes[i, 2].set_title('Prediction', fontsize=11)
        axes[i, 2].axis('off')

    fig.suptitle('Sample Predictions', fontsize=16, fontweight='bold')
    fig.tight_layout()
    fig.savefig(save_dir / 'sample_predictions.png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  🖼️  Sample grid saved to {save_dir / 'sample_predictions.png'}")


def save_dataset_samples(model, loader, device, save_dir, desc="Samples"):
    """Save every sample in the loader as an individual side-by-side image."""
    save_dir = Path(save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)
    model.eval()

    # Color map for head class
    color_map = np.array([
        [0, 0, 0],       # Background - black
        [255, 60, 60],    # Head - red
    ], dtype=np.uint8)

    print(f"  💾 Saving {desc} to {save_dir}...")
    sample_idx = 0
    with torch.no_grad():
        for batch_imgs, batch_masks in tqdm(loader, desc=f"  Saving {desc}"):
            batch_imgs = batch_imgs.to(device)
            outputs = model(batch_imgs)
            pred_classes = outputs.argmax(dim=1).cpu().numpy()

            for i in range(batch_imgs.shape[0]):
                img = batch_imgs[i, 0].cpu().numpy()
                gt = batch_masks[i].numpy()
                pred = pred_classes[i]

                # Create 3-panel figure for this specific sample
                fig, axes = plt.subplots(1, 3, figsize=(12, 4))
                
                axes[0].imshow(img, cmap='gray')
                axes[0].set_title('Ultrasound', fontsize=10)
                axes[0].axis('off')

                axes[1].imshow(color_map[gt])
                axes[1].set_title('Ground Truth', fontsize=10)
                axes[1].axis('off')

                axes[2].imshow(color_map[pred])
                axes[2].set_title('AI Prediction', fontsize=10)
                axes[2].axis('off')

                plt.tight_layout()
                plt.savefig(save_dir / f"sample_{sample_idx+1:03d}.png", dpi=100, bbox_inches='tight')
                plt.close(fig)
                sample_idx += 1
    
    print(f"  ✅ Saved {sample_idx} {desc.lower()} to {save_dir}")


def main():
    backend_dir = Path(__file__).parent
    project_root = backend_dir.parent
    dataset_dir = project_root / "dataset"
    model_path = backend_dir / "saved_models" / "model.pth"
    log_dir = backend_dir / "training_logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("📊 Model Evaluation — Fetal Head Segmentation")
    print("=" * 60)

    # Device
    if torch.cuda.is_available():
        device = torch.device('cuda')
    elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        device = torch.device('mps')
    else:
        device = torch.device('cpu')
    print(f"  Device: {device}")

    # Load model
    if not model_path.exists():
        print(f"❌ Model not found at {model_path}")
        sys.exit(1)

    model = UNetPlusPlus(in_channels=1, num_classes=2, deep_supervision=True)
    checkpoint = torch.load(model_path, map_location=device, weights_only=False)
    model.load_state_dict(checkpoint['model_state_dict'])
    model = model.to(device)
    model.eval()
    print(f"  ✅ Loaded model from epoch {checkpoint['epoch']}")

    # Data
    _, val_loader = get_dataloaders(dataset_dir, batch_size=8, num_workers=0)

    # Compute metrics and confusion matrix
    print("\n🔍 Computing evaluation metrics...")
    all_metrics = []
    total_cm = np.zeros((2, 2))
    
    with torch.no_grad():
        for images, masks in tqdm(val_loader, desc="  Evaluating"):
            images = images.to(device)
            masks = masks.to(device)
            outputs = model(images)
            
            # Record metrics
            batch_metrics = compute_metrics(outputs, masks)
            all_metrics.append(batch_metrics)
            
            # Record confusion matrix
            preds = outputs.argmax(dim=1).cpu().numpy().flatten()
            targets = masks.cpu().numpy().flatten()
            total_cm += confusion_matrix(targets, preds, labels=[0, 1])

    # Average metrics
    final_metrics = {}
    for key in all_metrics[0]:
        final_metrics[key] = {}
        for metric in all_metrics[0][key]:
            values = [m[key][metric] for m in all_metrics]
            final_metrics[key][metric] = round(np.mean(values), 4)

    # Print results
    print("\n" + "=" * 60)
    print("📋 Evaluation Results")
    print("=" * 60)
    print(f"{'Class':<12} {'Dice':>8} {'F1':>8} {'Acc':>8} {'IoU':>8}")
    print("-" * 50)
    for cls in ['Background', 'Head', 'Mean']:
        m = final_metrics[cls]
        print(f"{cls:<12} {m['dice']:>8.4f} {m['f1']:>8.4f} {m['accuracy']:>8.4f} {m['iou']:>8.4f}")

    # Save metrics
    with open(log_dir / 'evaluation_metrics.json', 'w') as f:
        json.dump(final_metrics, f, indent=2)
    print(f"\n  📄 Metrics saved to {log_dir / 'evaluation_metrics.json'}")

    # Generate plots
    plot_evaluation_results(final_metrics, log_dir)
    plot_confusion_matrix(total_cm, ['Background', 'Head'], log_dir)
    visualize_predictions(model, val_loader, device, log_dir, n_samples=6)

    # Save all samples for reference
    output_root = project_root / "training_output"
    train_loader_full, _ = get_dataloaders(dataset_dir, batch_size=1, num_workers=0)
    
    save_dataset_samples(model, train_loader_full, device, output_root / "trained_images", desc="Training Samples")
    save_dataset_samples(model, val_loader, device, output_root / "test_images", desc="Test Samples")

    print("\n✅ Evaluation and image export complete!")


if __name__ == "__main__":
    main()
