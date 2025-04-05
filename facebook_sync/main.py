import os

from utils.facebook_api import fetch_posts_from_profile
from utils.post_utils import save_post_as_markdown

OUTPUT_FOLDER = "../_posts"


def main():
    common_tags = [
        "general",
        "wydarzenia",
        "ogłoszenia",
    ]  # Define common tags to exclude
    all_posts = fetch_posts_from_profile()  # Fetch all posts
    if not all_posts:
        print("No new posts found.")
        return

    # List existing Markdown files in _posts folder
    all_existing_files = [f for f in os.listdir(OUTPUT_FOLDER) if f.endswith(".md")]

    for post in all_posts:
        save_post_as_markdown(post, all_existing_files, common_tags)


if __name__ == "__main__":
    main()
