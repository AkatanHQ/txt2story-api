from fastapi import FastAPI, HTTPException
from app.routes import comic

app = FastAPI(title="Comic API")

app.include_router(comic.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Comic API"}
