import os
import re

from utils.post_utils import generate_safe_filename  # Import function for generating safe filenames

# Correct paths based on your project structure
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Path to `facebook_sync/`
POSTS_FOLDER = os.path.join(BASE_DIR, "../_posts")  # Path to posts


def extract_metadata(content):
    """
    Extracts metadata (title, date) from a markdown file.
    """
    metadata = {}

    # Extract YAML Front Matter
    match = re.search(r"---\n(.*?)\n---", content, re.DOTALL)
    if match:
        yaml_content = match.group(1)
        title_match = re.search(r'title:\s*"(.*?)"', yaml_content)
        date_match = re.search(r"date:\s*(\d{4}-\d{2}-\d{2})", yaml_content)

        metadata["title"] = title_match.group(1) if title_match else None
        metadata["date"] = date_match.group(1) if date_match else None

    return metadata


def rename_md_files():
    """
    Iterates through all markdown posts in `_posts/` and renames them according to title and date.
    Ensures filenames are in lowercase.
    """
    for filename in os.listdir(POSTS_FOLDER):
        if not filename.endswith(".md"):
            continue  # Skip non-markdown files

        file_path = os.path.join(POSTS_FOLDER, filename)

        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

        metadata = extract_metadata(content)
        if not metadata["title"] or not metadata["date"]:
            print(f"Skipping {filename} (missing title or date)")
            continue

        # Generate the new filename based on title, ensuring lowercase
        safe_title = generate_safe_filename(metadata["title"])
        new_filename = f"{metadata['date']}-{safe_title}.md"
        new_file_path = os.path.join(POSTS_FOLDER, new_filename)

        if filename != new_filename:
            os.rename(file_path, new_file_path)
            print(f"Renamed {filename} → {new_filename}")


if __name__ == "__main__":
    rename_md_files()
