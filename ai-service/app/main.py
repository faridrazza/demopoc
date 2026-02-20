from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import router
from .database import engine, Base

app = FastAPI(
    title="AI Speaking Service",
    description="AI-powered language learning with speech recognition",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables
Base.metadata.create_all(bind=engine)

# Include routes
app.include_router(router, tags=["ai-speaking"])

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "ai-speaking",
        "features": ["sentence-generation", "speech-recognition", "accuracy-scoring"]
    }
