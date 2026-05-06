from fastapi import FastAPI

from libful_api.api.v1.router import router as api_v1_router


app = FastAPI(title="libful API")

app.include_router(api_v1_router, prefix="/api/v1")
