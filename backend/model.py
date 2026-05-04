"""
U-Net++ (Nested U-Net) Architecture for Fetal Head Segmentation.
Implements dense skip connections for high-precision multi-class segmentation.
"""

import torch
import torch.nn as nn


class ConvBlock(nn.Module):
    """Double convolution block with BatchNorm and ReLU."""

    def __init__(self, in_ch, out_ch):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, 3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, 3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
        )

    def forward(self, x):
        return self.conv(x)


class UNetPlusPlus(nn.Module):
    """
    U-Net++ (Nested U-Net) with deep supervision.

    Architecture:
        - 4-level encoder with max-pooling downsampling
        - Dense skip pathways (nested connections)
        - Deep supervision for multi-scale output
        - 4-class output: Background, Brain, CSP, LV
    """

    def __init__(self, in_channels=1, num_classes=2, features=None, deep_supervision=True):
        super().__init__()

        if features is None:
            features = [32, 64, 128, 256, 512]

        self.deep_supervision = deep_supervision
        self.pool = nn.MaxPool2d(2, 2)
        self.up = nn.Upsample(scale_factor=2, mode='bilinear', align_corners=True)

        # Encoder path (backbone)
        self.conv0_0 = ConvBlock(in_channels, features[0])
        self.conv1_0 = ConvBlock(features[0], features[1])
        self.conv2_0 = ConvBlock(features[1], features[2])
        self.conv3_0 = ConvBlock(features[2], features[3])
        self.conv4_0 = ConvBlock(features[3], features[4])

        # Dense skip connections - level 1
        self.conv0_1 = ConvBlock(features[0] + features[1], features[0])
        self.conv1_1 = ConvBlock(features[1] + features[2], features[1])
        self.conv2_1 = ConvBlock(features[2] + features[3], features[2])
        self.conv3_1 = ConvBlock(features[3] + features[4], features[3])

        # Dense skip connections - level 2
        self.conv0_2 = ConvBlock(features[0] * 2 + features[1], features[0])
        self.conv1_2 = ConvBlock(features[1] * 2 + features[2], features[1])
        self.conv2_2 = ConvBlock(features[2] * 2 + features[3], features[2])

        # Dense skip connections - level 3
        self.conv0_3 = ConvBlock(features[0] * 3 + features[1], features[0])
        self.conv1_3 = ConvBlock(features[1] * 3 + features[2], features[1])

        # Dense skip connections - level 4
        self.conv0_4 = ConvBlock(features[0] * 4 + features[1], features[0])

        # Deep supervision outputs
        if self.deep_supervision:
            self.final1 = nn.Conv2d(features[0], num_classes, 1)
            self.final2 = nn.Conv2d(features[0], num_classes, 1)
            self.final3 = nn.Conv2d(features[0], num_classes, 1)
            self.final4 = nn.Conv2d(features[0], num_classes, 1)
        else:
            self.final = nn.Conv2d(features[0], num_classes, 1)

    def forward(self, x):
        # Encoder
        x0_0 = self.conv0_0(x)
        x1_0 = self.conv1_0(self.pool(x0_0))
        x2_0 = self.conv2_0(self.pool(x1_0))
        x3_0 = self.conv3_0(self.pool(x2_0))
        x4_0 = self.conv4_0(self.pool(x3_0))

        # Nested decoder - column 1
        x0_1 = self.conv0_1(torch.cat([x0_0, self.up(x1_0)], dim=1))
        x1_1 = self.conv1_1(torch.cat([x1_0, self.up(x2_0)], dim=1))
        x2_1 = self.conv2_1(torch.cat([x2_0, self.up(x3_0)], dim=1))
        x3_1 = self.conv3_1(torch.cat([x3_0, self.up(x4_0)], dim=1))

        # Nested decoder - column 2
        x0_2 = self.conv0_2(torch.cat([x0_0, x0_1, self.up(x1_1)], dim=1))
        x1_2 = self.conv1_2(torch.cat([x1_0, x1_1, self.up(x2_1)], dim=1))
        x2_2 = self.conv2_2(torch.cat([x2_0, x2_1, self.up(x3_1)], dim=1))

        # Nested decoder - column 3
        x0_3 = self.conv0_3(torch.cat([x0_0, x0_1, x0_2, self.up(x1_2)], dim=1))
        x1_3 = self.conv1_3(torch.cat([x1_0, x1_1, x1_2, self.up(x2_2)], dim=1))

        # Nested decoder - column 4
        x0_4 = self.conv0_4(torch.cat([x0_0, x0_1, x0_2, x0_3, self.up(x1_3)], dim=1))

        if self.deep_supervision:
            out1 = self.final1(x0_1)
            out2 = self.final2(x0_2)
            out3 = self.final3(x0_3)
            out4 = self.final4(x0_4)
            return (out1 + out2 + out3 + out4) / 4
        else:
            return self.final(x0_4)


def count_parameters(model):
    """Count trainable parameters."""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


if __name__ == "__main__":
    model = UNetPlusPlus(in_channels=1, num_classes=4)
    x = torch.randn(1, 1, 256, 256)
    out = model(x)
    print(f"Input:  {x.shape}")
    print(f"Output: {out.shape}")
    print(f"Parameters: {count_parameters(model):,}")
