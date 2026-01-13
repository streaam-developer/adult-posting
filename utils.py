import re
import base64

def parse_duration(iso_duration):
    """Parse ISO 8601 duration to HH:MM:SS format."""
    # Handle formats like P0DT0H1M10S or PT1M10S
    match = re.search(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', iso_duration)
    if match:
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    # If no match, try to extract from P0DT0H1M10S format
    match = re.search(r'P\d+DT(\d+)H(\d+)M(\d+)S', iso_duration)
    if match:
        hours = int(match.group(1))
        minutes = int(match.group(2))
        seconds = int(match.group(3))
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return iso_duration

def sanitize_filename(name):
    """Sanitize string for use as filename."""
    return re.sub(r'[<>:"/\\|?*]', '', name).strip()

async def encode(string):
    return base64.urlsafe_b64encode(string.encode()).decode()

def apply_replacements(text, replacements):
    """Apply case-insensitive word replacements to text. Returns modified text and if any replacement was made."""
    modified = False
    for old, new in replacements.items():
        # Use word boundaries to replace whole words
        pattern = r'\b' + re.escape(old) + r'\b'
        if re.search(pattern, text, re.IGNORECASE):
            text = re.sub(pattern, new, text, flags=re.IGNORECASE)
            modified = True
    return text, modified