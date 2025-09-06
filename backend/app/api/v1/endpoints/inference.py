"""
FastAPI endpoints for food recognition inference.
Provides REST API for model serving with proper error handling and validation.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any, Union
import logging
from pathlib import Path
import tempfile
import asyncio
from PIL import Image
import io
import json

from pydantic import BaseModel, Field, validator
from app.ml.serving.model_server import get_server_instance, ServingConfig
from app.ml.inference.predictor import PredictionResult
from app.core.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Response models


class PredictionResponse(BaseModel):
    """Response model for single prediction."""
    class_name: str
    confidence: float
    class_index: int
    nutritional_category: Optional[str] = None
    local_names: Optional[List[str]] = None
    inference_time_ms: Optional[float] = None


class BatchPredictionResponse(BaseModel):
    """Response model for batch predictions."""
    predictions: List[Optional[PredictionResponse]]
    total_images: int
    successful_predictions: int
    batch_inference_time_ms: float


class NutritionAnalysisResponse(BaseModel):
    """Response model for nutrition analysis."""
    detected_foods: List[Dict[str, Any]]
    category_distribution: Dict[str, int]
    missing_categories: List[str]
    balance_score: float
    total_foods_detected: int
    recommendations: Optional[Dict[str, List[str]]] = None
    analysis_time_ms: float


class ServerStatusResponse(BaseModel):
    """Response model for server status."""
    status: str
    uptime_seconds: float
    models: List[Dict[str, Any]]
    config: Dict[str, Any]


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: Optional[str] = None
    error_code: Optional[str] = None

# Request models


class PredictionRequest(BaseModel):
    """Request model for prediction with base64 image."""
    image_base64: str = Field(..., description="Base64 encoded image")
    return_all_scores: bool = Field(
        False, description="Return all top-k predictions")
    model_id: str = Field("primary", description="Model identifier")


class BatchPredictionRequest(BaseModel):
    """Request model for batch prediction."""
    images_base64: List[str] = Field(...,
                                     description="List of base64 encoded images")
    return_all_scores: bool = Field(
        False, description="Return all top-k predictions")
    model_id: str = Field("primary", description="Model identifier")


class NutritionAnalysisRequest(BaseModel):
    """Request model for nutrition analysis."""
    images_base64: List[str] = Field(...,
                                     description="List of meal images as base64")
    model_id: str = Field("primary", description="Model identifier")

# Dependency to get server instance


def get_model_server():
    """Get model server instance."""
    try:
        settings = get_settings()

        # Configure server based on settings
        config = ServingConfig(
            model_path=getattr(settings, 'MODEL_PATH',
                               'models/best_model.pth'),
            food_mapping_path=getattr(
                settings, 'FOOD_MAPPING_PATH', 'dataset/metadata/nigerian_foods.json'),
            device=getattr(settings, 'INFERENCE_DEVICE', 'auto'),
            max_batch_size=getattr(settings, 'MAX_BATCH_SIZE', 16),
            confidence_threshold=getattr(
                settings, 'CONFIDENCE_THRESHOLD', 0.1),
            max_concurrent_requests=getattr(
                settings, 'MAX_CONCURRENT_REQUESTS', 10)
        )

        return get_server_instance(config)
    except Exception as e:
        logger.error(f"Failed to get model server: {e}")
        raise HTTPException(status_code=500, detail="Model server unavailable")

# Utility functions


def decode_base64_image(base64_str: str) -> Image.Image:
    """Decode base64 string to PIL Image."""
    try:
        import base64

        # Remove data URL prefix if present
        if base64_str.startswith('data:image'):
            base64_str = base64_str.split(',')[1]

        image_data = base64.b64decode(base64_str)
        image = Image.open(io.BytesIO(image_data)).convert('RGB')
        return image
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid image data: {str(e)}")


def convert_prediction_result(result: PredictionResult, inference_time_ms: float = None) -> PredictionResponse:
    """Convert PredictionResult to response model."""
    return PredictionResponse(
        class_name=result.class_name,
        confidence=result.confidence,
        class_index=result.class_index,
        nutritional_category=result.nutritional_category,
        local_names=result.local_names,
        inference_time_ms=inference_time_ms
    )

# API Endpoints


@router.post("/predict", response_model=Union[PredictionResponse, List[PredictionResponse]])
async def predict_food(
    request: PredictionRequest,
    server=Depends(get_model_server)
):
    """
    Predict food class from single image.

    - **image_base64**: Base64 encoded image
    - **return_all_scores**: Whether to return all top-k predictions
    - **model_id**: Model identifier (default: "primary")
    """
    try:
        import time
        start_time = time.time()

        # Decode image
        image = decode_base64_image(request.image_base64)

        # Run prediction
        result = await server.predict_single(
            image,
            model_id=request.model_id,
            return_all_scores=request.return_all_scores
        )

        inference_time_ms = (time.time() - start_time) * 1000

        if result is None:
            raise HTTPException(status_code=500, detail="Prediction failed")

        # Convert result(s)
        if isinstance(result, list):
            return [convert_prediction_result(r, inference_time_ms) for r in result]
        else:
            return convert_prediction_result(result, inference_time_ms)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict/upload")
async def predict_food_upload(
    file: UploadFile = File(...),
    return_all_scores: bool = Form(False),
    model_id: str = Form("primary"),
    server=Depends(get_model_server)
):
    """
    Predict food class from uploaded image file.

    - **file**: Image file (JPEG, PNG)
    - **return_all_scores**: Whether to return all top-k predictions
    - **model_id**: Model identifier
    """
    try:
        import time
        start_time = time.time()

        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400, detail="File must be an image")

        # Read and process image
        image_data = await file.read()
        image = Image.open(io.BytesIO(image_data)).convert('RGB')

        # Run prediction
        result = await server.predict_single(
            image,
            model_id=model_id,
            return_all_scores=return_all_scores
        )

        inference_time_ms = (time.time() - start_time) * 1000

        if result is None:
            raise HTTPException(status_code=500, detail="Prediction failed")

        # Convert result(s)
        if isinstance(result, list):
            return [convert_prediction_result(r, inference_time_ms) for r in result]
        else:
            return convert_prediction_result(result, inference_time_ms)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict/batch", response_model=BatchPredictionResponse)
async def predict_batch(
    request: BatchPredictionRequest,
    server=Depends(get_model_server)
):
    """
    Predict food classes for batch of images.

    - **images_base64**: List of base64 encoded images
    - **return_all_scores**: Whether to return all top-k predictions
    - **model_id**: Model identifier
    """
    try:
        import time
        start_time = time.time()

        if len(request.images_base64) == 0:
            raise HTTPException(status_code=400, detail="No images provided")

        if len(request.images_base64) > 50:  # Limit batch size
            raise HTTPException(
                status_code=400, detail="Batch size too large (max 50)")

        # Decode images
        images = []
        for i, base64_str in enumerate(request.images_base64):
            try:
                image = decode_base64_image(base64_str)
                images.append(image)
            except Exception as e:
                logger.warning(f"Failed to decode image {i}: {e}")
                images.append(None)

        # Run batch prediction
        results = await server.predict_batch(
            images,
            model_id=request.model_id,
            return_all_scores=request.return_all_scores
        )

        batch_inference_time_ms = (time.time() - start_time) * 1000

        # Convert results
        predictions = []
        successful_count = 0

        for result in results:
            if result is not None:
                if isinstance(result, list):
                    predictions.append(
                        [convert_prediction_result(r) for r in result])
                else:
                    predictions.append(convert_prediction_result(result))
                successful_count += 1
            else:
                predictions.append(None)

        return BatchPredictionResponse(
            predictions=predictions,
            total_images=len(request.images_base64),
            successful_predictions=successful_count,
            batch_inference_time_ms=batch_inference_time_ms
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/nutrition", response_model=NutritionAnalysisResponse)
async def analyze_meal_nutrition(
    request: NutritionAnalysisRequest,
    server=Depends(get_model_server)
):
    """
    Analyze nutritional content of a meal from multiple images.

    - **images_base64**: List of meal images as base64
    - **model_id**: Model identifier
    """
    try:
        import time
        start_time = time.time()

        if len(request.images_base64) == 0:
            raise HTTPException(status_code=400, detail="No images provided")

        if len(request.images_base64) > 20:  # Limit for nutrition analysis
            raise HTTPException(
                status_code=400, detail="Too many images for analysis (max 20)")

        # Decode images
        images = []
        for i, base64_str in enumerate(request.images_base64):
            try:
                image = decode_base64_image(base64_str)
                images.append(image)
            except Exception as e:
                logger.warning(f"Failed to decode image {i}: {e}")
                # Skip invalid images
                continue

        if not images:
            raise HTTPException(
                status_code=400, detail="No valid images provided")

        # Run nutrition analysis
        result = await server.analyze_meal_nutrition(
            images,
            model_id=request.model_id
        )

        analysis_time_ms = (time.time() - start_time) * 1000

        if result is None:
            raise HTTPException(
                status_code=500, detail="Nutrition analysis failed")

        return NutritionAnalysisResponse(
            detected_foods=result['detected_foods'],
            category_distribution=result['category_distribution'],
            missing_categories=result['missing_categories'],
            balance_score=result['balance_score'],
            total_foods_detected=result['total_foods_detected'],
            recommendations=result.get('recommendations'),
            analysis_time_ms=analysis_time_ms
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Nutrition analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=ServerStatusResponse)
async def get_server_status(server=Depends(get_model_server)):
    """
    Get server status and model information.
    """
    try:
        status = server.get_server_status()
        return ServerStatusResponse(**status)
    except Exception as e:
        logger.error(f"Status check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check(server=Depends(get_model_server)):
    """
    Perform health check on the model server.
    """
    try:
        is_healthy = await server.health_check()

        if is_healthy:
            return {"status": "healthy", "timestamp": time.time()}
        else:
            raise HTTPException(status_code=503, detail="Service unhealthy")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models")
async def list_models(server=Depends(get_model_server)):
    """
    List available models and their information.
    """
    try:
        models_info = server.model_manager.list_models()
        return {
            "models": [
                {
                    "model_id": info.model_id,
                    "num_classes": info.num_classes,
                    # Limit for response size
                    "class_names": info.class_names[:10],
                    "loaded_at": info.loaded_at,
                    "last_used": info.last_used,
                    "prediction_count": info.prediction_count,
                    "average_inference_time": info.average_inference_time
                }
                for info in models_info
            ]
        }
    except Exception as e:
        logger.error(f"List models error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Note: Exception handlers are now handled globally in main.py
