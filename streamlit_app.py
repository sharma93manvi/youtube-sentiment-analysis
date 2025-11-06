import streamlit as st
import pandas as pd
from datetime import datetime
from config import get_api_key, get_region, get_max_comments
from youtube_api import get_trending_videos, get_video_comments
from sentiment import score_comment

st.set_page_config(page_title="YouTube Sentiment Analysis", layout="wide")

# Header with title, timestamp, and controls
col1, col2, col3 = st.columns([4, 1, 1])
with col1:
    st.markdown("### Trending Videos Analysis")
with col2:
    st.caption(f"Updated {datetime.now().strftime('%b %d, %I:%M %p')}")
with col3:
    st.caption("Top")
    max_results = st.slider("", 1, 20, 10, key="max_results", label_visibility="collapsed")
    if st.button("↻ Refresh", use_container_width=True):
        st.cache_data.clear()

st.markdown("---")

# Read config
api_key = get_api_key()
region = get_region()
max_comments = get_max_comments()

@st.cache_data(ttl=300)
def fetch_trending_videos(api_key: str, region: str, max_results: int = 10):
    return get_trending_videos(api_key, region=region, max_results=max_results)

def generate_overall_analysis(sentiment_data: dict) -> str:
    """Generate a 2-3 line overall analysis based on sentiment data and trend."""
    total = sentiment_data["total"]
    pos_pct = (sentiment_data["positive"] / total * 100) if total > 0 else 0
    neg_pct = (sentiment_data["negative"] / total * 100) if total > 0 else 0
    neu_pct = (sentiment_data["neutral"] / total * 100) if total > 0 else 0
    avg_sentiment = sentiment_data["avg_sentiment"]
    
    # Analyze trend from time_series
    time_series = sentiment_data.get("time_series", [])
    trend_direction = "stable"
    trend_description = "remained relatively stable"
    
    if time_series and len(time_series) > 1:
        # Filter out None values
        valid_values = [v for v in time_series if v is not None]
        if len(valid_values) >= 2:
            # Compare first half vs second half
            mid_point = len(valid_values) // 2
            first_half_avg = sum(valid_values[:mid_point]) / len(valid_values[:mid_point])
            second_half_avg = sum(valid_values[mid_point:]) / len(valid_values[mid_point:])
            
            diff = second_half_avg - first_half_avg
            if diff > 0.05:
                trend_direction = "improving"
                trend_description = "has been improving"
            elif diff < -0.05:
                trend_direction = "declining"
                trend_description = "indicates declining sentiment"
            else:
                trend_direction = "stable"
                trend_description = "has remained relatively stable"
    
    # Generate analysis text
    if pos_pct >= 60:
        sentiment_desc = f"predominantly positive feedback ({pos_pct:.0f}% positive comments)"
        if trend_direction == "improving":
            analysis = f"The video has received {sentiment_desc}. Sentiment {trend_description} over the past 24 hours, with recent comments showing more enthusiasm than earlier ones, indicating growing viewer satisfaction."
        elif trend_direction == "declining":
            analysis = f"The video has received {sentiment_desc}. However, sentiment {trend_description} over the past 24 hours, with more recent comments being less positive, suggesting some concerns emerging among viewers."
        else:
            analysis = f"The video has received {sentiment_desc}. Sentiment {trend_description} over the past 24 hours, showing consistent viewer engagement without significant shifts."
    elif neg_pct >= 40:
        sentiment_desc = f"mixed sentiment with {pos_pct:.0f}% positive and {neg_pct:.0f}% negative comments"
        if trend_direction == "improving":
            analysis = f"The video shows {sentiment_desc}. The trend shows improving sentiment over the past 24 hours, with recent comments being more positive than earlier ones, suggesting viewer sentiment is recovering."
        elif trend_direction == "declining":
            analysis = f"The video shows {sentiment_desc}. The trend {trend_description} over the past 24 hours, with more recent comments being increasingly critical, suggesting potential concerns among viewers."
        else:
            analysis = f"The video shows {sentiment_desc}. Sentiment {trend_description} over the past 24 hours, showing consistent viewer engagement without significant shifts."
    else:
        sentiment_desc = f"a balanced sentiment profile with {pos_pct:.0f}% positive and {neu_pct:.0f}% neutral comments"
        if trend_direction == "improving":
            analysis = f"The video maintains {sentiment_desc}. Sentiment {trend_description} over the past 24 hours, with recent comments showing more positive engagement than earlier ones."
        elif trend_direction == "declining":
            analysis = f"The video maintains {sentiment_desc}. However, sentiment {trend_description} over the past 24 hours, with more recent comments showing increased criticism."
        else:
            analysis = f"The video maintains {sentiment_desc}. Sentiment {trend_description} over the past 24 hours, showing consistent viewer engagement without significant shifts."
    
    return analysis

