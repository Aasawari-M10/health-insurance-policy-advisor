from fastapi import FastAPI

from app.api.routes import router


app = FastAPI(
    title="Health Insurance Policy Advisor API",
    description="Backend API for the GenAI Health Insurance Policy Advisor",
    version="1.0.0",
)


app.include_router(router)


@app.get("/")
def root():
    return {
        "message": "Health Insurance Policy Advisor API"
    }