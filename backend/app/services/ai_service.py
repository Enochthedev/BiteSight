"""
AI Service for food recognition and analysis.
Handles model inference and nutritional analysis.
"""

import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from uuid import UUID
from PIL import Image

from app.core.config import settings
from app.ml.serving.model_server import ModelServer, ServingConfig
from app.ml.dataset.food_mapping import NigerianFoodMapper

logger = logging.getLogger(__name__)


class AIService:
    """Service for AI-powered food recognition and analysis."""
    
    def __init__(self):
        """Initialize AI service with model server."""
        self.model_server: Optional[ModelServer] = None
        self.food_mapper: Optional[NigerianFoodMapper] = None
        self.is_initialized = False
        
    def initialize(self):
        """Initialize the model server and food mapper."""
        try:
            logger.info("Initializing AI Service...")
            
            # Check if model file exists
            model_path = Path(settings.MODEL_PATH)
            if not model_path.exists():
                logger.warning(f"Model file not found: {settings.MODEL_PATH}")
                logger.warning("AI service will not be available")
                return
            
            # Check if food mapping exists
            mapping_path = Path(settings.FOOD_MAPPING_PATH)
            if not mapping_path.exists():
                logger.warning(f"Food mapping not found: {settings.FOOD_MAPPING_PATH}")
                logger.warning("AI service will not be available")
                return
            
            # Initialize food mapper
            self.food_mapper = NigerianFoodMapper(mapping_path)
            logger.info(f"Loaded food mapper with {len(self.food_mapper.food_classes)} food classes")
            
            # Create serving config
            config = ServingConfig(
                model_path=str(model_path),
                food_mapping_path=str(mapping_path),
                device=settings.INFERENCE_DEVICE,
                max_batch_size=settings.MAX_BATCH_SIZE,
                confidence_threshold=settings.CONFIDENCE_THRESHOLD,
                enable_batch_processing=True,
                max_concurrent_requests=settings.MAX_CONCURRENT_REQUESTS
            )
            
            # Initialize model server
            self.model_server = ModelServer(config)
            self.is_initialized = True
            
            logger.info("✓ AI Service initialized successfully")
            logger.info(f"  Model: {settings.MODEL_PATH}")
            logger.info(f"  Device: {settings.INFERENCE_DEVICE}")
            logger.info(f"  Confidence threshold: {settings.CONFIDENCE_THRESHOLD}")
            
        except Exception as e:
            logger.error(f"Failed to initialize AI service: {e}")
            logger.exception(e)
            self.is_initialized = False
    
    async def analyze_meal_image(
        self,
        image_path: str,
        meal_id: UUID,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Analyze a meal image and return detected foods.
        
        Args:
            image_path: Path to the meal image
            meal_id: Meal ID for tracking
            top_k: Number of top predictions to return
            
        Returns:
            Dictionary with detected foods and analysis
        """
        if not self.is_initialized or not self.model_server:
            logger.warning("AI service not initialized, returning mock results")
            return self._get_mock_results(meal_id)
        
        try:
            logger.info(f"Analyzing meal image: {meal_id}")
            
            # Load image
            image = Image.open(image_path).convert('RGB')
            
            # Run inference
            predictions = await self.model_server.predict_single(
                image_data=image,
                return_all_scores=True
            )
            
            if not predictions or len(predictions) == 0:
                logger.warning(f"No predictions for meal {meal_id}")
                return self._get_mock_results(meal_id)
            
            # Format detected foods
            detected_foods = []
            for pred in predictions[:top_k]:
                if pred.confidence >= settings.CONFIDENCE_THRESHOLD:
                    food_info = {
                        "food_name": pred.class_name.replace('_', ' ').title(),
                        "confidence": float(pred.confidence),
                        "food_class": pred.nutritional_category or "unknown",
                        "class_index": pred.class_index
                    }
                    
                    # Add local names if available
                    if pred.local_names:
                        food_info["local_names"] = pred.local_names
                    
                    detected_foods.append(food_info)
            
            # Analyze nutritional balance
            nutrition_analysis = self._analyze_nutrition(detected_foods)
            
            result = {
                "meal_id": str(meal_id),
                "detected_foods": detected_foods,
                "nutrition_analysis": nutrition_analysis,
                "analysis_status": "completed",
                "model_version": "1.0.0",
                "confidence_threshold": settings.CONFIDENCE_THRESHOLD
            }
            
            logger.info(f"✓ Analysis complete for meal {meal_id}: {len(detected_foods)} foods detected")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing meal {meal_id}: {e}")
            logger.exception(e)
            return self._get_mock_results(meal_id)
    
    def _analyze_nutrition(self, detected_foods: List[Dict]) -> Dict[str, Any]:
        """
        Analyze nutritional balance of detected foods.
        
        Args:
            detected_foods: List of detected food items
            
        Returns:
            Nutritional analysis
        """
        if not detected_foods:
            return {
                "balance_score": 0,
                "present_categories": [],
                "missing_categories": ["carbohydrates", "protein", "vitamins", "fats_oils"],
                "recommendations": ["Add a variety of foods from different food groups"]
            }
        
        # Count food categories
        categories = {}
        for food in detected_foods:
            category = food.get("food_class", "unknown")
            if category != "unknown":
                categories[category] = categories.get(category, 0) + 1
        
        present_categories = list(categories.keys())
        
        # Define essential categories
        essential_categories = ["carbohydrates", "protein", "vitamins"]
        missing_categories = [cat for cat in essential_categories if cat not in present_categories]
        
        # Calculate balance score (0-100)
        # Based on presence of essential categories
        balance_score = int((len(present_categories) / 6) * 100)  # 6 total categories
        
        # Generate recommendations
        recommendations = []
        if "protein" not in present_categories:
            recommendations.append("Add protein sources like beans, fish, or meat for body building")
        if "vitamins" not in present_categories:
            recommendations.append("Include vegetables or fruits for vitamins and minerals")
        if "carbohydrates" not in present_categories:
            recommendations.append("Add energy foods like rice, yam, or garri")
        
        if not recommendations:
            recommendations.append("Great! Your meal has a good balance of food groups")
        
        return {
            "balance_score": balance_score,
            "present_categories": present_categories,
            "missing_categories": missing_categories,
            "recommendations": recommendations,
            "category_counts": categories
        }
    
    def _get_mock_results(self, meal_id: UUID) -> Dict[str, Any]:
        """
        Get mock results when AI is not available.
        
        Args:
            meal_id: Meal ID
            
        Returns:
            Mock analysis results
        """
        return {
            "meal_id": str(meal_id),
            "detected_foods": [
                {
                    "food_name": "Jollof Rice",
                    "confidence": 0.85,
                    "food_class": "carbohydrates",
                    "class_index": 0
                },
                {
                    "food_name": "Fried Chicken",
                    "confidence": 0.72,
                    "food_class": "protein",
                    "class_index": 1
                }
            ],
            "nutrition_analysis": {
                "balance_score": 60,
                "present_categories": ["carbohydrates", "protein"],
                "missing_categories": ["vitamins"],
                "recommendations": [
                    "Add vegetables or fruits for vitamins and minerals"
                ],
                "category_counts": {
                    "carbohydrates": 1,
                    "protein": 1
                }
            },
            "analysis_status": "completed",
            "model_version": "mock",
            "note": "AI service not initialized - using mock results"
        }
    
    async def get_server_status(self) -> Dict[str, Any]:
        """Get AI service status."""
        if not self.is_initialized or not self.model_server:
            return {
                "status": "unavailable",
                "initialized": False,
                "message": "AI service not initialized"
            }
        
        try:
            server_status = self.model_server.get_server_status()
            return {
                "status": "healthy" if server_status["status"] == "healthy" else "unhealthy",
                "initialized": True,
                **server_status
            }
        except Exception as e:
            logger.error(f"Error getting server status: {e}")
            return {
                "status": "error",
                "initialized": True,
                "error": str(e)
            }
    
    def cleanup(self):
        """Cleanup AI service resources."""
        if self.model_server:
            self.model_server.cleanup()
        self.is_initialized = False
        logger.info("AI Service cleaned up")


# Global AI service instance
_ai_service: Optional[AIService] = None


def get_ai_service() -> AIService:
    """Get or create global AI service instance."""
    global _ai_service
    
    if _ai_service is None:
        _ai_service = AIService()
    
    return _ai_service


def initialize_ai_service():
    """Initialize the global AI service."""
    service = get_ai_service()
    service.initialize()


def cleanup_ai_service():
    """Cleanup the global AI service."""
    global _ai_service
    
    if _ai_service:
        _ai_service.cleanup()
        _ai_service = None
