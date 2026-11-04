from fastapi import APIRouter

from app.api.v1 import categories, health, ingredients, mixology, recipes, recommendations

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(categories.router)
api_router.include_router(ingredients.router)
api_router.include_router(recipes.router)
api_router.include_router(recommendations.router)
api_router.include_router(mixology.router)
