"""
Inference Pipeline for Fetal Brain Segmentation.
Handles model loading, image preprocessing, prediction, and visualization generation.
"""

import io
import base64
import time
from pathlib import Path

import numpy as np
from PIL import Image

import torch
import torch.nn.functional as F

from model import UNetPlusPlus

# Constants
IMG_SIZE = 256
NUM_CLASSES = 2
CLASS_NAMES = ['Background', 'Head']

# Visualization colors (RGBA)
CLASS_COLORS = np.array([
    [0, 0, 0, 0],          # Background - transparent
    [255, 60, 60, 180],     # Head - red
], dtype=np.uint8)

# Solid colors for mask display
CLASS_COLORS_SOLID = np.array([
    [20, 20, 30],           # Background - dark
    [255, 60, 60],          # Head - red
], dtype=np.uint8)


class SegmentationPredictor:
    """Manages model loading and inference for segmentation."""

    def __init__(self, model_path=None, device=None):
        if device is None:
            if torch.cuda.is_available():
                self.device = torch.device('cuda')
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                self.device = torch.device('mps')
            else:
                self.device = torch.device('cpu')
        else:
            self.device = torch.device(device)

        self.model = None
        self.model_info = {}

        if model_path:
            self.load_model(model_path)

    def load_model(self, model_path):
        """Load trained model from checkpoint."""
        model_path = Path(model_path)
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")

        self.model = UNetPlusPlus(in_channels=1, num_classes=NUM_CLASSES, deep_supervision=True)

        checkpoint = torch.load(model_path, map_location=self.device, weights_only=False)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model = self.model.to(self.device)
        self.model.eval()

        self.model_info = {
            'epoch': checkpoint.get('epoch', 'unknown'),
            'val_dice': checkpoint.get('val_dice', {}),
            'val_loss': checkpoint.get('val_loss', 0),
            'device': str(self.device),
        }

        print(f"✅ Model loaded (epoch {self.model_info['epoch']}, device: {self.device})")

    def preprocess(self, image_bytes: bytes) -> tuple:
        """
        Preprocess uploaded image for inference.

        Returns:
            tensor: (1, 1, 256, 256) normalized tensor
            original_image: PIL Image (for overlay)
            original_size: (width, height)
        """
        img = Image.open(io.BytesIO(image_bytes))
        original_size = img.size  # (W, H)
        original_image = img.convert('RGB')

        # Convert to grayscale and resize
        gray = img.convert('L').resize((IMG_SIZE, IMG_SIZE), Image.BILINEAR)

        # Normalize to [0, 1]
        arr = np.array(gray, dtype=np.float32) / 255.0

        # To tensor: (1, 1, H, W)
        tensor = torch.from_numpy(arr).unsqueeze(0).unsqueeze(0).float()

        return tensor, original_image, original_size

    def validate_ultrasound(self, image: Image.Image):
        """Heuristic check to reject images that are clearly not ultrasound scans."""
        rgb = np.array(image.convert('RGB'))
        r = rgb[:, :, 0].astype(int)
        g = rgb[:, :, 1].astype(int)
        b = rgb[:, :, 2].astype(int)
        
        # Color difference check
        color_diff = np.mean(np.abs(r - g)) + np.mean(np.abs(r - b)) + np.mean(np.abs(g - b))
        if color_diff > 15:
            raise ValueError("The uploaded image appears to be in color. Please upload a grayscale ultrasound scan.")
            
        # Dark region check
        gray = np.array(image.convert('L'))
        dark_ratio = np.sum(gray < 25) / gray.size
        # Medical ultrasounds have significant black regions.
        if dark_ratio < 0.05:
            raise ValueError("The uploaded image lacks the characteristic dark background (acoustic shadowing) of an ultrasound scan.")

    @torch.no_grad()
    def predict(self, image_bytes: bytes) -> dict:
        """
        Run full inference pipeline.

        Args:
            image_bytes: Raw image bytes from upload

        Returns:
            dict with mask_b64, overlay_b64, heatmap_b64, confidence, class_scores, etc.
        """
        if self.model is None:
            raise RuntimeError("Model not loaded")

        start_time = time.time()

        # Preprocess
        tensor, original_image, original_size = self.preprocess(image_bytes)
        
        # Validate that it's actually an ultrasound
        self.validate_ultrasound(original_image)
        
        tensor = tensor.to(self.device)

        # Inference
        output = self.model(tensor)  # (1, C, H, W)
        probabilities = F.softmax(output, dim=1)  # (1, C, H, W)

        # Move to CPU
        probs_np = probabilities.cpu().numpy()[0]  # (C, H, W)
        pred_classes = probs_np.argmax(axis=0)  # (H, W)

        inference_time = time.time() - start_time

        # Generate visualizations
        mask_image = self._create_mask_image(pred_classes, original_size)
        overlay_image = self._create_overlay(original_image, pred_classes, original_size)
        heatmap_image = self._create_heatmap(probs_np, original_size)

        # Confidence scores
        class_scores = {}
        for c in range(NUM_CLASSES):
            mask_c = (pred_classes == c)
            if mask_c.any():
                class_scores[CLASS_NAMES[c]] = round(float(probs_np[c][mask_c].mean()), 4)
            else:
                class_scores[CLASS_NAMES[c]] = 0.0

        overall_confidence = np.mean([v for k, v in class_scores.items() if k != 'Background' and v > 0])

        # Guardrail against out-of-distribution images (like MRIs or Fetal body scans)
        # Real fetal brain ultrasounds usually result in > 85% confidence. 
        # MRIs and out-of-distribution imaging tend to get 75-80% due to forced hallucination.
        if not np.isnan(overall_confidence) and overall_confidence < 0.82:
            raise ValueError(f"Model confidence too low ({overall_confidence:.1%}). The image appears to be an MRI, fetal body scan, or an unclear ultrasound. Please upload a clear fetal brain axial/sagittal plane.")

        # Explanation
        detected_structures = [
            name for name, score in class_scores.items()
            if name != 'Background' and score > 0.1
        ]
        explanation = self._generate_explanation(detected_structures, class_scores)

        return {
            'mask_b64': self._pil_to_base64(mask_image),
            'overlay_b64': self._pil_to_base64(overlay_image),
            'heatmap_b64': self._pil_to_base64(heatmap_image),
            'confidence': round(float(overall_confidence), 4) if not np.isnan(overall_confidence) else 0.0,
            'class_scores': class_scores,
            'detected_structures': detected_structures,
            'explanation': explanation,
            'inference_time_ms': round(inference_time * 1000, 2),
            'image_size': {'width': original_size[0], 'height': original_size[1]},
        }

    def _create_mask_image(self, pred_classes, original_size):
        """Create colored segmentation mask."""
        mask_rgb = CLASS_COLORS_SOLID[pred_classes]  # (H, W, 3)
        mask_img = Image.fromarray(mask_rgb, 'RGB')
        mask_img = mask_img.resize(original_size, Image.NEAREST)
        return mask_img

    def _create_overlay(self, original_image, pred_classes, original_size, alpha=0.5):
        """Create overlay of mask on original image."""
        # Resize mask colors to original size
        mask_rgba = CLASS_COLORS[pred_classes]  # (H, W, 4)
        mask_overlay = Image.fromarray(mask_rgba, 'RGBA')
        mask_overlay = mask_overlay.resize(original_size, Image.NEAREST)

        # Create overlay
        original_rgba = original_image.convert('RGBA')
        overlay = Image.alpha_composite(original_rgba, mask_overlay)
        return overlay.convert('RGB')

    def _create_heatmap(self, probs, original_size):
        """Create confidence heatmap (max non-background probability)."""
        # Max probability for Head class
        max_prob = probs[1]  # (H, W) - Head class probability

        # Create heatmap using matplotlib colormap
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.cm as cm

        heatmap_colored = cm.jet(max_prob)[:, :, :3]  # (H, W, 3) in [0,1]
        heatmap_uint8 = (heatmap_colored * 255).astype(np.uint8)
        heatmap_img = Image.fromarray(heatmap_uint8, 'RGB')
        heatmap_img = heatmap_img.resize(original_size, Image.BILINEAR)
        return heatmap_img

    def _generate_explanation(self, detected_structures, class_scores):
        """Generate clinical explanation text."""
        if not detected_structures:
            return (
                "The fetal head was not clearly detected in this image. "
                "This may indicate the ultrasound plane does not capture the target structures, "
                "or the image quality may be insufficient for segmentation."
            )

        lines = [
            "🧠 **Fetal Head Segmentation Analysis**\n",
            "The AI model has identified the following structures in the ultrasound image:\n",
        ]

        structure_desc = {
            'Head': 'Fetal head circumference — the primary measurement region for prenatal development.',
        }

        for struct in detected_structures:
            conf = class_scores.get(struct, 0)
            desc = structure_desc.get(struct, '')
            lines.append(f"• **{struct}** (confidence: {conf:.1%}): {desc}")

        lines.append(
            "\n⚠️ *This is an AI-assisted analysis for research purposes only. "
            "Clinical decisions should always be made by qualified medical professionals.*"
        )

        return '\n'.join(lines)

    @staticmethod
    def _pil_to_base64(image: Image.Image) -> str:
        """Convert PIL Image to base64 string."""
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        return base64.b64encode(buffer.getvalue()).decode('utf-8')


# Singleton instance
_predictor = None


def get_predictor() -> SegmentationPredictor:
    """Get or create the singleton predictor."""
    global _predictor
    if _predictor is None:
        model_path = Path(__file__).parent / "saved_models" / "model.pth"
        _predictor = SegmentationPredictor(model_path=model_path)
    return _predictor
