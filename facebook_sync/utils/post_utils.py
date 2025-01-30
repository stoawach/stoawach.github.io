import json
import os
import re
from collections import Counter
from datetime import datetime

from utils.file_utils import save_image
from utils.text_utils import add_non_breaking_spaces, extract_tags, filter_common_tags, format_links

OUTPUT_FOLDER = "../_posts"


def generate_safe_filename(title):
    """
    Generates a safe filename by replacing spaces with hyphens,
    removing unsupported characters, and replacing Polish characters with their Latin equivalents.
    Ensures the truncated title consists of whole words.
    """
    # Replace Polish characters with their Latin equivalents
    translation_table = str.maketrans("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ", "acelnoszzACELNOSZZ")
    sanitized_title = title.translate(translation_table)

    # Replace spaces with hyphens and remove unsupported characters
    sanitized_title = re.sub(r"[^a-zA-Z0-9 -]", "", sanitized_title).replace(" ", "-")

    # Truncate to the nearest whole word within 50 characters
    if len(sanitized_title) > 60:
        truncated = sanitized_title[:60].rsplit("-", 1)[0]  # Cut off at the last hyphen
    else:
        truncated = sanitized_title

    # Remove the last word if it's shorter than 3 characters and NOT purely numeric
    words = truncated.split("-")
    if words:
        last_word = words[-1]
        if len(last_word) < 3 and not last_word.isdigit():
            words.pop()

    return "-".join(words)


def find_related_posts(current_tags, current_post_id, all_existing_files, common_tags, current_content):
    """
    Finds posts with overlapping tags and similar content from both existing and new files.
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

    # Sort by shared words (descending)
    return sorted(related_posts, key=lambda x: (-x[1]))


def save_post_as_markdown(post, all_existing_files, common_tags):
    post_id = post.get("id")
    message = post.get("message", "No content").strip()
    created_time = post.get("created_time")
    formatted_date = datetime.strptime(created_time, "%Y-%m-%dT%H:%M:%S%z").strftime("%Y-%m-%d")
    weight = -int(datetime.strptime(created_time, "%Y-%m-%dT%H:%M:%S%z").strftime("%Y%m%d"))

    # Determine the author based on the content of the post
    author = "Stowarzyszenie Wachniewskiej"  # Default author
    if "©MJP" in message:
        author = "Michał Jan Patyk"

    # Extract first line as title
    title = message.split("\n")[0]

    # Remove title and hashtags from message
    content = re.sub(r"#\w+", "", "\n".join(message.split("\n")[1:])).strip()

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
    file_base_name = f"{formatted_date}-{safe_title}"

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
                    related_title = title_match.group(1)
                    related_safe_title = related_file.replace(".md", "").split("-", 3)[-1]  # Use safe title
                    related_safe_title = re.sub(r"-+", "-", related_safe_title)  # Replace multiple hyphens with one
                    file.write(f"- [{related_title}](/posts/{related_safe_title})\n")

        # Add social sharing link
        sharing_links = (
            f"\n\n---\n\n"
            f"Udostępnij ten tekst na Facebooku:\n"
            f"[Udostępnij na Facebooku](https://www.facebook.com/sharer/sharer.php?u="
            f"https://stowarzyszeniewachniewskiej.pl/posts/{safe_title})\n"
        )
        file.write(sharing_links)

        # Add JSON-LD for SEO
        json_ld = {
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "headline": title,
            "datePublished": formatted_date,
            "dateModified": formatted_date,
            "author": {"@type": "Person" if author == "Michał Jan Patyk" else "Organization", "name": author},
            "publisher": {
                "@type": "Organization",
                "name": "Stowarzyszenie im. Aleksandry Wachniewskiej",
                "logo": {"@type": "ImageObject", "url": "https://stowarzyszeniewachniewskiej.pl/images/logo/logo.svg"},
            },
            "mainEntityOfPage": {
                "@type": "WebPage",
                "@id": f"https://stowarzyszeniewachniewskiej.pl/posts/{safe_title}",
            },
            "image": {
                "@type": "ImageObject",
                "url": f"https://stowarzyszeniewachniewskiej.pl/{image_path.lstrip('../')}" if image_path else None,
            },
            "articleSection": "Dziedzictwo Kulturowe i Zabytki",
            "keywords": ", ".join(tags),
            "wordCount": len(content.split()),
            "articleBody": content,
            "description": "Odkryj piękno Zwierzyńca i jego zabytki.",
        }

        if author == "Michał Jan Patyk":
            json_ld["copyrightHolder"] = {"@type": "Person", "name": "Michał Jan Patyk"}

        # JSON-LD Breadcrumbs

        breadcrumbs = {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://stowarzyszeniewachniewskiej.pl"},
                {
                    "@type": "ListItem",
                    "position": 2,
                    "name": "posts",
                    "item": "https://stowarzyszeniewachniewskiej.pl/posts",
                },
                {
                    "@type": "ListItem",
                    "position": 3,
                    "name": title,
                    "item": f"https://stowarzyszeniewachniewskiej.pl/posts/{safe_title}",
                },
            ],
        }

        file.write('\n<script type="application/ld+json">\n')
        file.write(json.dumps(json_ld, ensure_ascii=False, indent=2))
        file.write("\n</script>\n")

        file.write('<script type="application/ld+json">\n')
        file.write(json.dumps(breadcrumbs, ensure_ascii=False, indent=2))
        file.write("\n</script>\n")

    print(f"Post saved as: {file_name}")
