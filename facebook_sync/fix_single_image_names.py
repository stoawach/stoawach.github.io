import os
import re

# Correct paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
POSTS_FOLDER = os.path.join(BASE_DIR, "../_posts")
IMAGES_FOLDER = os.path.join(BASE_DIR, "../images/posts")


def process_md_files():
    """
    Processes markdown files in _posts/ and renames single images if exactly one is found.
    """
    for filename in os.listdir(POSTS_FOLDER):
        if not filename.endswith(".md"):
            continue

        post_path = os.path.join(POSTS_FOLDER, filename)

        with open(post_path, "r", encoding="utf-8") as file:
            content = file.read()

        # Find all image links e.g., ![alt text](/images/posts/filename.jpg)
        images = re.findall(r"\!\[.*?\]\(/images/posts/([^\)]+\.jpg)\)", content)

        # Only if exactly one image found
        if len(images) == 1:
            old_image = images[0]
            md_base = os.path.splitext(filename)[0]  # Filename without .md
            new_image = f"{md_base}.jpg"

            old_image_path = os.path.join(IMAGES_FOLDER, old_image)
            new_image_path = os.path.join(IMAGES_FOLDER, new_image)

            # Rename image file if it exists
            if os.path.exists(old_image_path):
                os.rename(old_image_path, new_image_path)
                print(f"Renamed image {old_image} → {new_image}")

                # Update markdown file content
                new_content = content.replace(old_image, new_image)

                with open(post_path, "w", encoding="utf-8") as file:
                    file.write(new_content)
            else:
                print(f"Image {old_image} not found for {filename}")


if __name__ == "__main__":
    process_md_files()
