from ai_helpers.process_and_check_dup import process_incident  # Adjust to actual filename
import datetime

incident = {
    "id": "HkHRho483dm5OoUl7tct",
    "image_url": "https://media.assettype.com/deccanherald%2Fimport%2Fsites%2Fdh%2Ffiles%2Fgallery_images%2F2021%2F07%2F26%2FBengaluru%20Rains%20(4).jpg",
    "timestamp": "2025-03-10T106:12:03.888721+00:00",
    "zipcode": "560050",
    "geo": {
      "latitude": 12.9308,
      "longitude": 77.5839
    },
    "severity": "High",
    "location": {
      "lat": 12.9308,
      "lng": 77.5839
    },
    "area": "Jayanagara",
    "mood": 0,
    "category": "Power Cut",
    "summary": "kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk",
    "flood_level": "waist_deep",
    "road_passable": "impassable",
    "distance": 0,
    "title": "poer cut in Jayanagar - 1 Report"
  }
result = process_incident(incident)
print(result)



