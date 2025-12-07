"""Validates and merges extraction results."""
import logging
from typing import List, Dict, Any
from models import Citation, Definition


class DataValidator:
    """Validates and merges extraction results."""
    
    def __init__(self):
        """Initialize the data validator."""
        self.logger = logging.getLogger(__name__)
    
    def merge_results(self, deterministic: List, ai_enhanced: List) -> List:
        """Merge deterministic and AI-enhanced results.
        
        Args:
            deterministic: Results from deterministic extraction
            ai_enhanced: Results from AI enhancement
            
        Returns:
            Merged list of results
        """
        # Combine lists
        merged = list(deterministic) + list(ai_enhanced)
        
        # Deduplicate
        merged = self.deduplicate(merged)
        
        # Sort by confidence (highest first)
        merged.sort(key=lambda x: x.confidence, reverse=True)
        
        self.logger.info(f"Merged {len(deterministic)} deterministic + {len(ai_enhanced)} AI = {len(merged)} total")
        
        return merged
    
    def deduplicate(self, items: List) -> List:
        """Remove duplicate items.
        
        Args:
            items: List of Citation or Definition objects
            
        Returns:
            Deduplicated list
        """
        if not items:
            return []
        
        # Determine item type
        if isinstance(items[0], Citation):
            return self._deduplicate_citations(items)
        elif isinstance(items[0], Definition):
            return self._deduplicate_definitions(items)
        else:
            return items
    
    def _deduplicate_citations(self, citations: List[Citation]) -> List[Citation]:
        """Deduplicate citations with smart matching."""
        import re
        seen = {}
        
        for citation in citations:
            # Use canonical_id as primary key for deduplication
            # But normalize it first to handle variations
            canonical_id = citation.canonical_id
            
            # Normalize canonical IDs:
            # - "federal_decree_28_2022" → "fed_decree_law_28_2022"
            # - "unknown_28_2022" → "fed_decree_law_28_2022" (if text has "Decree Law")
            normalized_id = canonical_id
            
            # Fix "federal_decree" to "fed_decree_law" if text contains "law"
            if normalized_id.startswith('federal_decree_') and 'law' in citation.text.lower():
                normalized_id = normalized_id.replace('federal_decree_', 'fed_decree_law_')
            
            # Fix "unknown" to proper type if we can extract it
            if normalized_id.startswith('unknown_'):
                # Try to extract number and year
                number_match = re.search(r'(\d+)_(\d{4})', normalized_id)
                if number_match:
                    number, year = number_match.groups()
                    # Determine type from text
                    text_lower = citation.text.lower()
                    if 'decree' in text_lower and 'law' in text_lower:
                        normalized_id = f'fed_decree_law_{number}_{year}'
                    elif 'cabinet' in text_lower and 'resolution' in text_lower:
                        normalized_id = f'cabinet_resolution_{number}_{year}'
                    elif 'federal law' in text_lower:
                        normalized_id = f'federal_law_{number}_{year}'
            
            # Use normalized ID as key
            key = normalized_id
            
            # Keep the one with higher confidence, or prefer "Federal" prefix
            if key not in seen:
                seen[key] = citation
            else:
                # Prefer citations with "Federal" prefix
                if 'federal' in citation.text.lower() and 'federal' not in seen[key].text.lower():
                    seen[key] = citation
                elif citation.confidence > seen[key].confidence:
                    seen[key] = citation
        
        result = list(seen.values())
        self.logger.debug(f"Deduplicated {len(citations)} citations to {len(result)}")
        
        return result
    
    def _deduplicate_definitions(self, definitions: List[Definition]) -> List[Definition]:
        """Deduplicate definitions."""
        seen = {}
        
        for definition in definitions:
            key = definition.term.lower().strip()
            
            # Keep the one with higher confidence
            if key not in seen or definition.confidence > seen[key].confidence:
                seen[key] = definition
        
        result = list(seen.values())
        self.logger.debug(f"Deduplicated {len(definitions)} definitions to {len(result)}")
        
        return result
    
    def validate_schema(self, data: Dict) -> bool:
        """Validate the output data schema.
        
        Args:
            data: Output data dictionary
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check top-level structure
            if 'documents' not in data or 'summary' not in data:
                self.logger.error("Missing 'documents' or 'summary' in output")
                return False
            
            # Check documents
            if not isinstance(data['documents'], list):
                self.logger.error("'documents' must be a list")
                return False
            
            # Check each document
            for doc in data['documents']:
                if not self._validate_document(doc):
                    return False
            
            # Check summary
            if not self._validate_summary(data['summary']):
                return False
            
            self.logger.info("Schema validation passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Schema validation error: {e}")
            return False
    
    def _validate_document(self, doc: Dict) -> bool:
        """Validate a single document."""
        required_fields = ['doc_id', 'source_filename', 'metadata', 'citations', 'terms_definitions']
        
        for field in required_fields:
            if field not in doc:
                self.logger.error(f"Missing field '{field}' in document")
                return False
        
        # Check metadata
        if not isinstance(doc['metadata'], dict):
            self.logger.error("'metadata' must be a dictionary")
            return False
        
        # Check citations
        if not isinstance(doc['citations'], list):
            self.logger.error("'citations' must be a list")
            return False
        
        # Check terms_definitions
        if not isinstance(doc['terms_definitions'], list):
            self.logger.error("'terms_definitions' must be a list")
            return False
        
        return True
    
    def _validate_summary(self, summary: Dict) -> bool:
        """Validate the summary section."""
        required_fields = ['total_documents', 'total_citations', 'total_terms', 'processing_time_seconds']
        
        for field in required_fields:
            if field not in summary:
                self.logger.error(f"Missing field '{field}' in summary")
                return False
        
        return True
