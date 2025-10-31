from __future__ import annotations
from typing import List, Dict
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

THRESH_POS = 0.05
THRESH_NEG = -0.05

_analyzer: SentimentIntensityAnalyzer | None = None

def get_analyzer() -> SentimentIntensityAnalyzer:
    global _analyzer
    if _analyzer is None:
        try:
            _analyzer = SentimentIntensityAnalyzer()
        except LookupError:
            nltk.download("vader_lexicon")
            _analyzer = SentimentIntensityAnalyzer()
    return _analyzer

def score_comment(text: str) -> Dict:
    s = get_analyzer().polarity_scores(text or "")
    label = "neutral"
    if s["compound"] >= THRESH_POS:
        label = "positive"
    elif s["compound"] <= THRESH_NEG:
        label = "negative"
    return {**s, "label": label}