@st.cache_data(ttl=300)
def analyze_video_sentiment(api_key: str, video_id: str, max_comments: int = 200):
    """Fetch comments and calculate sentiment metrics with time-series data."""
    try:
        comment_items = get_video_comments(api_key, video_id, max_results=max_comments)
        if not comment_items:
            return None
        
        # Extract comment text and timestamps from API response structure
        comment_data = []
        for item in comment_items:
            try:
                top_comment = item.get("snippet", {}).get("topLevelComment", {})
                snippet = top_comment.get("snippet", {})
                comment_text = snippet.get("textDisplay", "")
                published_at = snippet.get("publishedAt", "")
                if comment_text and published_at:
                    comment_data.append({
                        "text": comment_text,
                        "published_at": published_at
                    })
            except (KeyError, AttributeError):
                continue
        
        if not comment_data:
            return None
        
        # Score comments and create time-series
        from datetime import datetime, timedelta
        scores = []
        time_series = []  # Hourly sentiment averages
        
        # Parse all timestamps first to find the time range
        comment_times = []
        for comment in comment_data:
            try:
                pub_time = datetime.fromisoformat(comment["published_at"].replace('Z', '+00:00'))
                comment_times.append(pub_time)
            except (ValueError, AttributeError):
                continue
        
        # Score all comments first (needed for both time-series and top comments)
        comments_with_scores = []
        for comment in comment_data:
            score = score_comment(comment["text"])
            scores.append(score)
            comments_with_scores.append({
                "text": comment["text"],
                "score": score,
                "published_at": comment.get("published_at", "")
            })
        
        if not comment_times:
            # No valid timestamps, return None for time_series
            time_series = [None] * 24
        else:
            # Find the time range (most recent comment to 24 hours before)
            most_recent = max(comment_times)
            start_time = most_recent - timedelta(hours=24)
            
            # Create 24 hourly buckets
            hourly_buckets = {}
            for i in range(24):
                hour_start = start_time + timedelta(hours=i)
                hour_key = hour_start.replace(minute=0, second=0, microsecond=0)
                hourly_buckets[hour_key] = []
            
            # Bucket scored comments by hour
            for comment_with_score in comments_with_scores:
                # Parse timestamp and bucket by hour
                try:
                    pub_time = datetime.fromisoformat(comment_with_score["published_at"].replace('Z', '+00:00'))
                    # Find which hour bucket this belongs to
                    hour_key = pub_time.replace(minute=0, second=0, microsecond=0)
                    if hour_key in hourly_buckets:
                        hourly_buckets[hour_key].append(comment_with_score["score"]["compound"])
                except (ValueError, AttributeError):
                    continue
            
            # Calculate hourly averages (sorted by time)
            for hour_key in sorted(hourly_buckets.keys()):
                bucket_scores = hourly_buckets[hour_key]
                if bucket_scores:
                    time_series.append(sum(bucket_scores) / len(bucket_scores))
                else:
                    time_series.append(None)  # No comments in this hour
        
        if not scores:
            return None
            
        avg_compound = sum(s["compound"] for s in scores) / len(scores)
        pos_count = sum(1 for s in scores if s["label"] == "positive")
        neu_count = sum(1 for s in scores if s["label"] == "neutral")
        neg_count = sum(1 for s in scores if s["label"] == "negative")
        
        return {
            "avg_sentiment": avg_compound,
            "positive": pos_count,
            "neutral": neu_count,
            "negative": neg_count,
            "total": len(comment_data),
            "time_series": time_series  # 24 hourly sentiment values
        }
    except Exception as e:
        # Log error for debugging (will show in terminal)
        st.error(f"Error analyzing video {video_id}: {str(e)}")
        return None

videos = fetch_trending_videos(api_key, region, max_results)
if not videos:
    st.info("No trending videos found")
    st.stop()

