"""
{{SERVICE_NAME}} - FastAPI application
"""
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title="{{SERVICE_NAME}}",
    description="A Python service built with FastAPI",
    version="0.1.0",
)


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "{{SERVICE_NAME}} is running"}


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        service="{{SERVICE_NAME}}",
        version="0.1.0"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
