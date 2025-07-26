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


# curl -X GET "http://127.0.0.1:8000/data/get_incidents_by_route?source_lat=12.9121&source_lng=77.6446&dest_lat=12.9784&dest_lng=77.6408"
@router.get("/get_incidents_by_route")
async def get_incidents_by_route(
    source_lat: float,
    source_lng: float,
    dest_lat: float,
    dest_lng: float
):
    try:
        getter = GeminiCityDataGetter()
        incidents = getter.get_incidents_along_route(source_lat, source_lng, dest_lat, dest_lng)
        return {"incidents": incidents}
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        return {"error": str(e), "trace": traceback_str}


# curl -X GET "http://127.0.0.1:8000/data/get_relevant_incidents?lat=12.9121&lng=77.6446&radius_km=1"
@router.get("/get_relevant_incidents")
async def get_relevant_incidents(
    lat: float = None,
    lng: float = None,
    user_id: str = None,
    radius_km: float = 10
):
    try:
        getter = GeminiCityDataGetter()
        user_location = (lat, lng) if lat is not None and lng is not None else None
        incidents = getter.get_relevant_incidents(user_location=user_location, user_id=user_id, radius_km=radius_km)
        return {"incidents": incidents}
    except Exception as e:
        import traceback
        return {"error": str(e), "trace": traceback.format_exc()}


# curl -X POST http://127.0.0.1:8000/data/register \
# -H "Content-Type: application/json" \
# -d '{"name": "John Doe", "email": "john@example.com", "interests": ["Flood", "Fire"], "password": "secret"}'
@router.post("/register")
async def register_user(user: UserRegisterInput):
    db = firestore.client()
    users_ref = db.collection("users")
    if users_ref.document(user.email).get().exists:
        raise HTTPException(status_code=400, detail="Email already registered.")

    user_data = user.dict()

    # Add location field with geo-coordinates and area from the API body
    user_data["location"] = {
        "area": user.area,  # Use provided area
        "geo": {"lat": user.lat, "lng": user.lng}  # Use provided geo-coordinates
    }

    users_ref.document(user.email).set(user_data)
    user_data.pop("password")  # Don't return password
    return {"message": "User registered successfully.", "user": user_data}


# curl -X POST http://127.0.0.1:8000/data/login \
# -H "Content-Type: application/json" \
# -d '{"email": "john@example.com", "password": "secret"}'
@router.post("/login")
async def login_user(user: UserLoginInput):
    db = firestore.client()
    users_ref = db.collection("users")
    doc = users_ref.document(user.email).get()
    if not doc.exists:
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    user_data = doc.to_dict()
    # Password check is skipped for demo; add real password check in production
    user_data.pop("password", None)
    return {"message": "Login successful.", "user": user_data}


# curl -X POST http://127.0.0.1:8000/data/update_interests \
# -H "Content-Type: application/json" \
# -d '{"email": "john@example.com", "interests": ["Flood", "Fire", "Accident"]}'
@router.post("/update_interests")
async def update_user_interests(data: UserInterestsInput):
    db = firestore.client()
    users_ref = db.collection("users")
    doc_ref = users_ref.document(data.email)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="User not found.")
    doc_ref.update({"interests": data.interests})
    return {"message": "User interests updated successfully.", "email": data.email, "interests": data.interests}


# curl -X GET "http://127.0.0.1:8000/data/agentic_predictive_layer?lat=12.9121&lng=77.6446&radius_km=1"
@router.get("/predictive_layer_for_current_location")
async def agentic_predictive_layer(lat: float = None, lng: float = None, radius_km: float = 10):
    getter = GeminiCityDataGetter()
    user_location = (lat, lng) if lat is not None and lng is not None else None
    incidents = getter.get_relevant_incidents(user_location=user_location, radius_km=radius_km)
    analysis = getter.agentic_predictive_analysis(incidents)
    return {"analysis": analysis, "incidents": incidents}


# curl -X GET "http://127.0.0.1:8000/data/agentic_predictive_route?source_lat=12.9121&source_lng=77.6446&dest_lat=12.9784&dest_lng=77.6408"
@router.get("/predictive_layer_for_route")
async def agentic_predictive_route(
    source_lat: float,
    source_lng: float,
    dest_lat: float,
    dest_lng: float
):
    getter = GeminiCityDataGetter()
    incidents = getter.get_incidents_along_route(source_lat, source_lng, dest_lat, dest_lng)
    analysis = getter.agentic_predictive_analysis(incidents)
    return {"analysis": analysis, "incidents": incidents}



# @router.post("/check_duplicate")
# async def check_duplicate_incident(incident: Request) -> Dict[str, bool]:
#     try:
#         data = await incident.json()
#         is_dup = is_duplicate_incident(data)
#         return {"duplicate": is_dup}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error checking duplicate: {e}")