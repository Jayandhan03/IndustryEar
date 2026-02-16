import requests



url = "https://www.searchapi.io/api/v1/search"
params = {
  "engine": "google_news",
  "q": "Jeff Bezos news",
  "location": "New York,United States"
}

response = requests.get(url, params=params)
print(response.text)
