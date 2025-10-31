import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_api_key(st_secrets: Optional[dict] = None) -> str:
    """Return the YouTube API key from Streamlit secrets or environment."""
    try:
        if st_secrets and "YOUTUBE_API_KEY" in st_secrets:
            return st_secrets["YOUTUBE_API_KEY"]
    except Exception:
        pass
    key = os.getenv("YOUTUBE_API_KEY")
    if not key:
        raise RuntimeError("YOUTUBE_API_KEY not set. Add it to .env or Streamlit secrets.")
    return key

def get_region(default: str = "CA") -> str:
    """Return uppercase ISO-3166-1 alpha-2 region, sanitized; default CA."""
    raw = os.getenv("REGION") or default
    # keep only letters, take first two
    letters = "".join(ch for ch in raw if ch.isalpha()).upper()
    if len(letters) >= 2:
        return letters[:2]
    return default

def _get_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default

def get_max_comments(default: int = 200) -> int:
    """Max comments per video."""
    return _get_int("MAX_COMMENTS", default)

def get_cache_ttl(default: int = 300) -> int:
    """Cache TTL in seconds; supports CACHE_TTL or CACHE_TTL_SECONDS env names."""
    if os.getenv("CACHE_TTL"):
        return _get_int("CACHE_TTL", default)
    return _get_int("CACHE_TTL_SECONDS", default)
