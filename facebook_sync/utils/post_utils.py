from utils.file_utils import save_image
from utils.text_utils import add_non_breaking_spaces, format_links, extract_tags, filter_common_tags
import re
import os
from datetime import datetime

OUTPUT_FOLDER = "_services"


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
    safe_title = re.sub(r"[^a-zA-Z0-9_-]", "", title.replace(" ", "_")[:50])
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
