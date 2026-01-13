# Word replacements for description (case-insensitive)
REPLACEMENTS = {
    "hotel": "oyo",
    "Lund": "namoona",
    "chut": "cheew",
    "bhosdi": "bhenchod",
    "bhosdiwala": "bhenchodwala",
    "bhosdika": "bhenchodka",
    "nangi": "nangi",
}

ADMIN_ID = 6924888856  # Replace with your Telegram user ID

BOT_TOKEN = '8057742931:AAHBalJqr2HmTEVbL5kfbStGLTswfdpPVxg'
CHANNEL_ID = -1003198232571
FILE_STORE_CHANNEL = [-1003198232571]

# List of usernames for random selection
USERNAMES = ['boltarhegabot', 'dcsdfvavbdfbot']  # Add multiple usernames here

# Channels to forward the link message to
FORWARD_CHANNELS = [-1003533855257]  # Add channel IDs here, e.g., [-1001234567890]

# MongoDB configuration
MONGO_URI = 'mongodb+srv://sonukumarkrbbu60:lfkTvljnt25ehTt9@cluster0.2wrbftx.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'  # Replace with your MongoDB URI
DB_NAME = 'video_bot'
COLLECTION_NAME = 'processed_urls'

# Video editing setting
VIDEO_EDITING_ENABLED = True  # Set to False to disable video editing
VIDEO_ENCODING_PRESET = 'medium' # FFmpeg encoding preset (e.g., 'ultrafast', 'superfast', 'fast', 'medium', 'slow', 'slower', 'veryslow')

# --- Category Configuration ---
CATEGORIES = [
    "Nepali", "Indian", "Boudi", "Housewife", "Couple", "Public", "Leaked", "Masturbation",
    "Outdoor", "Amateur", "Hardcore", "Compilation", "Anal", "Blowjob", "Teen", "Mature"
]

CATEGORY_KEYWORDS = {
    "Nepali": ["nepali", "nepal"],
    "Indian": ["indian", "desi"],
    "Boudi": ["boudi", "bhabi"],
    "Housewife": ["housewife", "aunty"],
    "Couple": ["couple", "bfgf", "husbandwife"],
    "Public": ["public", "outdoor"],
    "Leaked": ["leaked", "mms"],
    "Masturbation": ["masturbation", "solo"],
    "Outdoor": ["outdoor", "garden", "beach"],
    "Amateur": ["amateur", "homemade"],
    "Hardcore": ["hardcore", "extreme"],
    "Compilation": ["compilation", "mix"],
    "Anal": ["anal", "butt"],
    "Blowjob": ["blowjob", "bj"],
    "Teen": ["teen", "young"],
    "Mature": ["mature", "milf", "aunty"]
}

# Website configuration
SITE_URL = "http://0.0.0.0:8000"  # Your website's base URL
POSTS_PER_PAGE = 30

# Interval for automated posting (in seconds)
POST_INTERVAL_MIN = 30
POST_INTERVAL_MAX = 40

# Number of concurrent downloads/uploads
CONCURRENT_TASKS = 1
