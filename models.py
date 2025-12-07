"""Data models for the ETL pipeline."""
from dataclasses import dataclass
from typing import List, Dict, Optional, Any


@dataclass
class Page:
    """Represents a single PDF page with text and layout information."""
    page_num: int
    text: str
    layout_info: Dict[str, Any]
    

@dataclass
class Citation:
    """Represents a citation to another legal document."""
    text: str
    canonical_id: str
    page: int
    confidence: float
    extraction_method: str
    context: str = ""  # Surrounding text (±100 chars)
    position: Optional[tuple] = None  # (start, end) character positions
    
    def to_dict(self) -> Dict:
        return {
            "text": self.text,
            "canonical_id": self.canonical_id,
            "page": self.page,
            "confidence": self.confidence,
            "extraction_method": self.extraction_method,
            "context": self.context,
            "position": self.position
        }


@dataclass
class Definition:
    """Represents a term-definition pair."""
    term: str
    definition: str
    page: int
    confidence: float
    extraction_method: str
    references: List[str] = None  # Referenced terms/articles
    position: Optional[tuple] = None  # (start, end) character positions
    
    def __post_init__(self):
        if self.references is None:
            self.references = []
    
    def to_dict(self) -> Dict:
        return {
            "term": self.term,
            "definition": self.definition,
            "page": self.page,
            "confidence": self.confidence,
            "extraction_method": self.extraction_method,
            "references": self.references,
            "position": self.position
        }


@dataclass
class DocumentResult:
    """Represents the complete extraction result for a document."""
    doc_id: str
    source_filename: str
    metadata: Dict[str, Any]
    citations: List[Citation]
    terms_definitions: List[Definition]
    
    def to_dict(self) -> Dict:
        return {
            "doc_id": self.doc_id,
            "source_filename": self.source_filename,
            "metadata": self.metadata,
            "citations": [c.to_dict() for c in self.citations],
            "terms_definitions": [d.to_dict() for d in self.terms_definitions]
        }
