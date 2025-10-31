# YouTube Sentiment Analysis Dashboard

Real-time sentiment analysis of YouTube comments from trending videos in Canada using NLTK VADER and Streamlit.

## Features

- Fetches top 10 trending videos in Canada
- Analyzes sentiment of recent comments using NLTK VADER
- Interactive Streamlit dashboard with metrics and visualizations
- Auto-refresh every 5 minutes with manual refresh option

## Setup

### 1. Install Dependencies

Python 3.9.6

```bash
pip install -r requirements.txt
```

### 2. Get YouTube API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable **YouTube Data API v3**
4. Go to **Credentials** → **Create Credentials** → **API Key**
5. Copy your API key

### 3. Configure Environment

Create a `.env` file in the project root:
Edit `.env` and add your API key:

```bash
YOUTUBE_API_KEY=your-api-key
```

### 4. How to run: 

    streamlit run streamlit_app.py