import os
import requests
from dotenv import load_dotenv

load_dotenv()

def fetch_news(
    query: str,
    limit: int = 5,
    time_published: str = "anytime",
    country: str = "US",
    lang: str = "en"
):
    """
    Fetch news from RapidAPI Real-Time News Data API

    Args:
        query (str): Search topic (e.g., Football, AI, Tesla)
        limit (int): Number of articles
        time_published (str): anytime / past_hour / past_day / past_week
        country (str): Country code
        lang (str): Language

    Returns:
        dict: JSON response
    """
    api_key = os.getenv("RAPID_API_KEY")
    if not api_key:
        print("❌ Error: RAPID_API_KEY not found in environment variables.")
        return None

    url = "https://real-time-news-data.p.rapidapi.com/search"

    headers = {
        "x-rapidapi-host": "real-time-news-data.p.rapidapi.com",
        "x-rapidapi-key": api_key
    }

    params = {
        "query": query,
        "limit": str(limit),
        "time_published": time_published,
        "country": country,
        "lang": lang
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        print("❌ API Error:", e)
        return None

if __name__ == "__main__":
    test_news = fetch_news(query="Football", limit=3)
    if test_news:
        for article in test_news.get("data", []):
            print(f"Title: {article.get('title')}")
            print(f"Link: {article.get('link')}")
            print("-" * 30)
