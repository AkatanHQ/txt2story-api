from fastapi import FastAPI, Request, HTTPException
from app.routers import comic_routers
from dotenv import load_dotenv
import os
from app.utils.logger import logger


# Load environment variables from .env file
load_dotenv()

# Initialize the FastAPI app
app = FastAPI()

# Include application routers
app.include_router(comic_routers.router)

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to the Comic Generator API!"}

# Health check endpoint for monitoring tools
@app.get("/health")
async def health():
    return {"status": "ok"}
