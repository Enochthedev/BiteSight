"""API documentation configuration and customization."""

from typing import Dict, Any, List
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def custom_openapi(app: FastAPI) -> Dict[str, Any]:
    """Generate custom OpenAPI schema with enhanced documentation."""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Nutrition Feedback API",
        version="1.0.0",
        description="""
        ## AI-Powered Visual Nutrition Feedback System for Nigerian Students

        This API provides endpoints for a mobile-first nutrition feedback system that uses computer vision 
        to analyze meal images and provide culturally relevant nutritional guidance for Nigerian students.

        ### Key Features
        - **Image-based Food Recognition**: Upload meal photos for automatic Nigerian food identification
        - **Culturally Relevant Feedback**: Receive nutrition advice using familiar Nigerian food examples
        - **Meal History Tracking**: Track eating patterns over time with privacy controls
        - **Weekly Insights**: Get personalized nutrition insights and recommendations
        - **Consent Management**: Full control over data storage and privacy preferences

        ### Authentication
        Most endpoints require JWT authentication. Use the `/auth/login` endpoint to obtain an access token,
        then include it in the `Authorization` header as `Bearer <token>`.

        ### Rate Limiting
        API requests are rate-limited to 60 requests per minute per IP address. Rate limit information
        is included in response headers:
        - `X-RateLimit-Limit`: Maximum requests per minute
        - `X-RateLimit-Remaining`: Remaining requests in current window
        - `X-RateLimit-Reset`: Unix timestamp when the rate limit resets

        ### Error Handling
        All errors follow a consistent format:
        ```json
        {
            "error": {
                "code": 400,
                "message": "Error description",
                "type": "error_type",
                "timestamp": 1234567890.123,
                "path": "/api/v1/endpoint"
            }
        }
        ```

        ### File Uploads
        Image uploads are limited to 10MB and must be in JPEG or PNG format. Images are automatically
        processed and optimized for analysis.

        ### Privacy and Consent
        The system implements comprehensive consent management. Users must explicitly consent to:
        - Data processing for meal analysis
        - History storage for tracking and insights
        - Analytics for system improvement

        ### Nigerian Food Recognition
        The system is specifically trained to recognize common Nigerian foods including:
        - **Carbohydrates**: Rice (jollof, white, fried), yam, plantain, bread, amala, fufu
        - **Proteins**: Chicken, fish, beef, beans, eggs, moimoi
        - **Vegetables**: Efo riro, okra, ugwu, bitter leaf, tomato stew
        - **Snacks**: Suya, puff puff, chin chin, roasted plantain

        ### Support
        For technical support or questions about the API, contact the development team.
        """,
        routes=app.routes,
    )

    # Add custom tags for better organization
    openapi_schema["tags"] = [
        {
            "name": "authentication",
            "description": "User registration, login, and authentication management"
        },
        {
            "name": "consent",
            "description": "Privacy consent management and data usage preferences"
        },
        {
            "name": "meals",
            "description": "Meal image upload and management"
        },
        {
            "name": "inference",
            "description": "AI-powered food recognition and analysis"
        },
        {
            "name": "feedback",
            "description": "Nutritional feedback and recommendations"
        },
        {
            "name": "history",
            "description": "Meal history tracking and weekly insights"
        },
        {
            "name": "admin",
            "description": "Administrative functions for dataset and rule management"
        }
    ]

    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token obtained from the login endpoint"
        }
    }

    # Add common response schemas
    openapi_schema["components"]["schemas"].update({
        "ErrorResponse": {
            "type": "object",
            "properties": {
                "error": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "integer", "example": 400},
                        "message": {"type": "string", "example": "Error description"},
                        "type": {"type": "string", "example": "validation_error"},
                        "timestamp": {"type": "number", "example": 1234567890.123},
                        "path": {"type": "string", "example": "/api/v1/endpoint"}
                    }
                }
            }
        },
        "SuccessResponse": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "example": "Operation completed successfully"},
                "data": {"type": "object", "description": "Response data"}
            }
        },
        "NigerianFood": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "example": "Jollof Rice"},
                "local_names": {
                    "type": "array",
                    "items": {"type": "string"},
                    "example": ["Jollof", "Party Rice"]
                },
                "food_class": {
                    "type": "string",
                    "enum": ["carbohydrates", "proteins", "fats_oils", "vitamins", "minerals", "water"],
                    "example": "carbohydrates"
                },
                "confidence": {"type": "number", "minimum": 0, "maximum": 1, "example": 0.95}
            }
        },
        "NutritionFeedback": {
            "type": "object",
            "properties": {
                "overall_balance": {"type": "string", "example": "Good balance with room for improvement"},
                "missing_groups": {
                    "type": "array",
                    "items": {"type": "string"},
                    "example": ["vegetables", "fruits"]
                },
                "recommendations": {
                    "type": "array",
                    "items": {"type": "string"},
                    "example": ["Try adding some efo riro for vitamins", "Include fruits like orange or banana"]
                },
                "positive_aspects": {
                    "type": "array",
                    "items": {"type": "string"},
                    "example": ["Good protein source with chicken", "Adequate carbohydrates from rice"]
                }
            }
        }
    })

    # Add examples for common request/response patterns
    openapi_schema["components"]["examples"] = {
        "MealUploadSuccess": {
            "summary": "Successful meal upload",
            "value": {
                "message": "Meal uploaded successfully",
                "meal_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "processing"
            }
        },
        "FoodRecognitionResult": {
            "summary": "Food recognition results",
            "value": {
                "detected_foods": [
                    {
                        "name": "Jollof Rice",
                        "confidence": 0.95,
                        "food_class": "carbohydrates"
                    },
                    {
                        "name": "Fried Chicken",
                        "confidence": 0.88,
                        "food_class": "proteins"
                    }
                ],
                "analysis_complete": True
            }
        },
        "ValidationError": {
            "summary": "Validation error example",
            "value": {
                "error": {
                    "code": 422,
                    "message": "Validation error",
                    "type": "validation_error",
                    "details": [
                        {
                            "loc": ["body", "email"],
                            "msg": "field required",
                            "type": "value_error.missing"
                        }
                    ]
                }
            }
        }
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


def setup_api_docs(app: FastAPI) -> None:
    """Setup API documentation with custom configuration."""
    app.openapi = lambda: custom_openapi(app)


# Common response examples for reuse
COMMON_RESPONSES = {
    "400": {
        "description": "Bad Request",
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                "example": {
                    "error": {
                        "code": 400,
                        "message": "Invalid request data",
                        "type": "bad_request",
                        "timestamp": 1234567890.123,
                        "path": "/api/v1/endpoint"
                    }
                }
            }
        }
    },
    "401": {
        "description": "Unauthorized",
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                "example": {
                    "error": {
                        "code": 401,
                        "message": "Authentication required",
                        "type": "authentication_error",
                        "timestamp": 1234567890.123,
                        "path": "/api/v1/endpoint"
                    }
                }
            }
        }
    },
    "403": {
        "description": "Forbidden",
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                "example": {
                    "error": {
                        "code": 403,
                        "message": "Insufficient permissions or consent required",
                        "type": "permission_error",
                        "timestamp": 1234567890.123,
                        "path": "/api/v1/endpoint"
                    }
                }
            }
        }
    },
    "404": {
        "description": "Not Found",
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                "example": {
                    "error": {
                        "code": 404,
                        "message": "Resource not found",
                        "type": "not_found",
                        "timestamp": 1234567890.123,
                        "path": "/api/v1/endpoint"
                    }
                }
            }
        }
    },
    "422": {
        "description": "Validation Error",
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                "examples": {
                    "validation_error": {"$ref": "#/components/examples/ValidationError"}
                }
            }
        }
    },
    "429": {
        "description": "Rate Limit Exceeded",
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                "example": {
                    "error": {
                        "code": 429,
                        "message": "Rate limit exceeded",
                        "type": "rate_limit_error",
                        "retry_after": 60,
                        "timestamp": 1234567890.123,
                        "path": "/api/v1/endpoint"
                    }
                }
            }
        }
    },
    "500": {
        "description": "Internal Server Error",
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                "example": {
                    "error": {
                        "code": 500,
                        "message": "Internal server error",
                        "type": "internal_error",
                        "timestamp": 1234567890.123,
                        "path": "/api/v1/endpoint"
                    }
                }
            }
        }
    }
}
