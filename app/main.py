from fastapi import FastAPI, Request, HTTPException
from app.routers import comic_routers
from dotenv import load_dotenv
import os
from app.utils.logger import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

# Load environment variables from .env file
load_dotenv()


# Initialize the FastAPI app
app = FastAPI()

# Fetch allowed IPs and hosts from environment variables
ALLOWED_IPS = os.getenv("ALLOWED_IPS", "").split(",")  # Comma-separated list of IPs

# Middleware to validate IPs and Hosts
class AccessControlMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host  # Get client IP from the request
        host = request.headers.get("host", "").split(":")[0]  # Extract host without port
        
        # Deny access if the IP or host is not allowed
        if (ALLOWED_IPS and client_ip not in ALLOWED_IPS):
            logger.warning(f"Access denied for IP: {client_ip}, Host: {host}")
            return JSONResponse(status_code=403, content={"detail": "Access denied"})
        
        return await call_next(request)

# Add the middleware to the app
app.add_middleware(AccessControlMiddleware)

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
