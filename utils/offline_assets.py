import re

REMOTE_CSS_IMPORT = re.compile(
    r"@import\s+(?:url\(\s*['\"]?https?://[^)]*\)|['\"]https?://[^'\"]*['\"])\s*[^;]*;",
    re.IGNORECASE,
)


def local_stylesheet(source: str) -> str:
    return REMOTE_CSS_IMPORT.sub("", source)
