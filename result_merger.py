"""Advanced result merging with fuzzy matching and embeddings."""
import logging
from typing import List
from models import Citation, Definition

try:
    from fuzzywuzzy import fuzz
    FUZZYWUZZY_AVAILABLE = True
except ImportError:
    FUZZYWUZZY_AVAILABLE = False
    logging.warning("fuzzywuzzy not available - using simple matching")

from embedder import Embedder


class ResultMerger:
    """Merges deterministic and AI-enhanced results with intelligent deduplication."""
    
    def __init__(self, use_embeddings: bool = True):
        """Initialize result merger.
        
        Args:
            use_embeddings: Whether to use semantic embeddings for similarity
        """
        self.logger = logging.getLogger(__name__)
        self.use_embeddings = use_embeddings
        self.embedder = Embedder() if use_embeddings else None
        
        if use_embeddings and not self.embedder.is_available():
            self.logger.warning("Embeddings not available - using fuzzy matching only")
            self.use_embeddings = False
    
    def merge_citations(self, deterministic: List[Citation],
                       ai_enhanced: List[Citation]) -> List[Citation]:
        """Merge citation lists with intelligent deduplication.
        
        Args:
            deterministic: Citations from deterministic extraction
            ai_enhanced: Citations from AI enhancement
            
        Returns:
            Merged and deduplicated list
        """
        self.logger.info(f"Merging {len(deterministic)} deterministic + {len(ai_enhanced)} AI citations")
        
        # Start with deterministic (higher trust)
        merged = list(deterministic)
        
        # Add AI citations that don't overlap
        for ai_cit in ai_enhanced:
            if not self._has_citation_overlap(ai_cit, merged):
                merged.append(ai_cit)
        
        # Deduplicate
        merged = self._deduplicate_citations(merged)
        
        # Sort by confidence (descending)
        merged.sort(key=lambda x: x.confidence, reverse=True)
        
        self.logger.info(f"Merged result: {len(merged)} unique citations")
        return merged
    
    def merge_definitions(self, deterministic: List[Definition],
                         ai_enhanced: List[Definition]) -> List[Definition]:
        """Merge definition lists with intelligent deduplication.
        
        Args:
            deterministic: Definitions from deterministic extraction
            ai_enhanced: Definitions from AI enhancement
            
        Returns:
            Merged and deduplicated list
        """
        self.logger.info(f"Merging {len(deterministic)} deterministic + {len(ai_enhanced)} AI definitions")
        
        # Start with deterministic (higher trust)
        merged = list(deterministic)
        
        # Add AI definitions that don't overlap
        for ai_def in ai_enhanced:
            if not self._has_definition_overlap(ai_def, merged):
                merged.append(ai_def)
        
        # Deduplicate
        merged = self._deduplicate_definitions(merged)
        
        # Sort by confidence (descending)
        merged.sort(key=lambda x: x.confidence, reverse=True)
        
        self.logger.info(f"Merged result: {len(merged)} unique definitions")
        return merged
    
    def _has_citation_overlap(self, citation: Citation, existing: List[Citation]) -> bool:
        """Check if citation overlaps with existing citations."""
        for exist in existing:
            # Check canonical ID match
            if citation.canonical_id == exist.canonical_id:
                return True
            
            # Check text similarity
            similarity = self._calculate_similarity(citation.text, exist.text)
            if similarity > 0.85:
                return True
        
        return False
    
    def _has_definition_overlap(self, definition: Definition, existing: List[Definition]) -> bool:
        """Check if definition overlaps with existing definitions."""
        for exist in existing:
            # Check term match (normalized)
            if definition.term.lower().strip() == exist.term.lower().strip():
                return True
            
            # Check term similarity
            similarity = self._calculate_similarity(definition.term, exist.term)
            if similarity > 0.90:
                return True
        
        return False
    
    def _deduplicate_citations(self, citations: List[Citation]) -> List[Citation]:
        """Deduplicate citations using fuzzy matching."""
        if not citations:
            return []
        
        unique = []
        seen_ids = set()
        
        for cit in citations:
            # Check canonical ID
            if cit.canonical_id in seen_ids:
                continue
            
            # Check similarity with existing
            is_duplicate = False
            for existing in unique:
                similarity = self._calculate_similarity(cit.text, existing.text)
                if similarity > 0.85:
                    # Keep the one with higher confidence
                    if cit.confidence > existing.confidence:
                        unique.remove(existing)
                        seen_ids.discard(existing.canonical_id)
                    else:
                        is_duplicate = True
                    break
            
            if not is_duplicate:
                unique.append(cit)
                seen_ids.add(cit.canonical_id)
        
        return unique
    
    def _deduplicate_definitions(self, definitions: List[Definition]) -> List[Definition]:
        """Deduplicate definitions using fuzzy matching."""
        if not definitions:
            return []
        
        unique = []
        seen_terms = {}
        
        for defn in definitions:
            term_key = defn.term.lower().strip()
            
            # Check exact match
            if term_key in seen_terms:
                # Keep the one with higher confidence
                existing_idx = seen_terms[term_key]
                if defn.confidence > unique[existing_idx].confidence:
                    unique[existing_idx] = defn
                continue
            
            # Check similarity with existing
            is_duplicate = False
            for i, existing in enumerate(unique):
                similarity = self._calculate_similarity(defn.term, existing.term)
                if similarity > 0.90:
                    # Keep the one with higher confidence
                    if defn.confidence > existing.confidence:
                        unique[i] = defn
                        seen_terms[term_key] = i
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                seen_terms[term_key] = len(unique)
                unique.append(defn)
        
        return unique
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using available methods.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score 0.0-1.0
        """
        # Try embeddings first (most accurate)
        if self.use_embeddings and self.embedder:
            return self.embedder.similarity(text1, text2)
        
        # Fall back to fuzzy matching
        if FUZZYWUZZY_AVAILABLE:
            return fuzz.ratio(text1.lower(), text2.lower()) / 100.0
        
        # Last resort: simple string comparison
        return 1.0 if text1.lower() == text2.lower() else 0.0
