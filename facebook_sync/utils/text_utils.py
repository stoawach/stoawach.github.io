import re

def add_non_breaking_spaces(text):
    non_breaking_space = "\u00A0"
    text = re.sub(r"(?<!#)(\b\w{1,3}\b) ", lambda match: match.group(1) + non_breaking_space, text)
    text = re.sub(r"(?<!#)(\b[\w'’\"]+\.\b) ", lambda match: match.group(1) + non_breaking_space, text)
    return text

def format_links(text):
    return re.sub(r"(http[s]?://\S+)", r"[\1](\1)", text)

def extract_tags(message):
    hashtags = re.findall(r"#(\w+)", message)
    return ", ".join(hashtags) if hashtags else "general"

def filter_common_tags(tags, common_tags):
    return [tag for tag in tags if tag not in common_tags]
