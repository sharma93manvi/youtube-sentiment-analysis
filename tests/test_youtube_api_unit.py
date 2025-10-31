from unittest.mock import patch, MagicMock

from youtube_api import get_trending_videos


def _mock_service_with_items(items):
    mock_execute = MagicMock(return_value={"items": items})
    mock_list = MagicMock(return_value=MagicMock(execute=mock_execute))
    mock_videos = MagicMock(list=mock_list)
    mock_service = MagicMock(videos=MagicMock(return_value=mock_videos))
    return mock_service


@patch("youtube_api.build")
def test_get_trending_videos_parsing(mock_build):
    items = [
        {
            "id": "abc123",
            "snippet": {
                "title": "Video Title",
                "channelTitle": "Channel Name",
                "publishedAt": "2024-01-01T00:00:00Z",
                "thumbnails": {"default": {"url": "http://thumb"}},
            },
            "statistics": {"viewCount": "100", "likeCount": "10", "commentCount": "5"},
        }
    ]

    mock_build.return_value = _mock_service_with_items(items)

    out = get_trending_videos(api_key="dummy", region="CA", max_results=1, retries=1)
    assert len(out) == 1
    v = out[0]
    assert v["video_id"] == "abc123"
    assert v["title"] == "Video Title"
    assert v["channel"] == "Channel Name"
    assert v["views"] == 100
    assert v["likes"] == 10
    assert v["comments"] == 5

