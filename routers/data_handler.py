from fastapi import APIRouter, UploadFile, File, Form
from google import genai
from ai_helpers.gemini import GeminiCityAnalyzer
from ai_helpers.gemini2 import GeminiCityDataGetter
from geopy.distance import geodesic
from typing import List
from fastapi import Query
from pydantic import BaseModel, EmailStr
from fastapi import HTTPException
from firebase_admin import firestore
from fastapi import BackgroundTasks, Request
# from gemini_deduplicator import is_duplicate_incident  
from typing import Dict

router = APIRouter()
analyzer = GeminiCityAnalyzer()


class IncidentInput(BaseModel):
    lat: float
    lng: float
    image_url: str
    area: str


class UserRegisterInput(BaseModel):
    name: str
    email: EmailStr
    interests: list[str]
    password: str
    fcmToken: str  # Add FCM token to the input model
    lat: float  # Add latitude to the input model
    lng: float  # Add longitude to the input model
    area: str  # Add area to the input model

class UserLoginInput(BaseModel):
    email: EmailStr
    password: str

class UserInterestsInput(BaseModel):
    email: EmailStr
    interests: list[str]




# curl http://127.0.0.1:8000/data/get_data
@router.get("/get_data")
async def get_data_endpoint():
    """
    Handles GET requests to retrieve data.
    """
    return {"message": "This is your GET data endpoint!"}




# curl -X POST http://127.0.0.1:8000/data/incident/report \
# -H "Content-Type: application/json" \
# -d '{"lat": 12.9121, "lng": 77.6446, "area": "HSR Layout", "image_url": "https://picsum.photos/200/300"}'
@router.post("/incident/report")
async def report_incident(payload: IncidentInput, background_tasks: BackgroundTasks):
    result = analyzer.analyze_incident(
        image_url=payload.image_url,
        lat=payload.lat,
        lng=payload.lng,
        area=payload.area   
    )
    # If incident was successfully analyzed and saved, run alert in background
    if result.get("success"):
        background_tasks.add_task(analyzer.send_location_based_alert, payload.area, result["data"])
    return result
