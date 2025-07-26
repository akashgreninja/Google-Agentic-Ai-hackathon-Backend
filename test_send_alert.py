from ai_helpers.gemini import GeminiCityAnalyzer

def test_send_location_based_alert():
    analyzer = GeminiCityAnalyzer()

    # Simulated incident data
    incident_data = {
        "category": "Accident",
        "summary": "A big tree has fallen on the road causing a blockage.",
        "severity": "Medium",
        "location": {"lat": 12.9728512, "lng": 77.6011776},
        "timestamp": "2025-07-21T12:00:00Z",
        "body": "A big tree has fallen on the road causing a blockage. Please avoid the area. ",
    }

    # Area name for the incident
    area = "Test Area"

    # Call the function
    analyzer.send_location_based_alert(area, incident_data)

if __name__ == "__main__":
    test_send_location_based_alert()
