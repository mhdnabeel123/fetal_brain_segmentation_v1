"""
Hybrid Loss Functions for Multi-Class Segmentation.
Combines Dice Loss and Cross Entropy Loss for optimal training.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class DiceLoss(nn.Module):
    """
    Multi-class Dice Loss.
    Computes Dice coefficient per class and averages.
    """

    def __init__(self, num_classes=2, smooth=1e-6):
        super().__init__()
        self.num_classes = num_classes
        self.smooth = smooth

    def forward(self, pred, target):
        """
        Args:
            pred: (B, C, H, W) logits
            target: (B, H, W) class indices
        """
        pred_soft = F.softmax(pred, dim=1)
        target_one_hot = F.one_hot(target.long(), self.num_classes)  # (B, H, W, C)
        target_one_hot = target_one_hot.permute(0, 3, 1, 2).float()  # (B, C, H, W)

        dice_sum = 0.0
        for c in range(self.num_classes):
            pred_c = pred_soft[:, c]
            target_c = target_one_hot[:, c]

            intersection = (pred_c * target_c).sum(dim=(1, 2))
            union = pred_c.sum(dim=(1, 2)) + target_c.sum(dim=(1, 2))

            dice = (2.0 * intersection + self.smooth) / (union + self.smooth)
            dice_sum += dice.mean()

        return 1.0 - dice_sum / self.num_classes


class HybridLoss(nn.Module):
    """
    Hybrid Loss = α * DiceLoss + β * CrossEntropyLoss

    Combines the region-based Dice loss (good for class imbalance)
    with the pixel-wise CE loss (good for sharp boundaries).
    """

    def __init__(self, num_classes=2, dice_weight=0.5, ce_weight=0.5):
        super().__init__()
        self.dice_loss = DiceLoss(num_classes)
        self.ce_loss = nn.CrossEntropyLoss()
        self.dice_weight = dice_weight
        self.ce_weight = ce_weight

    def forward(self, pred, target):
        """
        Args:
            pred: (B, C, H, W) logits
            target: (B, H, W) class indices
        """
        d_loss = self.dice_loss(pred, target)
        c_loss = self.ce_loss(pred, target.long())
        return self.dice_weight * d_loss + self.ce_weight * c_loss


def dice_coefficient(pred, target, num_classes=2, smooth=1e-6):
    """
    Calculate per-class Dice coefficient (for evaluation).

    Args:
        pred: (B, C, H, W) logits or probabilities
        target: (B, H, W) class indices

    Returns:
        dict of class_name: dice_score
    """
    class_names = ['Background', 'Head']
    pred_classes = pred.argmax(dim=1)  # (B, H, W)
    scores = {}

    for c in range(num_classes):
        pred_c = (pred_classes == c).float()
        target_c = (target == c).float()

        intersection = (pred_c * target_c).sum()
        union = pred_c.sum() + target_c.sum()

        dice = (2.0 * intersection + smooth) / (union + smooth)
        scores[class_names[c]] = dice.item()

    scores['Mean'] = scores.get('Head', 0.0)
    return scores
