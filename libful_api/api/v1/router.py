from fastapi import APIRouter

from libful_api.api.v1.endpoints import users


router = APIRouter()

router.include_router(users.router)
