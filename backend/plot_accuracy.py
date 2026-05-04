#!/usr/bin/env python3
"""
Accuracy Plotter for Fetal Brain Segmentation.
Reads the training history and generates premium accuracy (Dice) and loss graphs.
"""

import json
import argparse
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

def plot_history(history_file, save_dir):
    history_file = Path(history_file)
    save_dir = Path(save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)

    if not history_file.exists():
        print(f"❌ Error: Could not find {history_file}")
        print("💡 Tip: Run training again with the updated train.py to generate history.json")
        return

    with open(history_file, 'r') as f:
        history = json.load(f)

    # In segmentation, Dice Score is used as the Accuracy metric
    epochs = range(1, len(history['train_dice']) + 1)
    
    # Use seaborn style for premium look
    sns.set_theme(style="whitegrid", context="talk")
    
    # 1. Plot Accuracy (Dice Score)
    plt.figure(figsize=(10, 6), dpi=200)
    plt.plot(epochs, history['train_dice'], label='Train Accuracy (Dice)', color='#3b82f6', linewidth=2.5, marker='o', markersize=4)
    plt.plot(epochs, history['val_dice'], label='Validation Accuracy (Dice)', color='#ef4444', linewidth=2.5, marker='o', markersize=4)
    plt.title('Model Accuracy (Dice Score) over Epochs', fontsize=18, fontweight='bold', pad=15)
    plt.xlabel('Epoch', fontsize=14)
    plt.ylabel('Accuracy (Dice)', fontsize=14)
    plt.legend(loc='lower right', frameon=True, shadow=True)
    plt.ylim(0.0, 1.05)
    plt.tight_layout()
    acc_path = save_dir / 'premium_accuracy_curve.png'
    plt.savefig(acc_path)
    plt.close()
    print(f"✅ Premium Accuracy graph saved to: {acc_path}")

    # 2. Plot Loss
    plt.figure(figsize=(10, 6), dpi=200)
    plt.plot(epochs, history['train_loss'], label='Train Loss', color='#3b82f6', linewidth=2.5, marker='o', markersize=4)
    plt.plot(epochs, history['val_loss'], label='Validation Loss', color='#ef4444', linewidth=2.5, marker='o', markersize=4)
    plt.title('Model Loss over Epochs', fontsize=18, fontweight='bold', pad=15)
    plt.xlabel('Epoch', fontsize=14)
    plt.ylabel('Loss', fontsize=14)
    plt.legend(loc='upper right', frameon=True, shadow=True)
    plt.tight_layout()
    loss_path = save_dir / 'premium_loss_curve.png'
    plt.savefig(loss_path)
    plt.close()
    print(f"✅ Premium Loss graph saved to: {loss_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Plot premium training graphs')
    parser.add_argument('--history', type=str, default='training_logs/history.json', help='Path to history.json')
    parser.add_argument('--save-dir', type=str, default='training_logs', help='Directory to save plots')
    args = parser.parse_args()
    
    backend_dir = Path(__file__).parent
    history_path = backend_dir / args.history
    save_path = backend_dir / args.save_dir
    
    plot_history(history_path, save_path)
