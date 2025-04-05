import os
import re
from collections import Counter

from utils.post_utils import generate_safe_filename

POSTS_FOLDER = "../_posts"


def extract_metadata(content):
    """
    Extracts metadata (title, tags, and content) from a markdown file.
    """
    metadata = {}
    match = re.search(r"---\n(.*?)\n---", content, re.DOTALL)
    if match:
        yaml_content = match.group(1)
        title_match = re.search(r'title:\s*"(.*?)"', yaml_content)
        tags_match = re.search(r"tags:\s*\[(.*?)\]", yaml_content)

        metadata["title"] = title_match.group(1) if title_match else "Untitled"
        metadata["tags"] = tags_match.group(1).split(", ") if tags_match else []

    # Extract post content after metadata block
    post_content = content.split("---", 2)[-1].strip()
    metadata["content"] = post_content

    return metadata


def find_related_posts(current_title, current_tags, current_content, all_posts):
    """
    Finds related posts based on common tags and similar content.
    """
    related_posts = []
    current_words = Counter(re.sub(r"[^\w\s]", "", current_content.lower()).split())

    for filename, data in all_posts.items():
        if data["title"] == current_title:
            continue  # Skip self

        # Compare tags
        common_tags = set(current_tags) & set(data["tags"])
        if common_tags:
            # Compare content similarity
            other_words = Counter(re.sub(r"[^\w\s]", "", data["content"].lower()).split())
            shared_words = sum((current_words & other_words).values())
            related_posts.append((filename, data["title"], shared_words))

    # Sort by similarity (descending) and limit to 5
    related_posts = sorted(related_posts, key=lambda x: -x[2])[:5]
    return related_posts


def update_related_posts():
    """
    Reads all markdown posts, finds related posts, and updates markdown files.
    """
    all_posts = {}

    # Load all posts into memory
    for filename in os.listdir(POSTS_FOLDER):
        if filename.endswith(".md"):
            with open(os.path.join(POSTS_FOLDER, filename), "r", encoding="utf-8") as file:
                content = file.read()
                metadata = extract_metadata(content)
                all_posts[filename] = metadata

    # Process and update each post
    for filename, data in all_posts.items():
        related_posts = find_related_posts(data["title"], data["tags"], data["content"], all_posts)

        # Generate new related section
        new_related_section = "\n\nPowiązane posty:\n"
        for related_file, related_title, _ in related_posts:
            safe_title = generate_safe_filename(related_title).lower()
            new_related_section += f"- [{related_title}](/posts/{safe_title})\n"

        # Load original file
        file_path = os.path.join(POSTS_FOLDER, filename)
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

        # Replace or insert the related section
        if "Powiązane posty:" in content:
            content = re.sub(
                r"Powiązane posty:.*?(?=\n{2,}|---|\Z)", new_related_section.strip(), content, flags=re.DOTALL
            )
        else:
            # Insert related section before the last '---' line (typically before JSON-LD)
            matches = list(re.finditer(r"\n---\n", content))
            if matches:
                last_match = matches[-1]
                insert_index = last_match.start()
                content = (
                    content[:insert_index].rstrip()
                    + "\n\n"
                    + new_related_section.strip()
                    + "\n\n"
                    + content[insert_index:]
                )
            else:
                # Fallback: append to the end if no '---' found
                if not content.endswith("\n"):
                    content += "\n"
                content += new_related_section

        # Save updated file
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(content)

        print(f"Updated: {filename}")


if __name__ == "__main__":
    update_related_posts()
