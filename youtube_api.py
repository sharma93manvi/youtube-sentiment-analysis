import time
from typing import List, Dict

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Initialize YouTube API client
def get_youtube_client(api_key: str):
    """Create and return a YouTube Data API v3 service object.
    YouTube Data API v3 (Google Developers):
    https://developers.google.com/youtube/v3/docs"""
    return build("youtube", "v3", developerKey=api_key, cache_discovery=False)

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