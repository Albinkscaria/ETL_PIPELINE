"""Normalizes document IDs and text."""
import re
import logging


class Canonicalizer:
    """Normalizes document IDs and text."""
    
    def __init__(self):
        """Initialize the canonicalizer."""
        self.logger = logging.getLogger(__name__)
        
        # Patterns for document types (ORDER MATTERS - most specific first!)
        self.doc_type_patterns = {
            r'Federal Decree[- ]?(?:by )?Law': 'fed_decree_law',  # Matches "Federal Decree Law", "Federal Decree-Law", "Federal Decree by Law"
            r'Decree[- ]?Law': 'fed_decree_law',  # Matches "Decree Law", "Decree-Law" (normalize to fed_decree_law)
            r'Federal Law': 'federal_law',
            r'Cabinet Resolution': 'cabinet_resolution',
            r'Ministerial Resolution': 'ministerial_resolution',
            r'Federal Decree': 'federal_decree'
        }
    
    def canonicalize_citation(self, citation_text: str) -> str:
        """Convert citation text to canonical ID.
        
        Args:
            citation_text: Raw citation text
            
        Returns:
            Canonical ID in format: [document_type]_[number]_[year]
        """
        # Extract document type
        doc_type = None
        for pattern, canonical_type in self.doc_type_patterns.items():
            if re.search(pattern, citation_text, re.IGNORECASE):
                doc_type = canonical_type
                break
        
        if not doc_type:
            doc_type = 'unknown'
        
        # Extract number
        number_match = re.search(r'No\.?\s*\(?(\d+)\)?', citation_text, re.IGNORECASE)
        number = number_match.group(1) if number_match else '0'
        
        # Extract year
        year_match = re.search(r'of\s+(\d{4})', citation_text, re.IGNORECASE)
        year = year_match.group(1) if year_match else '0000'
        
        canonical_id = f"{doc_type}_{number}_{year}"
        
        self.logger.debug(f"Canonicalized '{citation_text}' to '{canonical_id}'")
        
        return canonical_id
    
    def normalize_term(self, term: str) -> str:
        """Normalize a term name.
        
        Args:
            term: Raw term text (may contain newlines for multi-line terms)
            
        Returns:
            Normalized term
        """
        # Handle hyphenated line breaks (e.g., "Stock-\npiler" → "Stockpiler")
        # Pattern: word ending with hyphen, newline, then continuation
        normalized = re.sub(r'-\s*\n\s*', '', term)
        
        # Replace remaining newlines with spaces (for multi-line terms like "Government\nAuthorities")
        normalized = normalized.replace('\n', ' ')
        
        # Remove extra whitespace (collapse multiple spaces)
        normalized = ' '.join(normalized.split())
        
        # Remove trailing punctuation (colon, comma, period, etc.)
        normalized = normalized.rstrip(':.,;-—–')
        
        # Remove leading punctuation
        normalized = normalized.lstrip(':.,;-—–')
        
        # Remove quotes
        normalized = normalized.strip('"\'""''')
        
        # Remove "The" prefix if present (common in legal docs)
        if normalized.startswith('The '):
            normalized = normalized[4:]
        
        # Trim again
        normalized = normalized.strip()
        
        return normalized
    
    def normalize_definition(self, definition: str) -> str:
        """Normalize a definition text.
        
        Args:
            definition: Raw definition text
            
        Returns:
            Normalized definition
        """
        # Handle hyphenated line breaks (e.g., "legisla-\ntion" → "legislation")
        normalized = re.sub(r'-\s*\n\s*', '', definition)
        
        # Remove extra whitespace
        normalized = ' '.join(normalized.split())
        
        # Remove leading punctuation (colon, dash, etc.)
        normalized = normalized.lstrip(':,;-—–')
        
        # Remove trailing punctuation except period
        normalized = normalized.rstrip(',;:')
        
        # Trim whitespace
        normalized = normalized.strip()
        
        # Ensure ends with period if it's a complete sentence and doesn't already end with punctuation
        if normalized and not normalized[-1] in '.!?':
            if len(normalized) > 20:  # Likely a complete sentence
                normalized += '.'
        
        return normalized
    
    def generate_doc_id_from_filename(self, filename: str) -> str:
        """Generate canonical document ID from filename.
        
        Args:
            filename: PDF filename
            
        Returns:
            Canonical document ID
        """
        # Remove .pdf extension
        name = filename.replace('.pdf', '')
        
        # Try to extract citation from filename
        canonical_id = self.canonicalize_citation(name)
        
        # If extraction failed, create from filename
        if canonical_id.startswith('unknown'):
            # Convert to snake_case
            canonical_id = re.sub(r'[^\w\s]', '', name)
            canonical_id = re.sub(r'\s+', '_', canonical_id)
            canonical_id = canonical_id.lower()
        
        return canonical_id
