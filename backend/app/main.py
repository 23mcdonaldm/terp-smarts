from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import transcript, courses

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(transcript.router, prefix="/api/transcript", tags=["transcript"])
app.include_router(courses.router, prefix="/api/courses", tags=["courses"])