"""AI-powered extraction using Gemini 2.5 Flash."""
import os
import json
import time
import logging
from typing import List, Dict, Any
import google.generativeai as genai
from models import Page, Citation, Definition
from canonicalizer import Canonicalizer


class GeminiEnhancer:
    """AI-powered extraction using Gemini 2.5 Flash."""
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash-latest", 
                 max_retries: int = 3, chunk_size: int = 3500, chunk_overlap: int = 200):
        """Initialize the Gemini enhancer.
        
        Args:
            api_key: Gemini API key
            model_name: Model name to use
            max_retries: Maximum number of retries for API calls
            chunk_size: Size of text chunks for processing
            chunk_overlap: Overlap between chunks
        """
        self.logger = logging.getLogger(__name__)
        self.max_retries = max_retries
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.canonicalizer = Canonicalizer()
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        
        self.logger.info(f"Initialized Gemini enhancer with model: {model_name}")
    
    def enhance_citations(self, text: str, existing: List[Citation]) -> List[Citation]:
        """Enhance citations using Gemini AI.
        
        Args:
            text: Full document text
            existing: Existing citations from deterministic extraction
            
        Returns:
            List of additional Citation objects
        """
        self.logger.info("Enhancing citations with Gemini AI")
        
        # Create chunks
        chunks = self._create_chunks(text)
        
        # Process each chunk
        all_citations = []
        for i, chunk in enumerate(chunks):
            self.logger.debug(f"Processing citation chunk {i+1}/{len(chunks)}")
            
            citations = self._extract_citations_from_chunk(chunk)
            all_citations.extend(citations)
            
            # Rate limiting
            time.sleep(0.5)
        
        # Filter out duplicates with existing
        existing_texts = {c.text.lower() for c in existing}
        new_citations = [c for c in all_citations if c.text.lower() not in existing_texts]
        
        self.logger.info(f"Gemini found {len(new_citations)} new citations")
        return new_citations
    
    def _extract_citations_from_chunk(self, chunk: str) -> List[Citation]:
        """Extract citations from a text chunk using Gemini."""
        prompt = f"""You are a legal document analyzer. Extract all citations to other laws, decrees, and resolutions from the text below.

Return ONLY a valid JSON array with this structure (no markdown, no explanation):
[{{"text": "exact citation text", "confidence": 0.0-1.0}}]

If no citations found, return: []

Text:
{chunk}"""
        
        for attempt in range(self.max_retries):
            try:
                response = self.model.generate_content(prompt)
                result_text = response.text.strip()
                
                # Clean response
                result_text = self._clean_json_response(result_text)
                
                # Parse JSON
                citations_data = json.loads(result_text)
                
                # Convert to Citation objects
                citations = []
                for item in citations_data:
                    if isinstance(item, dict) and 'text' in item:
                        citation_text = item['text'].strip()
                        confidence = float(item.get('confidence', 0.7))
                        
                        # Generate canonical ID
                        canonical_id = self.canonicalizer.canonicalize_citation(citation_text)
                        
                        citations.append(Citation(
                            text=citation_text,
                            canonical_id=canonical_id,
                            page=0,  # Page unknown from chunk
                            confidence=min(confidence, 0.85),
                            extraction_method="gemini_ai"
                        ))
                
                return citations
                
            except json.JSONDecodeError as e:
                self.logger.warning(f"JSON decode error (attempt {attempt+1}): {e}")
                if attempt == self.max_retries - 1:
                    return []
                time.sleep(2 ** attempt)
            except Exception as e:
                self.logger.error(f"Error extracting citations (attempt {attempt+1}): {e}")
                if attempt == self.max_retries - 1:
                    return []
                time.sleep(2 ** attempt)
        
        return []
    
    def enhance_definitions(self, text: str, existing: List[Definition]) -> List[Definition]:
        """Enhance definitions using Gemini AI.
        
        Args:
            text: Full document text
            existing: Existing definitions from deterministic extraction
            
        Returns:
            List of additional Definition objects
        """
        self.logger.info("Enhancing definitions with Gemini AI")
        
        # Create chunks
        chunks = self._create_chunks(text)
        
        # Process each chunk
        all_definitions = []
        for i, chunk in enumerate(chunks):
            self.logger.debug(f"Processing definition chunk {i+1}/{len(chunks)}")
            
            definitions = self._extract_definitions_from_chunk(chunk)
            all_definitions.extend(definitions)
            
            # Rate limiting
            time.sleep(0.5)
        
        # Filter out duplicates with existing
        existing_terms = {d.term.lower() for d in existing}
        new_definitions = [d for d in all_definitions if d.term.lower() not in existing_terms]
        
        self.logger.info(f"Gemini found {len(new_definitions)} new definitions")
        return new_definitions
    
    def _extract_definitions_from_chunk(self, chunk: str) -> List[Definition]:
        """Extract definitions from a text chunk using Gemini."""
        prompt = f"""Extract term-definition pairs from this legal document section.

Return ONLY a valid JSON array (no markdown, no explanation):
[{{"term": "term name", "definition": "definition text", "confidence": 0.0-1.0}}]

If no definitions found, return: []

Text:
{chunk}"""
        
        for attempt in range(self.max_retries):
            try:
                response = self.model.generate_content(prompt)
                result_text = response.text.strip()
                
                # Clean response
                result_text = self._clean_json_response(result_text)
                
                # Parse JSON
                definitions_data = json.loads(result_text)
                
                # Convert to Definition objects
                definitions = []
                for item in definitions_data:
                    if isinstance(item, dict) and 'term' in item and 'definition' in item:
                        term = self.canonicalizer.normalize_term(item['term'])
                        definition = self.canonicalizer.normalize_definition(item['definition'])
                        confidence = float(item.get('confidence', 0.7))
                        
                        # Validate
                        if len(term) >= 2 and len(definition) >= 10:
                            definitions.append(Definition(
                                term=term,
                                definition=definition,
                                page=0,  # Page unknown from chunk
                                confidence=min(confidence, 0.85),
                                extraction_method="gemini_ai"
                            ))
                
                return definitions
                
            except json.JSONDecodeError as e:
                self.logger.warning(f"JSON decode error (attempt {attempt+1}): {e}")
                if attempt == self.max_retries - 1:
                    return []
                time.sleep(2 ** attempt)
            except Exception as e:
                self.logger.error(f"Error extracting definitions (attempt {attempt+1}): {e}")
                if attempt == self.max_retries - 1:
                    return []
                time.sleep(2 ** attempt)
        
        return []
    
    def batch_process(self, pages: List[Page], task: str) -> List[Dict]:
        """Batch process pages for a specific task.
        
        Args:
            pages: List of Page objects
            task: Task type ('citations' or 'definitions')
            
        Returns:
            List of extracted items as dictionaries
        """
        # Combine all page text
        full_text = "\n\n".join([p.text for p in pages])
        
        if task == 'citations':
            citations = self.enhance_citations(full_text, [])
            return [c.to_dict() for c in citations]
        elif task == 'definitions':
            definitions = self.enhance_definitions(full_text, [])
            return [d.to_dict() for d in definitions]
        else:
            self.logger.error(f"Unknown task: {task}")
            return []
    
    def _create_chunks(self, text: str) -> List[str]:
        """Create overlapping chunks from text.
        
        Args:
            text: Full text to chunk
            
        Returns:
            List of text chunks
        """
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk.rfind('.')
                if last_period > self.chunk_size * 0.7:
                    chunk = chunk[:last_period + 1]
                    end = start + last_period + 1
            
            chunks.append(chunk)
            
            # Move start with overlap
            start = end - self.chunk_overlap
            
            if end >= len(text):
                break
        
        self.logger.debug(f"Created {len(chunks)} chunks from text of length {len(text)}")
        return chunks
    
    def _clean_json_response(self, text: str) -> str:
        """Clean JSON response from Gemini.
        
        Args:
            text: Raw response text
            
        Returns:
            Cleaned JSON string
        """
        # Remove markdown code blocks
        text = text.replace('```json', '').replace('```', '')
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # If response contains explanation, try to extract JSON array
        if not text.startswith('['):
            # Look for JSON array
            start = text.find('[')
            end = text.rfind(']')
            if start != -1 and end != -1:
                text = text[start:end+1]
        
        return text
