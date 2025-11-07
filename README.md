# YouTube Sentiment Analysis Dashboard

A real-time sentiment analysis dashboard that analyzes YouTube video comments using NLTK VADER sentiment analysis. Analyze trending videos or any YouTube video by pasting a link!

## 🚀 Live Demo

**[Try it live here!](https://youtube-sentiment-intelligence-dashboard.streamlit.app/)**

## Features

### Core Features
- **Trending Videos Analysis**: Fetches and analyzes top trending videos in your selected region (default: Canada)
- **Custom Video Analysis**: Paste any YouTube video link to get instant sentiment analysis
- **Real-time Sentiment Analysis**: Uses NLTK VADER to analyze comment sentiment
- **Interactive Dashboard**: Beautiful Streamlit-based web interface with comprehensive metrics
- **24-Hour Trend Visualization**: Sparkline graphs showing sentiment trends over the past 24 hours
- **Detailed Metrics**: 
  - Sentiment breakdown (Positive, Neutral, Negative percentages)
  - Average sentiment scores
  - Comment distribution visualizations
  - Video statistics (views, likes, comments)

### Dashboard Features
- **Sorting & Filtering**: Sort videos by sentiment, views, or comment count
- **Expandable Details**: Click on any video to see detailed analysis
- **Auto-refresh**: Data refreshes every 5 minutes automatically
- **Manual Refresh**: Click the refresh button for immediate updates
- **Trend Analysis**: AI-generated insights about sentiment patterns and trends

## Screenshots

*Add screenshots of your dashboard here*

## Setup

### Prerequisites

- Python 3.8 or higher
- YouTube Data API v3 key

### 1. Install Dependencies

```bash
# Clone the repository
git clone https://github.com/sharma93manvi/youtube-sentiment-analysis.git
cd youtube-sentiment-analysis

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Get YouTube API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable **YouTube Data API v3**
4. Go to **Credentials** → **Create Credentials** → **API Key**
5. Copy your API key
6. (Optional) Restrict the API key to YouTube Data API v3 for security

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```bash
YOUTUBE_API_KEY=your-api-key-here
REGION=CA                    # Optional: ISO-3166-1 alpha-2 region code (default: CA)
MAX_COMMENTS=200             # Optional: Max comments to analyze per video (default: 200)
CACHE_TTL_SECONDS=300       # Optional: Cache TTL in seconds (default: 300)
```

### 4. Run the Application

```bash
streamlit run streamlit_app.py
```

The dashboard will open in your default web browser at `http://localhost:8501`

## Deployment to Streamlit Cloud

### Step 1: Push to GitHub

Make sure your code is pushed to a GitHub repository.

### Step 2: Deploy on Streamlit Cloud

1. Go to [Streamlit Cloud](https://streamlit.io/cloud)
2. Sign in with your GitHub account
3. Click "New app"
4. Select your repository and branch
5. Set the main file path to `streamlit_app.py`

### Step 3: Configure Secrets

In your Streamlit Cloud app settings, go to "Secrets" and add:

```toml
YOUTUBE_API_KEY = "your-api-key-here"
REGION = "CA"
MAX_COMMENTS = 200
```

**Note**: The app works without `python-dotenv` on Streamlit Cloud since it uses Streamlit's built-in secrets management.

## Usage

### Analyzing Trending Videos

1. Open the dashboard
2. Use the slider to select how many trending videos to analyze (1-20)
3. The dashboard automatically fetches and analyzes the videos
4. Click on any video title to see detailed analysis
5. Use the sort dropdown to organize videos by different criteria

### Analyzing a Custom Video

1. Scroll to the "🔍 Analyze Any YouTube Video" section at the top
2. Paste a YouTube video URL (supports various formats):
   - `https://www.youtube.com/watch?v=VIDEO_ID`
   - `https://youtu.be/VIDEO_ID`
   - `https://www.youtube.com/embed/VIDEO_ID`
   - Or just the video ID
3. Click "🔍 Analyze"
4. View comprehensive sentiment analysis results

## Project Structure

```
youtube-sentiment-analysis/
├── streamlit_app.py          # Main Streamlit dashboard application
├── youtube_api.py            # YouTube API integration functions
├── sentiment.py              # Sentiment analysis using NLTK VADER
├── config.py                 # Configuration and environment variable management
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (not in git)
├── .env.example             # Example environment file
├── README.md                # This file
└── tests/                   # Unit tests
    ├── __init__.py
    ├── conftest.py
    └── test_youtube_api_unit.py
```

## Technologies Used

- **Python 3.8+**: Programming language
- **Streamlit**: Web framework for dashboard
- **NLTK (VADER)**: Natural Language Processing for sentiment analysis
- **Google YouTube Data API v3**: For fetching video and comment data
- **Pandas**: Data manipulation
- **python-dotenv**: Environment variable management (optional, for local development)

## Dependencies

See `requirements.txt` for the complete list. Key dependencies:

- `streamlit==1.31.0`
- `google-api-python-client==2.116.0`
- `python-dotenv==1.0.1` (optional on Streamlit Cloud)
- `pandas==2.2.0`
- `nltk==3.8.1`

## How It Works

1. **Video Fetching**: Uses YouTube Data API v3 to fetch trending videos or video details from a custom URL
2. **Comment Retrieval**: Fetches top-level comments for each video (up to MAX_COMMENTS per video)
3. **Sentiment Analysis**: Each comment is analyzed using NLTK VADER sentiment analyzer
4. **Trend Calculation**: Comments are grouped by hour over the past 24 hours to create trend visualizations
5. **Visualization**: Results are displayed in an interactive dashboard with metrics, charts, and insights

## Sentiment Classification

- **Positive**: Sentiment score ≥ 0.05 (🟢)
- **Neutral**: Sentiment score between -0.05 and 0.05 (⚪)
- **Negative**: Sentiment score ≤ -0.05 (🔴)

## API Quota Considerations

The YouTube Data API has daily quota limits. The app is designed to be quota-efficient:
- Limits comment fetching per video (default: 200)
- Implements caching (5-minute TTL)
- Uses retry logic with exponential backoff for rate limiting

## Troubleshooting

### Common Issues

**ModuleNotFoundError for dotenv**
- This is normal on Streamlit Cloud - the app handles this automatically
- For local development, ensure `python-dotenv` is installed: `pip install python-dotenv`

**API Key Not Found**
- Ensure your `.env` file exists and contains `YOUTUBE_API_KEY`
- On Streamlit Cloud, check that secrets are configured correctly
- Verify the API key is valid and has YouTube Data API v3 enabled

**No Comments Found**
- Some videos have comments disabled
- The app will show "N/A" for videos without comments

**Rate Limiting Errors**
- The app includes retry logic, but if you hit quota limits, wait before retrying
- Consider reducing `MAX_COMMENTS` in your configuration

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[Add your license here]

## Author

Manvi Sharma

## Acknowledgments

- NLTK VADER for sentiment analysis
- Google YouTube Data API v3
- Streamlit for the amazing dashboard framework
