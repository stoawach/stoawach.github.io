import json
import os
import re
from collections import Counter
from datetime import datetime

from utils.file_utils import save_image
from utils.text_utils import add_non_breaking_spaces, extract_tags, filter_common_tags, format_links

OUTPUT_FOLDER = "../_services"


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
            image_markdown = f"![{title}](/{image_path.lstrip('../')})\n*{title}*\n\n"

    # Create Markdown file
    file_name = f"{OUTPUT_FOLDER}/{file_base_name}.md"
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    # Write metadata to file
    with open(file_name, "w", encoding="utf-8") as file:
        file.write("---\n")
        file.write(f'title: "{title}"\n')
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
        file.write(f'location: "{location_name}"\n')
        if location_lat and location_lon:
            file.write(f"latitude: {location_lat}\n")
            file.write(f"longitude: {location_lon}\n")
        meta_description = " ".join(content.split("\n")[:2]).strip()[:150] + "..."
        file.write(f'description: "{meta_description}"\n')

        file.write("---\n\n")

        # Add H1 title
        file.write(f"# {title}\n\n")

        # Add image if exists
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
                    title_match = re.search(r"title: \"(.*?)\"", related_content)
                    if not title_match:
                        continue
                    related_title = (
                        (title_match.group(1)[:70] + "...") if len(title_match.group(1)) > 70 else title_match.group(1)
                    )
                    file.write(f"- [{related_title}](/services/{related_file.replace('.md', '')})\n")

        # Add social sharing link
        sharing_links = (
            f"\n\n---\n\n"
            f"Udostępnij ten tekst na Facebooku:\n"
            f"[Udostępnij na Facebooku](https://www.facebook.com/sharer/sharer.php?u="
            f"https://stowarzyszeniewachniewskiej.pl/services/{file_base_name})\n"
        )
        file.write(sharing_links)

        # Add JSON-LD for SEO
        json_ld = {
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "headline": title,
            "datePublished": formatted_date,
            "author": {"@type": "Organization", "name": "Stowarzyszenie Wachniewskiej"},
            "image": (f"https://stowarzyszeniewachniewskiej.pl/{image_path.lstrip('../')}" if image_path else ""),
            "articleBody": content,
        }

        file.write('\n<script type="application/ld+json">\n')
        file.write(json.dumps(json_ld, ensure_ascii=False, indent=2))
        file.write("\n</script>\n")

    print(f"Post saved as: {file_name}")
