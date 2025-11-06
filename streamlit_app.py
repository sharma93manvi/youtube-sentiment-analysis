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

@st.cache_data(ttl=300)
def analyze_video_sentiment(api_key: str, video_id: str, max_comments: int = 200):
    """Fetch comments and calculate sentiment metrics."""
    try:
        comment_items = get_video_comments(api_key, video_id, max_results=max_comments)
        if not comment_items:
            return None
        
        # Extract comment text from API response structure
        comment_texts = []
        for item in comment_items:
            try:
                top_comment = item.get("snippet", {}).get("topLevelComment", {})
                comment_text = top_comment.get("snippet", {}).get("textDisplay", "")
                if comment_text:
                    comment_texts.append(comment_text)
            except (KeyError, AttributeError):
                continue
        
        if not comment_texts:
            return None
        
        scores = [score_comment(text) for text in comment_texts]
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
            "total": len(comment_texts)
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

def get_trend_indicator(sentiment_score):
    """Get trend indicator based on sentiment score."""
    if sentiment_score >= 0.3:
        return "🟢 ↑"
    elif sentiment_score >= 0.1:
        return "🟡 →"
    elif sentiment_score >= -0.1:
        return "⚪ →"
    elif sentiment_score >= -0.3:
        return "🟠 ↓"
    else:
        return "🔴 ↓"

# Initialize session state for expanded rows
if "expanded_video" not in st.session_state:
    st.session_state.expanded_video = None

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
    st.markdown("**Trend**")

st.markdown("---")

# Initialize sentiment cache in session state
if "sentiment_cache" not in st.session_state:
    st.session_state.sentiment_cache = {}

# Create custom table with visual elements
progress_bar = st.progress(0)
status_text = st.empty()

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
        if sentiment_data:
            st.write(get_trend_indicator(sentiment_data["avg_sentiment"]))
        else:
            st.write("—")
    
    # Expanded detail section
    if st.session_state.expanded_video == i:
        with st.expander(f"📊 Detailed Analysis: {video['title']}", expanded=True):
            # Re-analyze if needed (in case cache was cleared)
            if video_id not in st.session_state.sentiment_cache:
                with st.spinner("Fetching comments and analyzing sentiment..."):
                    sentiment_data = analyze_video_sentiment(api_key, video_id, max_comments)
                    st.session_state.sentiment_cache[video_id] = sentiment_data
            
            sentiment_data = st.session_state.sentiment_cache.get(video_id)
            
            if sentiment_data:
                st.markdown(f"**Average Sentiment:** {sentiment_data['avg_sentiment']:.3f}")
                st.markdown(f"**Total Comments Analyzed:** {sentiment_data['total']}")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Positive", sentiment_data['positive'], f"{(sentiment_data['positive']/sentiment_data['total']*100):.1f}%")
                with col2:
                    st.metric("Neutral", sentiment_data['neutral'], f"{(sentiment_data['neutral']/sentiment_data['total']*100):.1f}%")
                with col3:
                    st.metric("Negative", sentiment_data['negative'], f"{(sentiment_data['negative']/sentiment_data['total']*100):.1f}%")
                
                # Show video link
                st.markdown(f"[Watch on YouTube](https://www.youtube.com/watch?v={video['video_id']})")
            else:
                st.warning("Could not fetch comments for this video (may be disabled or unavailable).")
        
        st.markdown("---")

# Clear progress indicators
progress_bar.empty()
status_text.empty()



