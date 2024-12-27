import requests
import os
import json
import re
from datetime import datetime, timedelta

# Load secrets from secrets.json
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

# Load secrets
secrets = load_secrets()
ACCESS_TOKEN = secrets.get("facebook_token")
PROFILE_ID = secrets.get("profile_id")  # Example: "123456789012345"

if not ACCESS_TOKEN or not PROFILE_ID:
    print("Error: Missing access token or profile ID in secrets.json.")
    exit(1)

GRAPH_API_URL = "https://graph.facebook.com/v17.0"
OUTPUT_FOLDER = "_services"  # Folder for Markdown files
IMAGES_FOLDER = "images/posts"  # Folder for images

# Fetch posts from profile
def fetch_posts_from_profile():
    today = datetime.now()
    last_week_start = (today - timedelta(days=today.weekday() + 14)).date()
    last_week_end = (today - timedelta(days=today.weekday() + 1)).date()

    since_timestamp = int(last_week_start.strftime("%s"))
    until_timestamp = int(last_week_end.strftime("%s"))

    url = (f"{GRAPH_API_URL}/{PROFILE_ID}/posts?"
           f"fields=id,message,created_time,attachments&"
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

# Generate a safe filename
def generate_safe_filename(title):
    return re.sub(r"[^a-zA-Z0-9_-]", "", title.replace(" ", "_"))[:50]

# Add non-breaking spaces
def add_non_breaking_spaces(text):
    """
    Replaces spaces with non-breaking spaces after:
    - Short words (1-3 characters),
    - Words ending with a period (e.g., pw., św.).
    Excludes hashtags (#hashtag).
    """
    non_breaking_space = "\u00A0"

    # Handle short words (1-3 characters), excluding hashtags
    text = re.sub(
        r"(?<!#)(\b\w{1,3}\b) ",  # Short words not preceded by #
        lambda match: match.group(1) + non_breaking_space,
        text
    )

    # Handle words ending with a period, excluding hashtags
    text = re.sub(
        r"(?<!#)(\b[\w'’\"]+\.\b) ",  # Words ending with ".", not preceded by #
        lambda match: match.group(1) + non_breaking_space,
        text
    )

    return text

# Save image
def save_image(image_url, file_base_name):
    os.makedirs(IMAGES_FOLDER, exist_ok=True)
    image_name = f"{file_base_name}.jpg"
    image_path = os.path.join(IMAGES_FOLDER, image_name)

    try:
        response = requests.get(image_url, stream=True)
        if response.status_code == 200:
            with open(image_path, "wb") as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            print(f"Image saved: {image_path}")
        else:
            print(f"Failed to fetch image: {image_url}")
    except Exception as e:
        print(f"Error fetching image: {e}")
    return image_path

# Save post as Markdown
def save_post_as_markdown(post):
    post_id = post.get("id")
    message = post.get("message", "No content").strip()
    created_time = post.get("created_time")
    formatted_date = datetime.strptime(created_time, "%Y-%m-%dT%H:%M:%S%z").strftime("%Y-%m-%d")
    weight = -int(datetime.strptime(created_time, "%Y-%m-%dT%H:%M:%S%z").strftime("%Y%m%d"))

    # Extract first line as title
    title = message.split("\n")[0]

    # Remove title from message
    content = "\n".join(message.split("\n")[1:]).strip()

    # Add non-breaking spaces to content
    content = add_non_breaking_spaces(content)

    # Format links in the content
    content = format_links(content)

    # Extract tags from the message
    tags = extract_tags(message)

    # Generate base name for files
    safe_title = generate_safe_filename(title)
    file_base_name = f"{formatted_date}_{safe_title}"

    # Handle attachments
    image_path = None
    image_markdown = ""
    attachments = post.get("attachments", {}).get("data", [])
    for attachment in attachments:
        if "media" in attachment and "image" in attachment["media"]:
            image_url = attachment["media"]["image"]["src"]
            image_path = save_image(image_url, file_base_name)
            image_markdown = f"![{title}](/{image_path})\n*{title}*\n\n"

    # Create Markdown file
    file_name = f"{OUTPUT_FOLDER}/{file_base_name}.md"
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    # Write metadata to file
    with open(file_name, "w", encoding="utf-8") as file:
        file.write(f"---\n")
        file.write(f"title: \"{title}\"\n")
        file.write(f"date: {formatted_date}\n")
        file.write(f"weight: {weight}\n")
        file.write(f"post_id: {post_id}\n")
        file.write(f"tags: [{tags}]\n")
        if image_path:
            file.write(f"featured_image: /{image_path}\n")
        location = post.get("place", {}).get("name", "Unknown Location")
        file.write(f"location: \"{location}\"\n")
        file.write(f"---\n\n")
        if image_markdown:
            file.write(image_markdown)
        file.write(content)

        # Add social sharing links
        sharing_links = (
            "\n\n---\n\n"
            "Share this post:\n"
            "- [Facebook](https://www.facebook.com/sharer/sharer.php?u={file_base_name}.html)\n"
            "- [Twitter](https://twitter.com/intent/tweet?text={title}&url={file_base_name}.html)\n"
        )
        file.write(sharing_links)

    print(f"Post saved as: {file_name}")


# Main function
def main():
    posts = fetch_posts_from_profile()
    if not posts:
        print("No new posts found.")
        return

    for post in posts:
        save_post_as_markdown(post)

if __name__ == "__main__":
    main()
