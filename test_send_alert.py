from ai_helpers.gemini import GeminiCityAnalyzer

def test_send_location_based_alert():
    analyzer = GeminiCityAnalyzer()

    # Simulated incident data
    incident_data = {
        "category": "Accident",
        "summary": "A minor accident occurred.",
        "severity": "Medium",
        "location": {"lat": 12.9121, "lng": 77.6446},
        "timestamp": "2025-07-21T12:00:00Z",
    }

    # Area name for the incident
    area = "Test Area"

    # Call the function
    analyzer.send_location_based_alert(area, incident_data)

if __name__ == "__main__":
    test_send_location_based_alert()