def create_distribution_bar(pos_pct, neu_pct, neg_pct, width=100):
    """Create HTML bar for sentiment distribution."""
    pos_width = pos_pct
    neu_width = neu_pct
    neg_width = neg_pct
    return f"""
    <div style="display: flex; width: {width}px; height: 20px; border: 1px solid #ddd; border-radius: 3px; overflow: hidden;">
        <div style="background-color: #22c55e; width: {pos_width}%;"></div>
        <div style="background-color: #94a3b8; width: {neu_width}%;"></div>
        <div style="background-color: #ef4444; width: {neg_width}%;"></div>
    </div>
    """

def create_sparkline(time_series, width=120, height=30):
    """Create SVG sparkline from time-series sentiment data."""
    if not time_series or all(v is None for v in time_series):
        return '<div style="width: {}px; height: {}px; display: flex; align-items: center; justify-content: center; color: #999;">—</div>'.format(width, height)
    
    # Filter out None values and get valid data points
    valid_data = [(i, v) for i, v in enumerate(time_series) if v is not None]
    if not valid_data:
        return '<div style="width: {}px; height: {}px; display: flex; align-items: center; justify-content: center; color: #999;">—</div>'.format(width, height)
    
    # Normalize values to 0-1 range for visualization
    values = [v for _, v in valid_data]
    min_val, max_val = min(values), max(values)
    range_val = max_val - min_val if max_val != min_val else 1
    
    # Create SVG path
    points = []
    for idx, val in enumerate(time_series):
        if val is not None:
            x = (idx / (len(time_series) - 1)) * width if len(time_series) > 1 else width / 2
            y = height - ((val - min_val) / range_val) * (height - 4) - 2
            points.append(f"{x:.1f},{y:.1f}")
    
    path_data = "M " + " L ".join(points)
    
    # Determine color based on overall trend
    avg_sentiment = sum(values) / len(values)
    if avg_sentiment >= 0.05:
        color = "#22c55e"  # green
    elif avg_sentiment <= -0.05:
        color = "#ef4444"  # red
    else:
        color = "#94a3b8"  # gray
    
    return f'''
    <svg width="{width}" height="{height}" style="display: block;">
        <path d="{path_data}" 
              fill="none" 
              stroke="{color}" 
              stroke-width="2" 
              stroke-linecap="round" 
              stroke-linejoin="round"/>
        <circle cx="{points[-1].split(',')[0]}" cy="{points[-1].split(',')[1]}" r="2" fill="{color}"/>
    </svg>
    '''

# Initialize session state for expanded rows
if "expanded_video" not in st.session_state:
    st.session_state.expanded_video = None

# Initialize sentiment cache in session state
if "sentiment_cache" not in st.session_state:
    st.session_state.sentiment_cache = {}

# Step 1: Collect all sentiment data first
progress_bar = st.progress(0)
status_text = st.empty()

video_sentiment_data = {}  # Store all video data with sentiment
for i, video in enumerate(videos, 1):
    # Update progress
    progress = (i - 1) / len(videos)
    progress_bar.progress(progress)
    status_text.text(f"Analyzing video {i}/{len(videos)}: {video['title'][:40]}...")
    
    # Check cache first, otherwise analyze
    video_id = video["video_id"]
    if video_id not in st.session_state.sentiment_cache:
        sentiment_data = analyze_video_sentiment(api_key, video_id, max_comments)
        st.session_state.sentiment_cache[video_id] = sentiment_data
        # Debug: show what we got
        if sentiment_data is None:
            status_text.text(f"⚠️ Video {i}: No sentiment data (comments may be disabled)")
    else:
        sentiment_data = st.session_state.sentiment_cache[video_id]
    
    # Store video data with sentiment
    video_sentiment_data[i] = {
        "video": video,
        "sentiment": sentiment_data
    }

# Clear progress indicators
progress_bar.empty()
status_text.empty()

