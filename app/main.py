from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.mcp_server import mcp


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with mcp.session_manager.run():
        yield


app = FastAPI(
    title="Health Insurance Policy Advisor API",
    description="Backend API for the GenAI Health Insurance Policy Advisor",
    version="1.0.0",
    lifespan=lifespan,
)


app.include_router(router)


@app.get("/")
def root():
    return {
        "message": "Health Insurance Policy Advisor API"
    }


app.mount("/", mcp.streamable_http_app())

