# from firebase_admin import firestore, credentials
# from geopy.distance import geodesic
# from datetime import datetime
# import pytz
# import firebase_admin
# from ai_helpers.vertex_embed import embed_text_and_image

# if not firebase_admin._apps:
#     cred = credentials.Certificate("./firebasekey.json")
#     firebase_admin.initialize_app(cred)
# db = firestore.client()

# def fetch_all_incidents():
#     docs = db.collection("bangalore").document("incidents").collection("all").stream()
#     incidents = []
#     for doc in docs:
#         data = doc.to_dict()
#         data['id'] = doc.id
#         has_location = False
#         if data.get("lat") and data.get("lng"):
#             has_location = True
#         elif data.get("location") and isinstance(data["location"], dict):
#             if data["location"].get("lat") and data["location"].get("lng"):
#                 data["lat"] = data["location"]["lat"]
#                 data["lng"] = data["location"]["lng"]
#                 has_location = True
#         elif data.get("geo") and isinstance(data["geo"], dict):
#             if data["geo"].get("latitude") and data["geo"].get("longitude"):
#                 data["lat"] = data["geo"]["latitude"]
#                 data["lng"] = data["geo"]["longitude"]
#                 has_location = True
#         if has_location and data.get("timestamp") and data.get("summary"):
#             incidents.append(data)
#     print(f"[DEBUG] Fetched {len(incidents)} total incidents from database")
#     return incidents

# def compute_combined_embedding(summary: str, image_url: str):
#     try:
#         return embed_text_and_image(summary, image_url)
#     except Exception as e:
#         print(f"[ERROR] Failed to generate embedding: {e}")
#         return None

# def get_or_generate_embedding(incident_data):
#     if incident_data.get("embedding"):
#         print(f"[DEBUG] Using existing embedding for incident {incident_data.get('id', 'unknown')}")
#         return incident_data["embedding"]
#     summary = incident_data.get("summary", "")
#     image_url = incident_data.get("image_url", "")
#     if not summary or not image_url:
#         print(f"[DEBUG] Missing summary or image_url for incident {incident_data.get('id', 'unknown')}")
#         return None
#     print(f"[DEBUG] Generating new embedding for incident {incident_data.get('id', 'unknown')}")
#     embedding = compute_combined_embedding(summary, image_url)
#     if embedding and incident_data.get('id'):
#         try:
#             db.collection("bangalore").document("incidents").collection("all").document(incident_data['id']).update({
#                 "embedding": embedding.tolist() if hasattr(embedding, 'tolist') else embedding
#             })
#             print(f"[DEBUG] Saved embedding to database for incident {incident_data['id']}")
#         except Exception as e:
#             print(f"[DEBUG] Failed to save embedding: {e}")
#     return embedding

# def cosine_similarity(vec1, vec2):
#     import numpy as np
#     v1, v2 = np.array(vec1), np.array(vec2)
#     dot = np.dot(v1, v2)
#     norm1 = np.linalg.norm(v1)
#     norm2 = np.linalg.norm(v2)
#     return dot / (norm1 * norm2) if norm1 != 0 and norm2 != 0 else 0

# def time_difference_minutes(ts1: str, ts2: str):
#     try:
#         dt1 = datetime.fromisoformat(ts1.replace('+00:00', '+0000'))
#         dt2 = datetime.fromisoformat(ts2.replace('+00:00', '+0000'))
#         if dt1.tzinfo is None:
#             dt1 = pytz.UTC.localize(dt1)
#         if dt2.tzinfo is None:
#             dt2 = pytz.UTC.localize(dt2)
#         return abs((dt1 - dt2).total_seconds()) / 60.0
#     except Exception as e:
#         print(f"[ERROR] Failed to parse timestamps: {e}")
#         return float('inf')

# def is_duplicate_incident(new_incident: dict) -> bool:
#     print(f"[DEBUG] Starting duplicate check for incident")
#     required_fields = ["summary", "image_url", "location", "timestamp"]
#     for field in required_fields:
#         if field not in new_incident:
#             print(f"[ERROR] Missing required field: {field}")
#             return False
#     location = new_incident["location"]
#     if not ("lat" in location and "lng" in location):
#         print(f"[ERROR] Invalid location format: {location}")
#         return False
#     new_location = (location["lat"], location["lng"])
#     all_incidents = fetch_all_incidents()
#     if not all_incidents:
#         print("[DEBUG] No incidents to compare")
#         return False
#     new_embedding = compute_combined_embedding(new_incident["summary"], new_incident["image_url"])
#     if new_embedding is None:
#         print("[ERROR] Failed to get new embedding")
#         return False
#     new_time = new_incident["timestamp"]
#     SIMILARITY_THRESHOLD = 0.50
#     DISTANCE_THRESHOLD = 1.0
#     TIME_THRESHOLD = 240
#     for incident in all_incidents:
#         existing_embedding = get_or_generate_embedding(incident)
#         if existing_embedding is None:
#             continue
#         existing_location = (incident["lat"], incident["lng"])
#         existing_time = incident["timestamp"]
#         try:
#             similarity = cosine_similarity(new_embedding, existing_embedding)
#             distance = geodesic(new_location, existing_location).km
#             time_diff = time_difference_minutes(new_time, existing_time)
#         except Exception as e:
#             print(f"[ERROR] Metric calc failed: {e}")
#             continue
#         print(f"[DEBUG] Similarity: {similarity:.4f}, Distance: {distance:.2f}km, Time: {time_diff:.1f}min")
#         if similarity > SIMILARITY_THRESHOLD and distance < DISTANCE_THRESHOLD and time_diff < TIME_THRESHOLD:
#             print(f"✅ DUPLICATE with incident ID {incident.get('id', 'unknown')}")
#             return True
#     print("[RESULT] ❌ No duplicates found")
#     return False
