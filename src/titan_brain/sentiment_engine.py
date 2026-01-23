import logging

import torch
import torch.nn.functional as F  # noqa: N812
from transformers import AutoModelForSequenceClassification, AutoTokenizer

logger = logging.getLogger("TitanEngine")

class FinBERTEngine:
    def __init__(self):
        logger.info("🧠 Loading FinBERT Model... (This happens only once)")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"⚙️ Inference Device: {self.device.upper()}")

        # Load Pre-trained Financial BERT
        model_name = "ProsusAI/finbert"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name).to(self.device)
        self.model.eval() # Set to evaluation mode (faster)

        # Labels map: 0=Positive, 1=Negative, 2=Neutral (Check model config to confirm)
        self.labels = ["positive", "negative", "neutral"]

    def analyze(self, text):
        """
        Returns: (sentiment_score, confidence, label)
        Score range: -1.0 (Negative) to +1.0 (Positive)
        """
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True).to(self.device)

        with torch.no_grad():
            outputs = self.model(**inputs)
            probabilities = F.softmax(outputs.logits, dim=1)

        # Move to CPU for processing
        probs = probabilities.cpu().numpy()[0]

        # ProsusAI FinBERT Output Order: [Positive, Negative, Neutral]
        score_pos = probs[0]
        score_neg = probs[1]

        # Calculate a single scalar score (-1 to 1)
        sentiment_scalar = score_pos - score_neg

        confidence = max(probs)
        predicted_id = probs.argmax()
        label = self.labels[predicted_id]

        return {
            "score": float(sentiment_scalar),
            "confidence": float(confidence),
            "label": label
        }
