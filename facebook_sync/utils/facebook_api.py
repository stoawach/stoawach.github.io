import json
from datetime import datetime, timedelta

import requests


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
    last_week_start = (today - timedelta(days=today.weekday() + 1300)).date()
    last_week_end = (today - timedelta(days=today.weekday() + 1)).date()

    since_timestamp = int(last_week_start.strftime("%s"))
    until_timestamp = int(last_week_end.strftime("%s"))

    base_url = (
        f"{GRAPH_API_URL}/{PROFILE_ID}/posts?"
        f"fields=id,message,created_time,attachments,place&"
        f"since={since_timestamp}&until={until_timestamp}&"
        f"access_token={ACCESS_TOKEN}"
    )

    print(f"Fetching posts from {last_week_start} to {last_week_end}...")

    all_posts = []
    next_url = base_url

    while next_url:
        response = requests.get(next_url)
        # Debug info
        print(f"Debug: API response: {response.json() if response else 'No response'}")

        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            print(response.text)
            break  # Stop fetching if there's an error

        data = response.json()

        # Extract data
        posts_batch = data.get("data", [])
        # Filter out empty posts (those where 'message' is None or an empty string)
        filtered_posts = [p for p in posts_batch if p.get("message", "").strip() != ""]
        all_posts.extend(filtered_posts)

        # Check for next page
        paging = data.get("paging", {})
        next_url = paging.get("next")  # If there's a 'next' link, fetch more; otherwise, stop

    print(f"Total posts fetched: {len(all_posts)}")
    return all_posts
