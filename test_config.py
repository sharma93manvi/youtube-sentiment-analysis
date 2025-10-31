from config import get_api_key, get_region, get_max_comments, get_cache_ttl

# If your .env has YOUTUBE_API_KEY set, this should print first 6 chars
print("API key:", get_api_key()[:6] + "...")

print("Region:", get_region())              # Defaults to 'CA' if not set
print("Max comments:", get_max_comments())  # Defaults to 200 if not set
print("Cache TTL:", get_cache_ttl())        # Defaults to 300 if not set