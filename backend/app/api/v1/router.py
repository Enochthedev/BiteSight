"""Main API router for v1 endpoints."""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, meals, feedback, history, admin, consent, inference, monitoring, workflows, cache, dataset, nutrition_rules

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(consent.router, prefix="/consent", tags=["consent"])
api_router.include_router(meals.router, prefix="/meals", tags=["meals"])
api_router.include_router(
    feedback.router, prefix="/feedback", tags=["feedback"])
api_router.include_router(history.router, prefix="/history", tags=["history"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(
    inference.router, prefix="/inference", tags=["inference"])
api_router.include_router(
    monitoring.router, prefix="/monitoring", tags=["monitoring"])
api_router.include_router(
    workflows.router, prefix="/workflows", tags=["workflows"])
api_router.include_router(cache.router, prefix="/cache", tags=["cache"])
api_router.include_router(dataset.router, prefix="/dataset", tags=["dataset"])
api_router.include_router(nutrition_rules.router,
                          prefix="/nutrition-rules", tags=["nutrition-rules"])
