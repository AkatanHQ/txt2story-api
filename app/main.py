from fastapi import FastAPI
from app.routers import comic_routers

app = FastAPI()

app.include_router(comic_routers.router)

@app.get("/")
async def root():
    return {"message": "Welcome to the Comic Generator API!"}
