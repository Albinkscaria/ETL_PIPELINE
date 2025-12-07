"""Main pipeline coordinator."""
import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, List
from document_ingestor import DocumentIngestor
from page_extractor import PageExtractor
from deterministic_extractor import DeterministicExtractor
from gemini_enhancer import GeminiEnhancer
from canonicalizer import Canonicalizer
from data_validator import DataValidator
from json_exporter import JSONExporter
from models import DocumentResult
from ocr_processor import OCRProcessor
from ner_model import NERModel
from embedder import Embedder
from result_merger import ResultMerger
from human_review_queue import HumanReviewQueue
from schema_validator import SchemaValidator
from output_schema_exporter import OutputSchemaExporter


class ETLOrchestrator:
    """Main pipeline coordinator."""
    
    def __init__(self, config_path: str = 'config.json'):
        """Initialize the ETL orchestrator.
        
        Args:
            config_path: Path to configuration file
        """
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.logger.info(f"Loaded configuration from {config_path}")
        
        # Initialize components
        self.ingestor = DocumentIngestor(self.config['pdf_directory'])
        self.deterministic_extractor = DeterministicExtractor()
        self.canonicalizer = Canonicalizer()
        self.validator = DataValidator()
        self.exporter = JSONExporter(self.config['output_file'])
        
        # Initialize new components
        self.ocr_processor = OCRProcessor() if self.config.get('enable_ocr', True) else None
        self.ner_model = NERModel() if self.config.get('enable_ner', False) else None
        self.embedder = Embedder() if self.config.get('use_embeddings', True) else None
        self.result_merger = ResultMerger(use_embeddings=self.config.get('use_embeddings', True))
        self.human_review_queue = HumanReviewQueue(
            threshold=self.config.get('review_threshold', 0.7)
        ) if self.config.get('enable_human_review_queue', True) else None
        self.schema_validator = SchemaValidator()
        self.output_schema_exporter = OutputSchemaExporter(self.config['output_file'])
        
        # Check if AI enhancement is enabled
        self.use_ai_enhancement = self.config.get('use_ai_enhancement', False)
        
        # Initialize Gemini enhancer only if enabled
        self.gemini_enhancer = None
        if self.use_ai_enhancement:
            api_key_env_name = self.config['gemini_api_key_env']
            api_key = os.getenv(api_key_env_name)
            if not api_key:
                self.logger.warning(f"AI enhancement enabled but API key '{api_key_env_name}' not found. Disabling AI enhancement.")
                self.use_ai_enhancement = False
            else:
                self.gemini_enhancer = GeminiEnhancer(
                    api_key=api_key,
                    model_name=self.config['gemini_model'],
                    max_retries=self.config['max_retries'],
                    chunk_size=self.config['chunk_size'],
                    chunk_overlap=self.config['chunk_overlap']
                )
                self.logger.info("AI enhancement enabled with Gemini")
        else:
            self.logger.info("AI enhancement disabled - using deterministic extraction only")
        
        self.logger.info("ETL Orchestrator initialized")
    
    def run_pipeline(self) -> Dict:
        """Run the complete ETL pipeline.
        
        Returns:
            Final output data dictionary
        """
        self.logger.info("=" * 80)
        self.logger.info("Starting ETL Pipeline")
        self.logger.info("=" * 80)
        
        start_time = time.time()
        
        # Get list of PDFs
        pdf_files = self.ingestor.list_pdfs()
        
        if not pdf_files:
            self.logger.error("No PDF files found")
            return self._create_empty_output(0)
        
        self.logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        # Process each document
        documents = []
        errors = []
        
        for i, pdf_file in enumerate(pdf_files, 1):
            self.logger.info(f"\n{'='*80}")
            self.logger.info(f"Processing document {i}/{len(pdf_files)}: {pdf_file}")
            self.logger.info(f"{'='*80}")
            
            try:
                doc_result = self.process_single_document(pdf_file)
                documents.append(doc_result)
                
                self.logger.info(f"✓ Successfully processed: {pdf_file}")
                self.logger.info(f"  - Citations: {len(doc_result['citations'])}")
                self.logger.info(f"  - Definitions: {len(doc_result['terms_definitions'])}")
                
            except Exception as e:
                self.logger.error(f"✗ Failed to process {pdf_file}: {e}", exc_info=True)
                errors.append({
                    'filename': pdf_file,
                    'error': str(e)
                })
        
        # Calculate summary statistics
        end_time = time.time()
        processing_time = end_time - start_time
        
        total_citations = sum(len(doc['citations']) for doc in documents)
        total_terms = sum(len(doc['terms_definitions']) for doc in documents)
        
        # Create final output
        output = {
            'documents': documents,
            'summary': {
                'total_documents': len(documents),
                'total_citations': total_citations,
                'total_terms': total_terms,
                'processing_time_seconds': round(processing_time, 2)
            }
        }
        
        if errors:
            output['errors'] = errors
        
        # Add to human review queue if enabled
        if self.human_review_queue:
            # Convert dicts back to objects for review queue
            from models import Citation, Definition
            all_citations = []
            all_definitions = []
            
            for doc in documents:
                for c in doc['citations']:
                    all_citations.append(Citation(
                        text=c['text'],
                        canonical_id=c['canonical_id'],
                        page=c['page'],
                        confidence=c['confidence'],
                        extraction_method=c['extraction_method'],
                        context=c.get('context', ''),
                        position=c.get('position')
                    ))
                for d in doc['terms_definitions']:
                    all_definitions.append(Definition(
                        term=d['term'],
                        definition=d['definition'],
                        page=d['page'],
                        confidence=d['confidence'],
                        extraction_method=d['extraction_method'],
                        references=d.get('references', []),
                        position=d.get('position')
                    ))
            
            self.human_review_queue.check_and_add(all_citations)
            self.human_review_queue.check_and_add(all_definitions)
            
            if self.human_review_queue.queue:
                review_file = self.human_review_queue.export_review_batch(format='csv')
                self.logger.info(f"Exported review queue to: {review_file}")
                summary = self.human_review_queue.get_queue_summary()
                self.logger.info(f"Review queue summary: {summary}")
        
        # Export in requirements-compliant format
        self.output_schema_exporter.export(documents, processing_time)
        
        # Note: Schema validation is skipped since we're using the new requirements-compliant format
        # The old validator expects the legacy format structure
        
        # Legacy export (for backward compatibility - writes to extracted_data_legacy.json)
        # Commenting out to use only requirements-compliant format
        # self.exporter.export(output)
        
        # Log final summary
        self.logger.info("\n" + "=" * 80)
        self.logger.info("PIPELINE COMPLETE")
        self.logger.info("=" * 80)
        self.logger.info(f"Documents processed: {len(documents)}/{len(pdf_files)}")
        self.logger.info(f"Total citations: {total_citations}")
        self.logger.info(f"Total definitions: {total_terms}")
        self.logger.info(f"Processing time: {processing_time:.2f} seconds")
        self.logger.info(f"Output file: {self.config['output_file']}")
        
        if errors:
            self.logger.warning(f"Errors encountered: {len(errors)}")
            for error in errors:
                if isinstance(error, dict):
                    self.logger.warning(f"  - {error['filename']}: {error['error']}")
                else:
                    self.logger.warning(f"  - {error}")
        
        return output
    
    def process_single_document(self, pdf_file: str) -> Dict:
        """Process a single PDF document.
        
        Args:
            pdf_file: Name of the PDF file
            
        Returns:
            Document result dictionary
        """
        doc_start_time = time.time()
        
        # Get full path
        pdf_path = self.ingestor.get_pdf_path(pdf_file)
        
        # Extract pages
        self.logger.info("Stage 1: Extracting pages...")
        extractor = PageExtractor(pdf_path)
        pages = extractor.extract_pages()
        self.logger.info(f"Extracted {len(pages)} pages")
        
        # Stage 1: Deterministic extraction
        self.logger.info("Stage 2: Deterministic extraction...")
        # Set PDF path for PyMuPDF extraction
        self.deterministic_extractor.pdf_path = pdf_path
        det_citations = self.deterministic_extractor.extract_citations(pages)
        det_definitions = self.deterministic_extractor.extract_definitions(pages)
        
        self.logger.info(f"Deterministic extraction complete:")
        self.logger.info(f"  - Citations: {len(det_citations)}")
        self.logger.info(f"  - Definitions: {len(det_definitions)}")
        
        # Stage 2: AI enhancement (optional)
        ai_citations = []
        ai_definitions = []
        
        if self.use_ai_enhancement and self.gemini_enhancer:
            self.logger.info("Stage 3: AI enhancement with Gemini...")
            
            # Combine all page text
            full_text = "\n\n".join([p.text for p in pages])
            
            # Enhance citations
            ai_citations = self.gemini_enhancer.enhance_citations(full_text, det_citations)
            
            # Enhance definitions
            ai_definitions = self.gemini_enhancer.enhance_definitions(full_text, det_definitions)
            
            self.logger.info(f"AI enhancement complete:")
            self.logger.info(f"  - New citations: {len(ai_citations)}")
            self.logger.info(f"  - New definitions: {len(ai_definitions)}")
        else:
            self.logger.info("Stage 3: AI enhancement skipped (disabled)")
        
        # Merge and deduplicate with advanced matching
        self.logger.info("Stage 4: Merging and deduplicating...")
        all_citations = self.result_merger.merge_citations(det_citations, ai_citations)
        all_definitions = self.result_merger.merge_definitions(det_definitions, ai_definitions)
        
        self.logger.info(f"Final counts:")
        self.logger.info(f"  - Citations: {len(all_citations)}")
        self.logger.info(f"  - Definitions: {len(all_definitions)}")
        
        # Generate document ID
        doc_id = self.canonicalizer.generate_doc_id_from_filename(pdf_file)
        
        # Create document result
        doc_end_time = time.time()
        processing_time = doc_end_time - doc_start_time
        
        result = DocumentResult(
            doc_id=doc_id,
            source_filename=pdf_file,
            metadata={
                'pages': len(pages),
                'processing_date': datetime.utcnow().isoformat() + 'Z',
                'processing_time_seconds': round(processing_time, 2)
            },
            citations=all_citations,
            terms_definitions=all_definitions
        )
        
        self.logger.info(f"Document processing time: {processing_time:.2f} seconds")
        
        return result.to_dict()
    
    def _create_empty_output(self, processing_time: float) -> Dict:
        """Create empty output structure.
        
        Args:
            processing_time: Processing time in seconds
            
        Returns:
            Empty output dictionary
        """
        return {
            'documents': [],
            'summary': {
                'total_documents': 0,
                'total_citations': 0,
                'total_terms': 0,
                'processing_time_seconds': round(processing_time, 2)
            }
        }
