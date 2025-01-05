import requests
import os
import json
import re
from datetime import datetime, timedelta
from collections import Counter

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

# Generate a safe filename
def generate_safe_filename(title):
    translation_table = str.maketrans("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ", "acelnoszzACELNOSZZ")
    sanitized_title = title.translate(translation_table)
    return re.sub(r"[^a-zA-Z0-9_-]", "", sanitized_title.replace(" ", "_")[:50])

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

# Extract tags from hashtags
def extract_tags(message):
    """
    Extracts hashtags from the post content to use as tags.
    """
    hashtags = re.findall(r"#(\w+)", message)  # Find all hashtags
    return ", ".join(hashtags) if hashtags else "general"  # Default tag if none found

# Filter common tags
def filter_common_tags(tags, common_tags):
    """
    Removes common tags that appear frequently in posts.
    """
    return [tag for tag in tags if tag not in common_tags]

# Format links in Markdown
def format_links(text):
    """
    Converts plain URLs in the text into Markdown hyperlinks.
    """
    return re.sub(r"(http[s]?://\S+)", r"[\1](\1)", text)  # Convert URLs to Markdown links

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

# Find related posts based on tags and content similarity
def find_related_posts(current_tags, current_post_id, all_existing_files, common_tags, current_content):
    """
    Finds posts with overlapping tags and similar content from existing files.
    """
    related_posts = []
    current_words = Counter(re.sub(r"[^\w\s]", "", current_content.lower()).split())

    for file_name in all_existing_files:
        with open(os.path.join(OUTPUT_FOLDER, file_name), "r", encoding="utf-8") as file:
            content = file.read()
            # Extract tags and post_id from metadata
            tags_line = re.search(r"tags: \[(.*?)\]", content)
            post_id_line = re.search(r"post_id: (\d+)", content)
            if tags_line and post_id_line:
                tags = tags_line.group(1).split(", ")
                tags = filter_common_tags(tags, common_tags)
                post_id = post_id_line.group(1)

                # Skip self-references
                if post_id == current_post_id:
                    continue

                # Compare tags
                if any(tag in current_tags for tag in tags):
                    # Compare content similarity
                    other_words = Counter(re.sub(r"[^\w\s]", "", content.lower()).split())
                    shared_words = sum((current_words & other_words).values())
                    related_posts.append((file_name, shared_words))

    # Sort by shared words (descending) and then by filename (newest first)
    return sorted(related_posts, key=lambda x: (-x[1], x[0]))

# Save post as Markdown
def save_post_as_markdown(post, all_existing_files, common_tags):
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

    # Filter common tags
    tags = filter_common_tags(tags.split(", "), common_tags)

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
        file.write(f"tags: [{', '.join(tags)}]\n")
        if image_path:
            file.write(f"featured_image: /{image_path}\n")
        place = post.get("place", {})
        location_name = place.get("name", "Unknown Location")
        location_lat = place.get("location", {}).get("latitude", None)
        location_lon = place.get("location", {}).get("longitude", None)
        file.write(f"location: \"{location_name}\"\n")
        if location_lat and location_lon:
            file.write(f"latitude: {location_lat}\n")
            file.write(f"longitude: {location_lon}\n")
        file.write(f"---\n\n")
        if image_markdown:
            file.write(image_markdown)
        file.write(content)

        # Add related posts section
        current_tags = tags
        related_posts = find_related_posts(current_tags, post_id, all_existing_files, common_tags, content)
        if related_posts:
            file.write("\n\nPowiązane posty:\n")
            for related_file, _ in related_posts[:5]:  # Limit to 5 related posts
                with open(os.path.join(OUTPUT_FOLDER, related_file), "r", encoding="utf-8") as related_file_content:
                    related_content = related_file_content.read()
                    title_match = re.search(r'title: \"(.*?)\"', related_content)
                    if not title_match:
                        continue
                    related_title = title_match.group(1)
                    file.write(f"- [{related_title}](/services/{related_file.replace('.md', '')})\n")

        # Add social sharing link for Facebook
        sharing_links = (
            f"\n\n---\n\n"
            f"Udostępnij ten tekst na Facebooku:\n"
            f"[Udostępnij na Facebooku](https://www.facebook.com/sharer/sharer.php?u=https://stowarzyszeniewachniewskiej.pl/services/{file_base_name})\n"
        )
        file.write(sharing_links)

    print(f"Post saved as: {file_name}")

# Main function
def main():
    common_tags = ["general", "wydarzenia", "ogłoszenia"]  # Define common tags to exclude
    all_posts = fetch_posts_from_profile()  # Fetch all posts
    if not all_posts:
        print("No new posts found.")
        return

    # List existing Markdown files in _services folder
    all_existing_files = [f for f in os.listdir(OUTPUT_FOLDER) if f.endswith(".md")]

    for post in all_posts:
        save_post_as_markdown(post, all_existing_files, common_tags)

if __name__ == "__main__":
    main()
