from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import data_handler # Assuming 'routers' is a package/directory
import uvicorn
import os
app = FastAPI()

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the router from data_handler.py
# The prefix ensures that all routes in data_handler will start with /data
app.include_router(data_handler.router, prefix="/data", tags=["Data Operations"])

@app.get("/")
async def root():
    return {"message": "Hello World from main.py"}
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port)