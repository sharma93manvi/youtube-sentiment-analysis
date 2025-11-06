import time
import re
from typing import List, Dict, Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Initialize YouTube API client
def get_youtube_client(api_key: str):
    """Create and return a YouTube Data API v3 service object.
    YouTube Data API v3 (Google Developers):
    https://developers.google.com/youtube/v3/docs"""
    return build("youtube", "v3", developerKey=api_key, cache_discovery=False)

def extract_video_id(url: str) -> Optional[str]:
    """Extract video ID from various YouTube URL formats.
    
    Supports:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    - https://m.youtube.com/watch?v=VIDEO_ID
    - VIDEO_ID (if already just an ID)
    
    Args:
        url: YouTube URL or video ID
        
    Returns:
        Video ID string or None if not found
    """
    if not url:
        return None
    
    # If it's already just an ID (11 characters, alphanumeric)
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url.strip()):
        return url.strip()
    
    # Pattern for standard YouTube URLs
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com\/watch\?.*v=([a-zA-Z0-9_-]{11})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None

def get_video_details(api_key: str, video_id: str, retries: int = 3) -> Optional[Dict]:
    """Get video details for a specific video ID.
    
    Args:
        api_key: YouTube API key
        video_id: YouTube video ID
        retries: Number of retry attempts for errors (default: 3)
    
    Returns:
        Video dictionary with: video_id, title, channel, 
        published_at, thumb_url, views, likes, comments
        Returns None if video not found or error occurs
    """
    youtube = get_youtube_client(api_key)
    
    params = {
        "part": "snippet,statistics",
        "id": video_id,
    }
    
    # Retry logic for 429 (Too Many Requests) and 5xx errors
    for attempt in range(retries):
        try:
            response = youtube.videos().list(**params).execute()
            items = response.get("items", [])
            
            if not items:
                return None
            
            item = items[0]
            stats = item.get("statistics", {}) or {}
            snippet = item.get("snippet", {}) or {}
            thumbs = (snippet.get("thumbnails", {}) or {}).get("default", {}) or {}
            
            return {
                "video_id": item.get("id"),
                "title": snippet.get("title"),
                "channel": snippet.get("channelTitle"),
                "published_at": snippet.get("publishedAt"),
                "thumb_url": thumbs.get("url"),
                "views": int(stats.get("viewCount", 0) or 0),
                "likes": int(stats.get("likeCount", 0) or 0),
                "comments": int(stats.get("commentCount", 0) or 0),
            }
            
        except HttpError as e:
            if e.resp.status in [429, 500, 502, 503, 504]:
                time.sleep(2 ** attempt)
                continue
            return None
        except Exception:
            return None
    
    return None

def get_trending_videos(
    api_key: str,
    region: str = "CA", 
    max_results: int = 10,
    retries: int = 3,
)-> List[Dict]:
    """Get the top trending videos for a given region.
    
    Args:
        api_key: YouTube API key
        region: ISO-3166-1 alpha-2 region code (default: CA)
        max_results: Maximum number of videos to fetch (default: 10)
        retries: Number of retry attempts for errors (default: 3)
    
    Returns:
        List of video dictionaries with: video_id, title, channel, 
        published_at, thumb_url, views, likes, comments
    
    Raises:
        HttpError: If API request fails after retries
    """
    youtube = get_youtube_client(api_key)

    # Parameters for the API request
    params = {
        "part": "snippet,statistics",
        "chart": "mostPopular",
        "regionCode": region,
        "maxResults": max_results,
    }

    # Retry logic for 429 (Too Many Requests) and 5xx errors
    for attempt in range(retries):
        try:
            response = youtube.videos().list(**params).execute()
            items = response.get("items", [])

            videos: List[Dict] = []
            for item in items:
                stats = item.get("statistics", {}) or {}
                snippet = item.get("snippet", {}) or {}
                thumbs = (snippet.get("thumbnails", {}) or {}).get("default", {}) or {}
                videos.append(
                    {
                        "video_id": item.get("id"),
                        "title": snippet.get("title"),
                        "channel": snippet.get("channelTitle"),
                        "published_at": snippet.get("publishedAt"),
                        "thumb_url": thumbs.get("url"),
                        "views": int(stats.get("viewCount", 0) or 0),
                        "likes": int(stats.get("likeCount", 0) or 0),
                        "comments": int(stats.get("commentCount", 0) or 0),
                    }
                )

            return videos

        except HttpError as e:
            if e.resp.status in [429, 500, 502, 503, 504]:
                time.sleep(2 ** attempt)
                continue
            raise
        except Exception:
            raise

def get_video_comments(
    api_key: str,
    video_id: str,
    max_results: int = 200,
    order: str = "time",
    retries: int = 3,
)-> List[Dict]:
    """Get the comments for a given video with pagination support.
    
    Fetches up to max_results comments, paginating through API pages.
    API returns max 100 per page, so we paginate to get more.
    """
    youtube = get_youtube_client(api_key)
    all_items = []
    page_token = None
    per_page = min(100, max_results)  # API max is 100 per page
    
    while len(all_items) < max_results:
        params = {
            "part": "snippet",
            "videoId": video_id,
            "maxResults": per_page,
            "order": order,
        }
        
        if page_token:
            params["pageToken"] = page_token
        
        # Retry logic for this page
        attempt = 0
        while attempt <= retries:
            try:
                response = youtube.commentThreads().list(**params).execute()
                break  # Success, exit retry loop
            except HttpError as e:
                attempt += 1
                if attempt > retries:
                    raise  # Re-raise if exhausted retries
                
                status_code = e.resp.status if hasattr(e, 'resp') else None
                if status_code == 429 or (status_code and 500 <= status_code < 600):
                    wait_time = 2 ** (attempt - 1)
                    time.sleep(wait_time)
                else:
                    raise  # Non-retryable error
            except Exception:
                raise
        
        # Add items from this page
        items = response.get("items", [])
        all_items.extend(items)
        
        # Check if we've reached our limit
        if len(all_items) >= max_results:
            return all_items[:max_results]
        
        # Check for next page
        page_token = response.get("nextPageToken")
        if not page_token:
            break  # No more pages
        
        # Small delay between pages to be respectful
        time.sleep(0.1)
    
    return all_items