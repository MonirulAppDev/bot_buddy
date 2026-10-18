import random
import re

SPINTAX_PATTERN = re.compile(r"\{([^{}]+)\}")

DEFAULT_TEMPLATES = [
    "{Awesome|Great|Amazing|Superb|Fantastic} {post|content|video|work}! {Keep it up|Loved it|Really good} {🔥|👏|❤️|👍}",
    "This is {so helpful|really inspiring|super interesting}! {Thanks for sharing|Appreciate this} {✨|🙌|💯}",
    "{Nice|Good|Valuable} perspective! {Agree with this|Well said|Totally agree} {👌|🌟}",
    "Love the {energy|quality|effort} here! {Keep inspiring|Can't wait for the next one} {🚀|😍|🔥}",
    "{Interesting|Very informative|Such a great point}! {Bookmarked|Saved this} {📌|💡}"
]


def parse_spintax(text: str) -> str:
    """Recursively resolve nested spintax patterns like {choice1|choice2|choice3}."""
    while True:
        match = SPINTAX_PATTERN.search(text)
        if not match:
            break
        options = match.group(1).split("|")
        replacement = random.choice(options)
        text = text[:match.start()] + replacement + text[match.end():]
    return text.strip()


def get_comment_for_post(raw_input: str | None = None) -> str:
    """Generate a realistic comment. If user provided custom comments or spintax, pick/parse from it;
    otherwise, pick from realistic default templates.
    """
    if raw_input and raw_input.strip():
        # User might provide multiple lines of comments or a single spintax line
        lines = [line.strip() for line in raw_input.strip().splitlines() if line.strip()]
        selected_line = random.choice(lines)
        return parse_spintax(selected_line)
    
    # Pick a random template and resolve spintax
    template = random.choice(DEFAULT_TEMPLATES)
    return parse_spintax(template)
