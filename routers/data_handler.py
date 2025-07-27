# Removed stray email line
from fastapi import Body
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from datetime import datetime, timedelta



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
import json
# from gemini_deduplicator import is_duplicate_incident  
from typing import Dict

router = APIRouter()
analyzer = GeminiCityAnalyzer()
load_dotenv()

class IncidentInput(BaseModel):
    lat: float
    lng: float
    image_url: str
    area: str

class SendAuthorityRequest(BaseModel):
    to_email: EmailStr = None  # Optional, can be determined by AI
    subject: str
    message: str


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


class PlaceRequest(BaseModel):
    place: str


class UpdateInterestInput(BaseModel):
    email: EmailStr
    category: str
    action: str | int  # can be 'add', 'remove', or an integer (e.g., -1)


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
    if result.get("success") and "data" in result:
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

@router.post("/update_interests")
async def update_user_interests(data: UpdateInterestInput):

    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("update_user_interests")

    db = firestore.client()
    users_ref = db.collection("users")
    doc_ref = users_ref.document(data.email)
    doc = doc_ref.get()
    if not doc.exists:
        logger.error(f"User not found: {data.email}")
        raise HTTPException(status_code=404, detail="User not found.")

    user_data = doc.to_dict()
    interests = user_data.get("interests", {})
    logger.info(f"Original interests: {interests}")

    # Convert legacy list to dict
    if isinstance(interests, list):
        interests = {cat: {"count": 1, "last_updated": datetime.utcnow().isoformat()} for cat in interests}
        logger.info(f"Converted legacy interests to dict: {interests}")

    now = datetime.utcnow()
    threshold = now - timedelta(days=30)  # 30 days threshold

    # Remove interests not updated within threshold
    interests = {
        cat: val for cat, val in interests.items()
        if datetime.fromisoformat(val.get("last_updated", now.isoformat())) >= threshold
    }
    logger.info(f"Filtered interests (within threshold): {interests}")

    cat = data.category
    action = data.action
    logger.info(f"Action received: {action} for category: {cat}")
    if isinstance(action, int):
        # Only allow +1 or -1
        if action not in [1, -1]:
            logger.error(f"Invalid integer action: {action}. Only +1 or -1 allowed.")
            raise HTTPException(status_code=400, detail="Integer action must be +1 or -1.")
        if cat in interests:
            interests[cat]["count"] += action
            interests[cat]["last_updated"] = now.isoformat()
            if interests[cat]["count"] <= 0:
                interests.pop(cat)
        elif action == 1:
            interests[cat] = {"count": 1, "last_updated": now.isoformat()}
    elif action == "add":
        if cat in interests:
            interests[cat]["count"] += 1
        else:
            interests[cat] = {"count": 1, "last_updated": now.isoformat()}
        interests[cat]["last_updated"] = now.isoformat()
    elif action == "remove":
        if cat in interests:
            interests[cat]["count"] -= 1
            interests[cat]["last_updated"] = now.isoformat()
            if interests[cat]["count"] <= 0:
                interests.pop(cat)
    else:
        logger.error(f"Invalid action: {action}")
        raise HTTPException(status_code=400, detail="Invalid action. Use 'add', 'remove', or an integer.")

    logger.info(f"Updated interests: {interests}")
    # Save back to Firestore
    doc_ref.update({"interests": interests})
    return {"success": True, "interests": interests}



@router.get("/get_relevant_incidents_summary")
async def get_relevant_incidents_summary(
    lat: float = None,
    lng: float = None,
    user_id: str = None,
    radius_km: float = 10
):
    try:
        getter = GeminiCityDataGetter()
        user_location = (lat, lng) if lat is not None and lng is not None else None
        result = getter.get_relevant_incidents_summary(user_id=user_id, user_location=user_location, radius_km=radius_km)
        return result
    except Exception as e:
        import traceback
        return {"error": str(e), "trace": traceback.format_exc()}
    




@router.post("/get_latlng_for_place")
async def get_latlng_for_place(req: PlaceRequest):
    """
    Given a place name, use Gemini to return the accurate latitude and longitude.
    Accepts JSON body: {"place": "city_name"}
    """
    prompt = (
        f"You are a geocoding assistant. Given the place name: '{req.place}', return ONLY the accurate latitude and longitude as a JSON object in this format: {{'lat': ..., 'lng': ...}}. Do not include any explanation, markdown, or extra text."
    )

    client = genai.Client()

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt]
        )
        text = response.text.strip().replace("'", '"')
        latlng = json.loads(text)
        return latlng

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/send_to_authority")
async def send_to_authority(req: SendAuthorityRequest):
    """
    Sends an email to the specified authority with the given subject and message using Gmail SMTP.
    Set environment variables GMAIL_USER and GMAIL_APP_PASSWORD before running.
    Request body: {"to_email": ..., "subject": ..., "message": ...}
    """
    import os
    sender_email = os.environ.get("GMAIL_USER")
    app_password = os.environ.get("GMAIL_APP_PASSWORD")
    orig_subject = req.subject
    orig_body = req.message

    if not sender_email or not app_password:
        return {"error": "GMAIL_USER and GMAIL_APP_PASSWORD environment variables must be set."}

    # If to_email is not provided, use Gemini to determine the best authority
    receiver_email = req.to_email
    ai_reason = None
    if not receiver_email:
        try:
            from google import genai
            client = genai.Client()
            prompt = (
                f"Given the following email subject and body, suggest the best authority email to send this to. "
                f"send to : ['akashuhulekal@gmail.com'] "
                f"\nSubject: {orig_subject}\nBody: {orig_body}\n"
                f"Return ONLY a JSON object: {{'to_email': ...}}."
            )
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt]
            )
            import json as _json
            text = response.text.strip().replace("'", '"')
            ai_result = _json.loads(text)
            receiver_email = ai_result.get("to_email")
            ai_reason = "Determined by Gemini based on subject and message."
        except Exception as e:
            return {"error": f"Could not determine authority email: {str(e)}"}

    # Use Gemini to rewrite the subject and body for clarity and professionalism
    try:
        from google import genai
        client = genai.Client()
        prompt = (
            f"Rewrite the following email subject and body to be clear, concise, and professional for a civic authority. "
            f"\nSubject: {orig_subject}\nBody: {orig_body}\n"
            f"Return ONLY a JSON object: {{'subject': ..., 'body': ...}}."
        )
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt]
        )
        import json as _json
        text = response.text.strip().replace("'", '"')
        improved = _json.loads(text)
        subject = improved.get("subject", orig_subject)
        body = improved.get("body", orig_body)
    except Exception as e:
        # If Gemini fails, fall back to original
        subject = orig_subject
        body = orig_body

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, app_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        return {"success": True, "sent_to": receiver_email, "subject": subject, "body": body, "ai_reason": ai_reason}
    except Exception as e:
        return {"error": str(e)}






