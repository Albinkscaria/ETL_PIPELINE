"""Semantic embeddings for similarity matching."""
import logging
from typing import List, Tuple
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logging.warning("sentence-transformers not available - embeddings disabled")


class Embedder:
    """Semantic embeddings for text similarity."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize embedder.
        
        Args:
            model_name: Sentence transformer model name
        """
        self.logger = logging.getLogger(__name__)
        self.model_name = model_name
        self.model = None
        
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            self.logger.warning("sentence-transformers not available. Embeddings disabled.")
            self.logger.warning("To enable: pip install sentence-transformers")
            return
        
        try:
            self.model = SentenceTransformer(model_name)
            self.logger.info(f"Loaded embedding model: {model_name}")
        except Exception as e:
            self.logger.error(f"Failed to load embedding model: {e}")
            self.model = None
    
    def encode(self, texts: List[str]) -> np.ndarray:
        """Encode texts to embeddings.
        
        Args:
            texts: List of text strings
            
        Returns:
            Numpy array of embeddings
        """
        if not self.model:
            return np.array([])
        
        try:
            embeddings = self.model.encode(texts, show_progress_bar=False)
            return embeddings
        except Exception as e:
            self.logger.error(f"Encoding failed: {e}")
            return np.array([])
    
    def similarity(self, text1: str, text2: str) -> float:
        """Calculate cosine similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score 0.0-1.0
        """
        if not self.model:
            return 0.0
        
        try:
            embeddings = self.encode([text1, text2])
            if len(embeddings) != 2:
                return 0.0
            
            # Cosine similarity
            similarity = np.dot(embeddings[0], embeddings[1]) / (
                np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
            )
            
            # Normalize to 0-1
            return float((similarity + 1) / 2)
            
        except Exception as e:
            self.logger.error(f"Similarity calculation failed: {e}")
            return 0.0
    
    def find_similar(self, query: str, candidates: List[str], 
                     threshold: float = 0.7) -> List[Tuple[int, float]]:
        """Find similar texts from candidates.
        
        Args:
            query: Query text
            candidates: List of candidate texts
            threshold: Minimum similarity threshold
            
        Returns:
            List of (index, similarity) tuples
        """
        if not self.model or not candidates:
            return []
        
        try:
            # Encode all texts
            all_texts = [query] + candidates
            embeddings = self.encode(all_texts)
            
            if len(embeddings) == 0:
                return []
            
            query_emb = embeddings[0]
            candidate_embs = embeddings[1:]
            
            # Calculate similarities
            similarities = []
            for i, cand_emb in enumerate(candidate_embs):
                sim = np.dot(query_emb, cand_emb) / (
                    np.linalg.norm(query_emb) * np.linalg.norm(cand_emb)
                )
                sim = float((sim + 1) / 2)  # Normalize to 0-1
                
                if sim >= threshold:
                    similarities.append((i, sim))
            
            # Sort by similarity (descending)
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            return similarities
            
        except Exception as e:
            self.logger.error(f"Similar search failed: {e}")
            return []
    
    def is_available(self) -> bool:
        """Check if embedder is available."""
        return self.model is not None
