"""NER model for entity extraction."""
import logging
from typing import List, Dict, Tuple
from dataclasses import dataclass

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logging.warning("spacy not available - NER will be disabled")


@dataclass
class NEREntity:
    """Entity extracted by NER."""
    text: str
    label: str
    start: int
    end: int
    confidence: float


class NERModel:
    """Named Entity Recognition for legal documents."""
    
    def __init__(self, model_name: str = "en_core_web_sm"):
        """Initialize NER model.
        
        Args:
            model_name: SpaCy model name
        """
        self.logger = logging.getLogger(__name__)
        self.model_name = model_name
        self.nlp = None
        
        if not SPACY_AVAILABLE:
            self.logger.warning("SpaCy not available. NER functionality disabled.")
            self.logger.warning("To enable NER:")
            self.logger.warning("  pip install spacy")
            self.logger.warning("  python -m spacy download en_core_web_sm")
            return
        
        try:
            self.nlp = spacy.load(model_name)
            self.logger.info(f"Loaded SpaCy model: {model_name}")
        except OSError:
            self.logger.warning(f"SpaCy model '{model_name}' not found.")
            self.logger.warning(f"Download with: python -m spacy download {model_name}")
            self.nlp = None
    
    def extract_entities(self, text: str) -> List[NEREntity]:
        """Extract named entities from text.
        
        Args:
            text: Input text
            
        Returns:
            List of NEREntity objects
        """
        if not self.nlp:
            return []
        
        try:
            doc = self.nlp(text)
            entities = []
            
            for ent in doc.ents:
                # Focus on relevant entity types for legal documents
                if ent.label_ in ['LAW', 'ORG', 'DATE', 'CARDINAL', 'ORDINAL']:
                    entities.append(NEREntity(
                        text=ent.text,
                        label=ent.label_,
                        start=ent.start_char,
                        end=ent.end_char,
                        confidence=0.8  # SpaCy doesn't provide confidence scores
                    ))
            
            return entities
            
        except Exception as e:
            self.logger.error(f"NER extraction failed: {e}")
            return []
    
    def extract_legal_references(self, text: str) -> List[Tuple[str, int, int]]:
        """Extract potential legal document references using NER.
        
        Args:
            text: Input text
            
        Returns:
            List of (text, start, end) tuples
        """
        if not self.nlp:
            return []
        
        entities = self.extract_entities(text)
        
        # Filter for LAW entities and ORG entities that might be legal references
        legal_refs = []
        for ent in entities:
            if ent.label_ == 'LAW':
                legal_refs.append((ent.text, ent.start, ent.end))
            elif ent.label_ == 'ORG' and any(keyword in ent.text.lower() 
                                             for keyword in ['law', 'decree', 'resolution', 'cabinet']):
                legal_refs.append((ent.text, ent.start, ent.end))
        
        return legal_refs
    
    def is_available(self) -> bool:
        """Check if NER is available."""
        return self.nlp is not None
