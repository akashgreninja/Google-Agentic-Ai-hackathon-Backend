# AgenticAI City Events & Incident Backend

A FastAPI backend for real-time city event and incident reporting, predictive analysis, and intelligent notifications. Supports user registration, event reporting, AI-powered summaries, and agentic alerts for citizens and authorities.

---

## Features
- **User Registration & Login**: Register with name, email, interests, and password.
- **Incident/Event Reporting**: Report incidents (Flood, Fire, Concerts, Fairs, etc.) with location and image.
- **Relevant Incidents API**: Get incidents filtered by user interests and location.
- **Route-based Alerts**: Get actionable alerts for incidents along a travel route.
- **Predictive & Agentic Layer**: AI-powered endpoint summarizes and predicts risks for an area or route, providing clear, actionable advice.
- **Admin/Dev Utilities**: Populate users/events, update interests, and more.
- **CORS Enabled**: Open for frontend and external integrations.

---

## Business Logic
- Users can register and set their interests (e.g., Flood, Concerts, Pottery).
- Incidents are reported with category, summary, location, and image.
- Users can fetch incidents relevant to their interests and area.
- Predictive endpoints analyze event streams and generate AI-powered, actionable alerts (e.g., "Avoid HSR Layout because it is heavily flooded.").
- Route-based analysis helps users plan safe travel.
- All data is stored in Firebase Firestore; AI analysis uses Gemini.

---

## Running the Project

### 1. Local (Python)

1. **Clone the repo & enter directory:**
   ```bash
   git clone <repo-url>
   cd Mis-3-Backend
   ```
2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Set environment variables:**
   - Create a `.env` file with:
     ```
     GEMINI_API_KEY=your_gemini_api_key
     ```
5. **Run the server:**
   ```bash
   uvicorn main:app --reload
   ```
6. **(Optional) Expose with ngrok:**
   ```bash
   ngrok http 8000
   ```

---

### 2. Docker

1. **Build the Docker image:**
   ```bash
   docker build -t city-backend:latest .
   ```
2. **Run the container (with API key):**
   ```bash
   docker run -e GEMINI_API_KEY=your_gemini_api_key -p 8000:8000 city-backend:latest
   ```
3. **(Optional) Push to GCR:**
   ```bash
   ./build_and_push.sh <gcp-project-id> <gcr-region> <image-name>:<tag>
   ```

---

## API Endpoints (Key Examples)
- `POST /data/register` — Register a user
- `POST /data/login` — Login
- `POST /data/incident/report` — Report an incident/event
- `GET /data/get_relevant_incidents` — Get incidents for user/location
- `GET /data/agentic_predictive_layer` — Predictive, actionable summary for an area
- `GET /data/agentic_predictive_route` — Predictive, actionable summary for a route

See `routers/data_handler.py` for more endpoints and curl examples.

---

## Notes
- Requires Firebase credentials (`firebasekey.json`) in the project root.
- Ensure your Gemini API key is valid and has sufficient quota.
- For production, secure your API and do not store plain text passwords.

---

## License
MIT
