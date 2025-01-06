import re


def add_non_breaking_spaces(text):
    non_breaking_space = "\u00A0"

    # Add non-breaking space after short words (1-3 characters) not preceded by a hashtag
    text = re.sub(r"(?<!#)(\b\w{1,3}\b) (?=\S)", lambda match: match.group(1) + non_breaking_space, text)

    # Add non-breaking space after abbreviations
    text = re.sub(
        r"(?<!#)\b([a-ząćęłńóśźż]{1,3}\.|[a-ząćęłńóśźż]{1,3}\.[a-ząćęłńóśźż]{1,3}\.) (?=\S)",
        lambda match: match.group(1) + non_breaking_space,
        text,
    )

    # Add non-breaking space after initials followed by a name or hyphenated name
    text = re.sub(
        r"(?<!#)(\b[A-Z]\.|[A-Z]\.[A-Z]\.) (?=[A-Za-z])", lambda match: match.group(1) + non_breaking_space, text
    )

    return text


def format_links(text):
    return re.sub(r"(http[s]?://\S+)", r"[\1](\1)", text)


def extract_tags(message):
    hashtags = re.findall(r"#(\w+)", message)
    return ", ".join(hashtags) if hashtags else "general"


def filter_common_tags(tags, common_tags):
    return [tag for tag in tags if tag not in common_tags]