# Step 2: Calculate and display overall KPIs
all_sentiments = [v["sentiment"] for v in video_sentiment_data.values() if v["sentiment"]]
if all_sentiments:
    total_comments = sum(s["total"] for s in all_sentiments)
    total_positive = sum(s["positive"] for s in all_sentiments)
    total_neutral = sum(s["neutral"] for s in all_sentiments)
    total_negative = sum(s["negative"] for s in all_sentiments)
    avg_sentiment = sum(s["avg_sentiment"] for s in all_sentiments) / len(all_sentiments)
    
    # Display KPIs
    kpi_cols = st.columns(5)
    with kpi_cols[0]:
        st.metric("Videos Analyzed", len(video_sentiment_data))
    with kpi_cols[1]:
        st.metric("Total Comments", f"{total_comments:,}")
    with kpi_cols[2]:
        sentiment_emoji = "🟢" if avg_sentiment >= 0.05 else "🔴" if avg_sentiment <= -0.05 else "⚪"
        st.metric("Avg Sentiment", f"{sentiment_emoji} {avg_sentiment:.3f}")
    with kpi_cols[3]:
        st.metric("Positive", f"{total_positive:,}", f"{(total_positive/total_comments*100):.1f}%")
    with kpi_cols[4]:
        st.metric("Negative", f"{total_negative:,}", f"{(total_negative/total_comments*100):.1f}%")
    
    st.markdown("---")

# Step 3: Add sort/filter controls
sort_col1, sort_col2 = st.columns([1, 3])
with sort_col1:
    sort_by = st.selectbox(
        "Sort by",
        ["Default", "Sentiment (High to Low)", "Sentiment (Low to High)", "Views (High to Low)", "Comments (High to Low)"],
        key="sort_option"
    )

# Apply sorting
if sort_by != "Default":
    def get_sort_key(item):
        data = item[1]
        video = data["video"]
        sentiment = data["sentiment"]
        
        if sort_by == "Sentiment (High to Low)":
            return sentiment["avg_sentiment"] if sentiment else -999
        elif sort_by == "Sentiment (Low to High)":
            return sentiment["avg_sentiment"] if sentiment else 999
        elif sort_by == "Views (High to Low)":
            return video["views"]
        elif sort_by == "Comments (High to Low)":
            return video["comments"]
        return 0
    
    sorted_items = sorted(
        video_sentiment_data.items(),
        key=get_sort_key,
        reverse=sort_by in ["Sentiment (High to Low)", "Views (High to Low)", "Comments (High to Low)"]
    )
    # Re-index to maintain numbering
    video_sentiment_data = {i+1: data for i, (_, data) in enumerate(sorted_items)}

# Table header row
header_cols = st.columns([0.3, 3, 1.5, 1, 1, 1.5, 1, 0.5])
with header_cols[0]:
    st.markdown("**#**")
with header_cols[1]:
    st.markdown("**Video**")
with header_cols[2]:
    st.markdown("**Channel**")
with header_cols[3]:
    st.markdown("**Views**")
with header_cols[4]:
    st.markdown("**Comments**")
with header_cols[5]:
    st.markdown("**Sentiment**")
with header_cols[6]:
    st.markdown("**Distribution**")
with header_cols[7]:
    st.markdown("**Past 24 hours**")

st.markdown("---")

