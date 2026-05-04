"""
FastAPI Backend for Fetal Brain Segmentation.
Provides REST API for image upload, inference, and result retrieval.
"""

import io
import time
import logging
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from inference import get_predictor

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger(__name__)

# Supported image types
ALLOWED_TYPES = {'image/jpeg', 'image/png', 'image/bmp', 'image/tiff', 'image/webp'}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model on startup."""
    logger.info("🚀 Loading segmentation model...")
    try:
        predictor = get_predictor()
        logger.info(f"✅ Model loaded successfully (device: {predictor.device})")
    except Exception as e:
        logger.error(f"❌ Failed to load model: {e}")
    yield
    logger.info("👋 Shutting down...")


app = FastAPI(
    title="Fetal Head Segmentation API",
    description="AI-powered fetal head circumference segmentation from ultrasound images using U-Net++",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# app.include_router(chat_router)  # Removed chatbot

@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "name": "Fetal Head Segmentation API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "predict": "POST /predict/ - Upload image for segmentation",
            "health": "GET /health - Health check",
            "model_info": "GET /model-info - Model metadata",
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        predictor = get_predictor()
        model_loaded = predictor.model is not None
    except Exception:
        model_loaded = False

    return {
        "status": "healthy" if model_loaded else "degraded",
        "model_loaded": model_loaded,
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/model-info")
async def model_info():
    """Return model metadata."""
    try:
        predictor = get_predictor()
        return {
            "architecture": "U-Net++ (Nested U-Net)",
            "input_size": "256x256 grayscale",
            "num_classes": 2,
            "classes": ["Background", "Head"],
            "device": str(predictor.device),
            "training_info": predictor.model_info,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict/")
async def predict(file: UploadFile = File(...)):
    """
    Perform fetal head segmentation on uploaded ultrasound image.

    Returns segmentation mask, overlay, heatmap as base64, plus metrics.
    """
    request_start = time.time()

    # Validate file type
    if file.content_type and file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Supported: {', '.join(ALLOWED_TYPES)}"
        )

    # Read file
    try:
        contents = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({len(contents) / 1024 / 1024:.1f} MB). Max: {MAX_FILE_SIZE / 1024 / 1024:.0f} MB"
        )

    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Empty file uploaded")

    # Run inference
    try:
        predictor = get_predictor()
        result = predictor.predict(contents)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=f"Model not available: {str(e)}")
    except Exception as e:
        logger.error(f"Inference error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Inference failed: {str(e)}")

    total_time = (time.time() - request_start) * 1000

    logger.info(
        f"📊 Prediction complete | "
        f"File: {file.filename} | "
        f"Size: {len(contents) / 1024:.1f} KB | "
        f"Inference: {result['inference_time_ms']:.1f} ms | "
        f"Total: {total_time:.1f} ms | "
        f"Confidence: {result['confidence']:.2%}"
    )

    return {
        "success": True,
        "filename": file.filename,
        "mask": result['mask_b64'],
        "overlay": result['overlay_b64'],
        "heatmap": result['heatmap_b64'],
        "confidence": result['confidence'],
        "class_scores": result['class_scores'],
        "detected_structures": result['detected_structures'],
        "explanation": result['explanation'],
        "inference_time_ms": result['inference_time_ms'],
        "total_time_ms": round(total_time, 2),
        "image_size": result['image_size'],
    }


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )
