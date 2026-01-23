import logging
import uuid
from datetime import datetime

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from sentence_transformers import SentenceTransformer

logger = logging.getLogger("TitanMemory")

class TitanMemory:
    def __init__(self):
        # 1. Connect to Qdrant (Docker)
        self.client = QdrantClient(url="http://localhost:6333")
        self.collection_name = "market_news_history"

        # 2. Load Embedding Model (Turns text into numbers)
        # 'all-MiniLM-L6-v2' is fast and efficient for this
        logger.info("🧠 Loading Embedding Model (all-MiniLM-L6-v2)...")
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')

        # 3. Initialize Collection if it doesn't exist
        self._init_collection()

    def _init_collection(self):
        if not self.client.collection_exists(self.collection_name):
            logger.info(f"📂 Creating Vector Collection: {self.collection_name}")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )

    def store_event(self, text, metadata):
        """
        Saves a news event + sentiment into the Vector DB.
        """
        # Create Vector
        vector = self.encoder.encode(text).tolist()

        # Create Payload
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload={
                "text": text,
                "timestamp": datetime.utcnow().isoformat(),
                **metadata  # Stores sentiment_score, symbol, etc.
            }
        )

        # Upsert (Upload)
        self.client.upsert(
            collection_name=self.collection_name,
            points=[point]
        )

    def find_similar_events(self, text, limit=3):
        """
        Retrieves the top 'limit' most similar past events.
        """
        vector = self.encoder.encode(text).tolist()
        # FIX: Use query_points (Stable API) instead of search
        search_result = self.client.query_points(
            collection_name=self.collection_name,
            query=vector,
            limit=limit
        )
        # The result object has a 'points' attribute containing the hits
        return search_result.points

# Self-test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    mem = TitanMemory()

    # Test Store
    test_headline = "Apple releases new AI glasses, stock jumps 5%"
    mem.store_event(test_headline, {"sentiment": 0.8, "symbol": "AAPL"})
    print("✅ Stored test event.")

    # Test Retrieve
    print("\n🔍 Searching for similar events...")
    hits = mem.find_similar_events("Tech giant unveils augmented reality hardware")

    for hit in hits:
        print(f"   Found: '{hit.payload['text']}' (Score: {hit.score:.4f})")
