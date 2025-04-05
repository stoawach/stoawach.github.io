import json
import os
import re

from utils.post_utils import generate_safe_filename

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
POSTS_FOLDER = os.path.join(BASE_DIR, "../_posts")
SITE_URL = "https://stowarzyszeniewachniewskiej.pl"
ORGANIZATION_NAME = "Stowarzyszenie im. Aleksandry Wachniewskiej"
ORGANIZATION_LOGO = f"{SITE_URL}/images/logo/logo.svg"


def extract_metadata(content):
    match = re.search(r"---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return {}

    yaml_block = match.group(1)

    def extract(key):
        m = re.search(rf"{key}:\s*(.*)", yaml_block)
        return m.group(1).strip('"') if m else None

    return {
        "title": extract("title"),
        "date": extract("date"),
        "description": extract("description"),
        "tags": extract("tags"),
        "author": "Michał Jan Patyk" if "©MJP" in content else ORGANIZATION_NAME,
        "image": extract("featured_image"),
    }


def extract_article_body(full_content):
    content = re.sub(r"^---.*?---\s*", "", full_content, flags=re.DOTALL)
    content = re.sub(r"<script type=\"application/ld\+json\">.*?</script>", "", content, flags=re.DOTALL)
    content = re.split(r"(?i)powiązane posty[:：]", content)[0]
    content = re.split(r"(?i)udostępnij ten tekst na facebooku", content)[0]
    content = re.sub(r"!\[.*?\]\(.*?\)\s*\*.*?\*\n*", "", content, count=1, flags=re.DOTALL)
    content = re.sub(r"^---$", "", content, flags=re.MULTILINE)
    return content.strip()


def generate_json_ld(meta, safe_title, article_body):
    word_count = len(article_body.split())

    blog_posting = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": meta["title"],
        "datePublished": meta["date"],
        "dateModified": meta["date"],
        "author": {
            "@type": "Person" if meta["author"] == "Michał Jan Patyk" else "Organization",
            "name": meta["author"],
        },
        "publisher": {
            "@type": "Organization",
            "name": ORGANIZATION_NAME,
            "logo": {"@type": "ImageObject", "url": ORGANIZATION_LOGO},
        },
        "mainEntityOfPage": {"@type": "WebPage", "@id": f"{SITE_URL}/posts/{safe_title}"},
        "image": (
            {"@type": "ImageObject", "url": f"{SITE_URL}{meta['image'].replace('..', '')}"} if meta["image"] else None
        ),
        "articleSection": "Dziedzictwo Kulturowe i Zabytki",
        "keywords": meta["tags"],
        "wordCount": word_count,
        "articleBody": article_body,
        "description": meta["description"] or "Odkryj piękno Zwierzyńca i jego zabytki.",
        "copyrightHolder": (
            {"@type": "Person", "name": "Michał Jan Patyk"} if meta["author"] == "Michał Jan Patyk" else None
        ),
    }

    breadcrumb = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE_URL}"},
            {"@type": "ListItem", "position": 2, "name": "posts", "item": f"{SITE_URL}/posts"},
            {"@type": "ListItem", "position": 3, "name": meta["title"], "item": f"{SITE_URL}/posts/{safe_title}"},
        ],
    }

    return blog_posting, breadcrumb


def update_jsonld_in_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    meta = extract_metadata(content)
    if not meta["title"] or not meta["date"]:
        print(f"Skipping {file_path} (missing metadata)")
        return

    safe_title = generate_safe_filename(meta["title"]).lower()
    article_body = extract_article_body(content)

    blog_posting, breadcrumb = generate_json_ld(meta, safe_title, article_body)
    json_ld_block = f'<script type="application/ld+json">\n{json.dumps(blog_posting, ensure_ascii=False, indent=2)}\n</script>\n<script type="application/ld+json">\n{json.dumps(breadcrumb, ensure_ascii=False, indent=2)}\n</script>'  # noqa: E501

    content = re.sub(r'<script type="application/ld\+json">.*?</script>', "", content, flags=re.DOTALL)
    content = content.strip() + "\n\n" + json_ld_block + "\n"

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Updated JSON-LD in {file_path}")


if __name__ == "__main__":
    for md_file in os.listdir(POSTS_FOLDER):
        if md_file.endswith(".md"):
            update_jsonld_in_file(os.path.join(POSTS_FOLDER, md_file))
