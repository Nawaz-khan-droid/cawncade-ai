"""
TF-IDF Baseline Signal Module.
Provides a lightweight suspicion score based on TF-IDF patterns.
This is ONE signal among many — NOT the final decision maker.
Integrated into the scoring pipeline as a supplemental signal.
"""
import os
import pickle
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from ...utils.logger import log

# Model file path
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
MODEL_FILE = os.path.join(MODEL_DIR, "tfidf_model.pkl")


class TFIDFModel:
    """
    TF-IDF based suspicion signal.
    In production, this model is trained on labeled fake/real news data.
    For MVP, it provides keyword extraction and a basic pattern score.
    """

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=5000,
            ngram_range=(1, 2),
            token_pattern=r"(?u)\b[a-z]{3,}\b",
        )
        self.model = None
        self._load_model()

    def _load_model(self):
        """Try to load a pre-trained model. If not found, use untrained baseline."""
        if os.path.exists(MODEL_FILE):
            try:
                with open(MODEL_FILE, "rb") as f:
                    pipeline = pickle.load(f)
                self.vectorizer = pipeline.named_steps["tfidf"]
                self.model = pipeline.named_steps["clf"]
                log.info("TF-IDF model loaded from disk.")
                return
            except Exception as e:
                log.warning(f"Could not load TF-IDF model: {e}")

        log.info("No pre-trained TF-IDF model found. Using keyword extraction only.")
        self.model = None

    def train(self, texts: list[str], labels: list[int]):
        """
        Train the TF-IDF model on labeled data.
        labels: 0 = reliable, 1 = suspicious/unreliable
        """
        if len(texts) < 10:
            log.warning("Not enough training data. Need at least 10 samples.")
            return

        pipeline = Pipeline([
            ("tfidf", self.vectorizer),
            ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
        ])
        pipeline.fit(texts, labels)

        self.vectorizer = pipeline.named_steps["tfidf"]
        self.model = pipeline.named_steps["clf"]

        # Save model
        os.makedirs(MODEL_DIR, exist_ok=True)
        with open(MODEL_FILE, "wb") as f:
            pickle.dump(pipeline, f)

        log.info(f"TF-IDF model trained on {len(texts)} samples and saved.")

    def predict(self, text: str) -> dict:
        """
        Get TF-IDF suspicion score and extracted keywords.
        Returns dict with:
          - tfidf_suspicion_score: float (0.0 to 1.0), higher = more suspicious
          - keywords: list of top keywords
        """
        # Always extract keywords
        keywords = self.extract_keywords(text)

        if self.model is None:
            # No trained model — return neutral score
            return {
                "tfidf_suspicion_score": 0.3,  # Neutral default
                "keywords": keywords,
                "model_trained": False,
            }

        try:
            tfidf_matrix = self.vectorizer.transform([text])
            prob = self.model.predict_proba(tfidf_matrix)[0]

            # Probability of class 1 (suspicious)
            suspicion_score = float(prob[1]) if len(prob) > 1 else 0.3

            return {
                "tfidf_suspicion_score": round(suspicion_score, 4),
                "keywords": keywords,
                "model_trained": True,
            }
        except Exception as e:
            log.error(f"TF-IDF prediction error: {e}")
            return {
                "tfidf_suspicion_score": 0.3,
                "keywords": keywords,
                "model_trained": False,
                "error": str(e),
            }

    def extract_keywords(self, text: str, top_n: int = 10) -> list[str]:
        """Extract top keywords using TF-IDF."""
        try:
            tfidf_matrix = self.vectorizer.fit_transform([text])
            feature_names = self.vectorizer.get_feature_names_out()
            scores = tfidf_matrix.toarray()[0]
            top_indices = np.argsort(scores)[-top_n:][::-1]
            return [feature_names[i] for i in top_indices if scores[i] > 0]
        except Exception:
            # Fallback: simple word frequency
            words = text.lower().split()
            word_freq = {}
            for w in words:
                if len(w) > 3 and w not in {"that", "this", "with", "from", "have", "they"}:
                    word_freq[w] = word_freq.get(w, 0) + 1
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            return [w for w, _ in sorted_words[:top_n]]


# Singleton
tfidf_model = TFIDFModel()
