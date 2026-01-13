import re

# Site-specific extractors
def extract_title_default(html):
    match = re.search(r'<meta itemprop="name\s*" content="([^"]*)"', html)
    return match.group(1) if match else "Unknown Title"

def extract_description_default(html):
    match = re.search(r'<meta itemprop="description" content="([^"]*)"', html)
    return match.group(1) if match else "No description"

def extract_duration_default(html):
    match = re.search(r'<meta itemprop="duration" content="([^"]*)"', html)
    return match.group(1) if match else "Unknown"

def extract_video_url_default(html):
    match = re.search(r"(https?://[^\s\"]+\.mp4)", html)
    video_url = match.group(1) if match else None
    print(f"Default extractor: video_url = {video_url}")
    return video_url

def extract_video_url_viralkand(html):
    match = re.search(r"(https?://[^\s\"]*viralkand\.com[^\s\"]*\.mp4)", html)
    video_url = match.group(1) if match else None
    print(f"Viralkand extractor: video_url = {video_url}")
    return video_url

def extract_upload_date_default(html):
    match = re.search(r'<meta itemprop="uploadDate" content="([^"]*)"', html)
    return match.group(1) if match else None

def extract_thumbnail_url_default(html):
    match = re.search(r'<meta itemprop="thumbnailUrl" content="([^"]*)"', html)
    return match.group(1) if match else None

SITE_EXTRACTORS = {
    'viralkand.com': {
        'extract_title': extract_title_default,
        'extract_description': extract_description_default,
        'extract_duration': extract_duration_default,
        'extract_video_url': extract_video_url_viralkand,
    },
    # Add more domains as needed
    'default': {
        'extract_title': extract_title_default,
        'extract_description': extract_description_default,
        'extract_duration': extract_duration_default,
        'extract_video_url': extract_video_url_default,
    }
}