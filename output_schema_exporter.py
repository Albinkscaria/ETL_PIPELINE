"""Exports data in the correct schema format matching requirements."""
import json
import logging
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path
from models import DocumentResult


class OutputSchemaExporter:
    """Exports data in requirements-compliant schema."""
    
    def __init__(self, output_path: str):
        """Initialize exporter.
        
        Args:
            output_path: Path to output JSON file
        """
        self.logger = logging.getLogger(__name__)
        self.output_path = output_path
        # Also create requirements-compliant format
        self.requirements_path = output_path.replace('.json', '_requirements_format.json')
    
    def export(self, documents: List[Dict], processing_time: float, 
               pipeline_version: str = "1.0.0"):
        """Export in BOTH document-organized AND requirements-compliant formats.
        
        Args:
            documents: List of processed document dictionaries
            processing_time: Total processing time in seconds
            pipeline_version: Version of the pipeline
        """
        # Format 1: Document-organized (current format - easy to navigate)
        doc_organized = self._export_document_organized(documents)
        
        # Format 2: Requirements-compliant (flat arrays with provenance)
        requirements_format = self._export_requirements_format(documents, processing_time, pipeline_version)
        
        # Write document-organized format
        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(doc_organized, f, indent=2, ensure_ascii=False)
        
        # Write requirements-compliant format
        with open(self.requirements_path, 'w', encoding='utf-8') as f:
            json.dump(requirements_format, f, indent=2, ensure_ascii=False)
        
        total_citations = sum(len(doc['citations']) for doc in documents)
        total_definitions = sum(len(doc['terms_definitions']) for doc in documents)
        
        self.logger.info(f"Exported to {self.output_path} (document-organized)")
        self.logger.info(f"Exported to {self.requirements_path} (requirements-compliant)")
        self.logger.info(f"  - {len(documents)} documents")
        self.logger.info(f"  - {total_citations} citations")
        self.logger.info(f"  - {total_definitions} definitions")
        
        # Also export file sizes
        file_size = Path(self.output_path).stat().st_size
        req_file_size = Path(self.requirements_path).stat().st_size
        self.logger.info(f"  - File sizes: {file_size:,} bytes (doc-organized), {req_file_size:,} bytes (requirements)")
    
    def _export_document_organized(self, documents: List[Dict]) -> Dict:
        """Export in document-organized format (current format)."""
        output = {}
        
        for doc in documents:
            filename = doc['source_filename']
            
            # Format citations for this document
            citations = []
            for cit in doc['citations']:
                citations.append({
                    "text": cit['text'],
                    "canonical_id": cit['canonical_id'],
                    "page": cit['page'],
                    "confidence": cit['confidence'],
                    "extraction_method": cit['extraction_method']
                })
            
            # Format definitions for this document
            definitions = []
            for defn in doc['terms_definitions']:
                definitions.append({
                    "term": defn['term'],
                    "definition": defn['definition'],
                    "page": defn['page'],
                    "confidence": defn['confidence'],
                    "extraction_method": defn['extraction_method']
                })
            
            # Add document entry
            output[filename] = {
                "metadata": {
                    "doc_id": doc['doc_id'],
                    "pages": doc['metadata'].get('pages', 0),
                    "processing_date": doc['metadata'].get('processing_date', ''),
                    "processing_time_seconds": doc['metadata'].get('processing_time_seconds', 0)
                },
                "citations": citations,
                "term_definitions": definitions
            }
        
        return output
    
    def _export_requirements_format(self, documents: List[Dict], 
                                    processing_time: float, 
                                    pipeline_version: str) -> Dict:
        """Export in requirements-compliant format (flat arrays with provenance).
        
        This matches the exact schema from the requirements document:
        {
          "source_manifest": [...],
          "citations": [...],
          "term_definitions": [...],
          "summary": {...}
        }
        """
        # Build source manifest
        source_manifest = []
        for doc in documents:
            source_manifest.append({
                "doc_id": doc['doc_id'],
                "filename": doc['source_filename'],
                "pages": doc['metadata'].get('pages', 0),
                "ingested_at": doc['metadata'].get('processing_date', '')
            })
        
        # Build flat citations array with provenance
        all_citations = {}  # canonical_id -> citation with provenance
        for doc in documents:
            for cit in doc['citations']:
                canonical_id = cit['canonical_id']
                
                # Create provenance entry
                provenance_entry = {
                    "doc_id": doc['doc_id'],
                    "page": cit['page'],
                    "excerpt": cit['text'][:200]  # First 200 chars
                }
                
                if canonical_id in all_citations:
                    # Add to existing citation's provenance
                    all_citations[canonical_id]['provenance'].append(provenance_entry)
                    # Update confidence to max
                    all_citations[canonical_id]['confidence'] = max(
                        all_citations[canonical_id]['confidence'],
                        cit['confidence']
                    )
                else:
                    # Create new citation entry
                    all_citations[canonical_id] = {
                        "canonical_id": canonical_id,
                        "raw_text": cit['text'],
                        "normalized": canonical_id,
                        "type": self._extract_citation_type(cit['text']),
                        "number": self._extract_citation_number(cit['text']),
                        "year": self._extract_citation_year(cit['text']),
                        "title": self._extract_citation_title(cit['text']),
                        "provenance": [provenance_entry],
                        "confidence": cit['confidence'],
                        "extraction_method": cit['extraction_method']
                    }
        
        # Build flat term_definitions array with provenance
        all_definitions = {}  # normalized_term -> definition with provenance
        for doc in documents:
            for defn in doc['terms_definitions']:
                normalized_term = defn['term'].lower().replace(' ', '_')
                
                # Create provenance entry
                provenance_entry = {
                    "doc_id": doc['doc_id'],
                    "page": defn['page'],
                    "excerpt": f"{defn['term']}: {defn['definition'][:150]}"
                }
                
                if normalized_term in all_definitions:
                    # Add to existing definition's provenance
                    all_definitions[normalized_term]['provenance'].append(provenance_entry)
                    # Update confidence to max
                    all_definitions[normalized_term]['confidence'] = max(
                        all_definitions[normalized_term]['confidence'],
                        defn['confidence']
                    )
                else:
                    # Create new definition entry
                    all_definitions[normalized_term] = {
                        "term": defn['term'],
                        "definition": defn['definition'],
                        "normalized_term": normalized_term,
                        "provenance": [provenance_entry],
                        "confidence": defn['confidence'],
                        "extraction_method": defn['extraction_method']
                    }
        
        # Build summary
        summary = {
            "total_documents": len(documents),
            "total_citations": len(all_citations),
            "total_terms": len(all_definitions),
            "processing_time_seconds": round(processing_time, 2),
            "processing_date": datetime.utcnow().isoformat() + 'Z',
            "pipeline_version": pipeline_version
        }
        
        # Build final output
        output = {
            "source_manifest": source_manifest,
            "citations": list(all_citations.values()),
            "term_definitions": list(all_definitions.values()),
            "summary": summary
        }
        
        return output
    
    def _extract_citation_type(self, text: str) -> str:
        """Extract citation type from text."""
        text_lower = text.lower()
        if 'federal decree-law' in text_lower or 'federal decree law' in text_lower:
            return 'federal_decree_law'
        elif 'federal decree by law' in text_lower:
            return 'federal_decree_law'
        elif 'cabinet resolution' in text_lower:
            return 'cabinet_resolution'
        elif 'federal law' in text_lower:
            return 'federal_law'
        elif 'ministerial resolution' in text_lower:
            return 'ministerial_resolution'
        elif 'ministerial decision' in text_lower:
            return 'ministerial_decision'
        else:
            return 'unknown'
    
    def _extract_citation_number(self, text: str) -> int:
        """Extract citation number from text."""
        import re
        match = re.search(r'No\.?\s*\(?\s*(\d+)\s*\)?', text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return 0
    
    def _extract_citation_year(self, text: str) -> int:
        """Extract citation year from text."""
        import re
        match = re.search(r'\b(19|20)\d{2}\b', text)
        if match:
            return int(match.group(0))
        return 0
    
    def _extract_citation_title(self, text: str) -> str:
        """Extract citation title from text."""
        import re
        # Try to extract text after "Concerning" or "on" or "Regarding"
        match = re.search(r'(?:Concerning|on|Regarding)\s+(.+?)(?:\.|$)', text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        # Otherwise return the full text
        return text

