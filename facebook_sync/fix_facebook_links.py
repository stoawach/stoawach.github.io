import os
import re

from utils.post_utils import generate_safe_filename

POSTS_FOLDER = "../_posts"
SITE_URL = "https://stowarzyszeniewachniewskiej.pl"


def update_facebook_share_links():
    for filename in os.listdir(POSTS_FOLDER):
        if not filename.endswith(".md"):
            continue

        file_path = os.path.join(POSTS_FOLDER, filename)
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

        # Extract title from front matter
        title_match = re.search(r'title:\s*"(.*?)"', content)
        if not title_match:
            print(f"No title found in {filename}, skipping.")
            continue
        title = title_match.group(1)
        safe_title = generate_safe_filename(title).lower()

        # Build correct URL
        correct_url = f"{SITE_URL}/posts/{safe_title}"
        correct_facebook_block = (
            f"---\n\n"
            f"Udostępnij ten tekst na Facebooku:\n"
            f"[Udostępnij na Facebooku](https://www.facebook.com/sharer/sharer.php?u={correct_url})\n"
        )

        # Replace old block (--- + Udostępnij... + link)
        content_updated = re.sub(
            r"---\n+Udostępnij ten tekst na Facebooku:.*?(?=\n<script|\Z)",
            correct_facebook_block,
            content,
            flags=re.DOTALL,
        )

        with open(file_path, "w", encoding="utf-8") as file:
            file.write(content_updated)

        print(f"Updated Facebook link in: {filename}")


if __name__ == "__main__":
    update_facebook_share_links()
