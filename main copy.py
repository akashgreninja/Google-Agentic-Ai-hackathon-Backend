from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import data_handler # Assuming 'routers' is a package/directory

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
