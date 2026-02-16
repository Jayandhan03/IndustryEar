import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("SERP_API_KEY")  


def fetch_news(query: str, location: str = "India"):
    if not API_KEY:
        print("❌ ERROR: SERP_API_KEY not set in .env")
        sys.exit(1)

    url = "https://www.searchapi.io/api/v1/search"

    params = {
        "engine": "google_news",
        "q": query,
        "location": location,
        "api_key": API_KEY
    }

    try:
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        print("❌ Network / API error:", e)
        sys.exit(1)


def extract_news(data: dict):
    """
    SearchAPI may return news in different keys.
    We handle all known cases.
    """

    if "news_results" in data and data["news_results"]:
        return data["news_results"]

    if "organic_results" in data and data["organic_results"]:
        return data["organic_results"]

    # DEBUG: print available keys once
    print("⚠️ No news arrays found.")
    print("🔍 Available response keys:", list(data.keys()))
    return []


def print_news(news_results: list):
    if not news_results:
        print("⚠️ No news found after extraction.")
        return

    for idx, item in enumerate(news_results, start=1):
        title = item.get("title", "N/A")
        source = item.get("source", item.get("publisher", "N/A"))
        published = item.get("date", item.get("published_date", "N/A"))
        snippet = item.get("snippet", item.get("description", "N/A"))
        link = item.get("link", item.get("url", "N/A"))

        print(f"\n📰 News {idx}")
        print("-" * 70)
        print(f"Title     : {title}")
        print(f"Source    : {source}")
        print(f"Published : {published}")
        print(f"Summary   : {snippet}")
        print(f"Link      : {link}")


def main():
    query = "AI solopreneur who reached multimillionaire"
    location = "India"

    data = fetch_news(query, location)
    news_results = extract_news(data)
    print_news(news_results)


if __name__ == "__main__":
    main()
