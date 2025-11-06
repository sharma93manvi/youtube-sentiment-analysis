from unittest.mock import patch, MagicMock

from sentiment import score_comment


class _FakeAnalyzer:
    def __init__(self, compound: float):
        self._compound = compound

    def polarity_scores(self, text: str):
        # Return full VADER-like dict
        return {"neg": 0.0, "neu": 1.0, "pos": 0.0, "compound": self._compound}


@patch("sentiment.get_analyzer", return_value=_FakeAnalyzer(0.8))
def test_score_comment_positive(mock_ga):
    out = score_comment("I love this!")
    assert out["compound"] == 0.8
    assert out["label"] == "positive"


@patch("sentiment.get_analyzer", return_value=_FakeAnalyzer(-0.2))
def test_score_comment_negative(mock_ga):
    out = score_comment("I hate this.")
    assert out["compound"] == -0.2
    assert out["label"] == "negative"


@patch("sentiment.get_analyzer", return_value=_FakeAnalyzer(0.0))
def test_score_comment_neutral(mock_ga):
    out = score_comment("This is okay.")
    assert out["compound"] == 0.0
    assert out["label"] == "neutral"


@patch("sentiment.get_analyzer", return_value=_FakeAnalyzer(0.0))
def test_score_comment_handles_none(mock_ga):
    out = score_comment(None)  # type: ignore[arg-type]
    assert out["label"] == "neutral"



