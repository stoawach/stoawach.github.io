import requests
import json
from datetime import datetime, timedelta

def load_secrets(file_path="secrets.json"):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
        return {}
    except json.JSONDecodeError:
        print("Error: Invalid JSON in secrets.json.")
        return {}

def fetch_posts_from_profile():
    secrets = load_secrets()
    ACCESS_TOKEN = secrets.get("facebook_token")
    PROFILE_ID = secrets.get("profile_id")  # Example: "123456789012345"

    if not ACCESS_TOKEN or not PROFILE_ID:
        print("Error: Missing access token or profile ID in secrets.json.")
        exit(1)

    GRAPH_API_URL = "https://graph.facebook.com/v17.0"
    today = datetime.now()
    last_week_start = (today - timedelta(days=today.weekday() + 30)).date()
    last_week_end = (today - timedelta(days=today.weekday() + 1)).date()

    since_timestamp = int(last_week_start.strftime("%s"))
    until_timestamp = int(last_week_end.strftime("%s"))

    url = (f"{GRAPH_API_URL}/{PROFILE_ID}/posts?"
           f"fields=id,message,created_time,attachments,place&"
           f"since={since_timestamp}&until={until_timestamp}&access_token={ACCESS_TOKEN}")

    print(f"Pobieranie postów z profilu od {last_week_start} do {last_week_end}...")
    response = requests.get(url)
    print(f"Debug: API response: {response.json()}")  # Debug response

    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        return []

    data = response.json()
    return data.get('data', [])