# Step 4: Display table with stored data
for i, data in video_sentiment_data.items():
    video = data["video"]
    sentiment_data = data["sentiment"]
    video_id = video["video_id"]  # Extract video_id for use in expanded view
    
    # Create row with columns
    cols = st.columns([0.3, 3, 1.5, 1, 1, 1.5, 1, 0.5])
    
    with cols[0]:
        st.write(f"**#{i}**")
    
    with cols[1]:
        video_title = f"{video['title'][:60]}..." if len(video['title']) > 60 else video['title']
        if st.button(f"📹 {video_title}", key=f"video_{i}", use_container_width=True):
            if st.session_state.expanded_video == i:
                st.session_state.expanded_video = None
            else:
                st.session_state.expanded_video = i
    
    with cols[2]:
        st.caption(video['channel'][:30])
    
    with cols[3]:
        st.write(f"{video['views']:,}")
    
    with cols[4]:
        st.write(f"{video['comments']:,}")
    
    with cols[5]:
        if sentiment_data:
            sentiment_score = sentiment_data["avg_sentiment"]
            # Color code sentiment
            if sentiment_score >= 0.05:
                color = "🟢"
            elif sentiment_score <= -0.05:
                color = "🔴"
            else:
                color = "⚪"
            st.markdown(f"{color} **{sentiment_score:.2f}**")
        else:
            st.write("N/A")
    
    with cols[6]:
        if sentiment_data:
            pos_pct = (sentiment_data["positive"] / sentiment_data["total"]) * 100
            neu_pct = (sentiment_data["neutral"] / sentiment_data["total"]) * 100
            neg_pct = (sentiment_data["negative"] / sentiment_data["total"]) * 100
            st.markdown(create_distribution_bar(pos_pct, neu_pct, neg_pct), unsafe_allow_html=True)
            st.caption(f"{pos_pct:.0f}% | {neu_pct:.0f}% | {neg_pct:.0f}%")
        else:
            st.write("—")
    
    with cols[7]:
        if sentiment_data and "time_series" in sentiment_data:
            st.markdown(create_sparkline(sentiment_data.get("time_series", [])), unsafe_allow_html=True)
        else:
            st.write("—")
    
    # Expanded detail section
    if st.session_state.expanded_video == i:
        with st.expander(f"📊 Detailed Analysis: {video['title']}", expanded=True):
            # Use the sentiment_data already calculated for this video
            # (it's already in video_sentiment_data from the collection loop)
            expanded_sentiment_data = sentiment_data
            
            # If somehow missing, try to get from cache or re-analyze
            if expanded_sentiment_data is None:
                if video_id in st.session_state.sentiment_cache:
                    expanded_sentiment_data = st.session_state.sentiment_cache[video_id]
                else:
                    with st.spinner("Fetching comments and analyzing sentiment..."):
                        expanded_sentiment_data = analyze_video_sentiment(api_key, video_id, max_comments)
                        st.session_state.sentiment_cache[video_id] = expanded_sentiment_data
            
            if expanded_sentiment_data:
                st.markdown(f"**Average Sentiment:** {expanded_sentiment_data['avg_sentiment']:.3f}")
                st.markdown(f"**Total Comments Analyzed:** {expanded_sentiment_data['total']}")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Positive", expanded_sentiment_data['positive'], f"{(expanded_sentiment_data['positive']/expanded_sentiment_data['total']*100):.1f}%")
                with col2:
                    st.metric("Neutral", expanded_sentiment_data['neutral'], f"{(expanded_sentiment_data['neutral']/expanded_sentiment_data['total']*100):.1f}%")
                with col3:
                    st.metric("Negative", expanded_sentiment_data['negative'], f"{(expanded_sentiment_data['negative']/expanded_sentiment_data['total']*100):.1f}%")
                
                st.markdown("---")
                
                # Overall analysis based on sentiment and trend
                analysis_text = generate_overall_analysis(expanded_sentiment_data)
                st.markdown(analysis_text)
                
                st.markdown("---")
                # Show video link
                st.markdown(f"[Watch on YouTube](https://www.youtube.com/watch?v={video['video_id']})")
            else:
                st.warning("Could not fetch comments for this video (may be disabled or unavailable).")
        
        st.markdown("---")

# Clear progress indicators
progress_bar.empty()
status_text.empty()

# Legend section at bottom
st.markdown("---")
with st.expander("📖 Legend & Help", expanded=False):
    st.markdown("### Sentiment Score")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("🟢 **Positive** (≥ 0.05)")
        st.caption("Generally positive comments")
    with col2:
        st.markdown("⚪ **Neutral** (-0.05 to 0.05)")
        st.caption("Neutral or mixed sentiment")
    with col3:
        st.markdown("🔴 **Negative** (≤ -0.05)")
        st.caption("Generally negative comments")
    
    st.markdown("### Past 24 Hours")
    st.markdown("""
    The sparkline graph shows sentiment trend over the past 24 hours:
    - **Green line** = Overall positive sentiment trend
    - **Red line** = Overall negative sentiment trend  
    - **Gray line** = Neutral sentiment trend
    - The dot at the end shows the most recent sentiment
    - Higher on the graph = more positive, lower = more negative
    """)
    
    st.markdown("### Distribution Bar")
    st.markdown("""
    The colored bar shows the percentage breakdown of comments:
    - **Green** = Positive comments
    - **Gray** = Neutral comments  
    - **Red** = Negative comments
    """)
    
    st.markdown("### How to Use")
    st.markdown("""
    - Click on any video title (📹) to see detailed sentiment analysis
    - Use the **Top** slider to change the number of trending videos displayed
    - Click **↻ Refresh** to update data immediately
    - Data auto-refreshes every 5 minutes
    """)



