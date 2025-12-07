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
    
    def export(self, documents: List[Dict], processing_time: float, 
               pipeline_version: str = "1.0.0"):
        """Export in document-organized format.
        
        Args:
            documents: List of processed document dictionaries
            processing_time: Total processing time in seconds
            pipeline_version: Version of the pipeline
        """
        # Build output organized by document filename
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
        
        # Write to file
        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        total_citations = sum(len(doc['citations']) for doc in documents)
        total_definitions = sum(len(doc['terms_definitions']) for doc in documents)
        
        self.logger.info(f"Exported to {self.output_path}")
        self.logger.info(f"  - {len(documents)} documents")
        self.logger.info(f"  - {total_citations} citations")
        self.logger.info(f"  - {total_definitions} definitions")
        
        # Also export file size
        file_size = Path(self.output_path).stat().st_size
        self.logger.info(f"  - File size: {file_size:,} bytes")

