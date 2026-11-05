from fastapi import APIRouter

from app.api.v1 import (
    admin,
    agent,
    categories,
    health,
    ingredients,
    me,
    mixology,
    paths,
    recipes,
    recommendations,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(categories.router)
api_router.include_router(ingredients.router)
api_router.include_router(recipes.router)
api_router.include_router(recommendations.router)
api_router.include_router(mixology.router)
api_router.include_router(paths.router)
api_router.include_router(me.router)
api_router.include_router(admin.router)
api_router.include_router(agent.router)
