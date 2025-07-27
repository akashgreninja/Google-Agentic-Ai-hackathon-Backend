from ai_helpers.gemini import GeminiCityAnalyzer

if __name__ == "__main__":
    analyzer = GeminiCityAnalyzer()
    video_url = "https://firebasestorage.googleapis.com/v0/b/sankalpa-b7b13.appspot.com/o/photos%2FSampleVideo_1280x720_1mb.mp4?alt=media&token=8d3b4363-8c3e-4f38-ac5a-8d05b330cd98"
    lat = 12.9716
    lng = 77.5946
    area = "MG Road"
    result = analyzer.analyze_incident(video_url, lat, lng, area)
    print(result)
