"""AI enhancement using Groq API with llama-3.1-8b-instant."""
import os
import logging
import time
from typing import List
from groq import Groq
from models import Page, Citation, Definition
from canonicalizer import Canonicalizer


class GroqEnhancer:
    """AI-powered enhancement using Groq API."""
    
    def __init__(self, api_key: str = None):
        """Initialize Groq enhancer.
        
        Args:
            api_key: Groq API key (defaults to env variable)
        """
        self.logger = logging.getLogger(__name__)
        
        # Get API key
        self.api_key = api_key or os.getenv('GROQ_API_KEY')
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment")
        
        # Initialize Groq client (simple initialization)
        from groq import Groq as GroqClient
        self.client = GroqClient(api_key=self.api_key)
        self.model = "llama-3.1-8b-instant"
        
        self.canonicalizer = Canonicalizer()
        self.logger.info(f"Initialized Groq enhancer with model: {self.model}")
    
    def enhance_citations(self, pages: List[Page], existing_citations: List[Citation]) -> List[Citation]:
        """Enhance citations using Groq AI.
        
        Args:
            pages: List of Page objects
            existing_citations: Citations from deterministic extraction
            
        Returns:
            Enhanced list of citations
        """
        self.logger.info("Enhancing citations with Groq AI...")
        
        # Combine all page text
        full_text = "\n\n".join([f"=== Page {p.page_num} ===\n{p.text}" for p in pages[:10]])  # First 10 pages
        
        # Create prompt
        prompt = f"""You are a legal document analyzer. Extract ALL legal citations from this UAE legal document.

A citation is a reference to another law, decree, resolution, or regulation. Examples:
- Federal Decree-Law No. (28) of 2022 on Tax Procedures
- Cabinet Resolution No. (74) of 2023
- Federal Law No. (7) of 2017

Document text:
{full_text[:15000]}  # Limit to 15k chars

Extract ALL citations. For each citation, provide:
1. The exact text of the citation
2. The page number where it appears

Format your response as JSON:
{{
  "citations": [
    {{"text": "Federal Decree-Law No. (28) of 2022 on Tax Procedures", "page": 1}},
    {{"text": "Cabinet Resolution No. (74) of 2023", "page": 2}}
  ]
}}

IMPORTANT: Only extract actual citations to other laws/decrees/resolutions. Do not extract article numbers or section references."""
        
        try:
            # Call Groq API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a legal document analyzer specializing in UAE law."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            # Parse response
            import json
            response_text = response.choices[0].message.content
            
            # Extract JSON from response
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            data = json.loads(response_text.strip())
            
            # Convert to Citation objects
            ai_citations = []
            for item in data.get('citations', []):
                text = item.get('text', '').strip()
                page = item.get('page', 1)
                
                if text and len(text) > 20:  # Valid citation
                    canonical_id = self.canonicalizer.canonicalize_citation(text)
                    ai_citations.append(Citation(
                        text=text,
                        canonical_id=canonical_id,
                        page=page,
                        confidence=0.75,
                        extraction_method="groq_ai"
                    ))
            
            # Merge with existing citations
            all_citations = existing_citations + ai_citations
            
            # Deduplicate by canonical_id
            seen = set()
            unique_citations = []
            for c in all_citations:
                if c.canonical_id not in seen:
                    seen.add(c.canonical_id)
                    unique_citations.append(c)
            
            self.logger.info(f"AI found {len(ai_citations)} new citations")
            self.logger.info(f"Total after merge: {len(unique_citations)} citations")
            
            return unique_citations
            
        except Exception as e:
            self.logger.error(f"Groq API error: {e}")
            self.logger.info("Returning original citations")
            return existing_citations
    
    def enhance_definitions(self, pages: List[Page], existing_definitions: List[Definition]) -> List[Definition]:
        """Enhance definitions using Groq AI.
        
        Args:
            pages: List of Page objects
            existing_definitions: Definitions from deterministic extraction
            
        Returns:
            Enhanced list of definitions
        """
        self.logger.info("Enhancing definitions with Groq AI...")
        
        # Find definitions section
        def_section_text = ""
        for page in pages[:10]:  # Check first 10 pages
            if any(keyword in page.text.lower() for keyword in ['definitions', 'article 1', 'article (1)']):
                def_section_text += f"\n\n=== Page {page.page_num} ===\n{page.text}"
        
        if not def_section_text:
            self.logger.info("No definitions section found, using existing definitions")
            return existing_definitions
        
        # Create prompt
        prompt = f"""You are a legal document analyzer. Extract ALL term-definition pairs from this definitions section.

A term-definition pair consists of:
- Term: A legal term or concept (e.g., "Authority", "Tax Period", "Taxable Person")
- Definition: The explanation of what the term means

Definitions section:
{def_section_text[:15000]}  # Limit to 15k chars

Extract ALL term-definition pairs. For each pair, provide:
1. The term
2. The definition
3. The page number

Format your response as JSON:
{{
  "definitions": [
    {{"term": "Authority", "definition": "The Federal Tax Authority.", "page": 1}},
    {{"term": "Tax Period", "definition": "A specific period for which the payable tax shall be calculated.", "page": 1}}
  ]
}}

IMPORTANT: Only extract actual term-definition pairs from the definitions section. Do not extract article text or preamble."""
        
        try:
            # Call Groq API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a legal document analyzer specializing in UAE law."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=3000
            )
            
            # Parse response
            import json
            response_text = response.choices[0].message.content
            
            # Extract JSON from response
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            data = json.loads(response_text.strip())
            
            # Convert to Definition objects
            ai_definitions = []
            for item in data.get('definitions', []):
                term = item.get('term', '').strip()
                definition = item.get('definition', '').strip()
                page = item.get('page', 1)
                
                if term and definition and len(term) > 1 and len(definition) > 5:
                    # Normalize
                    term = self.canonicalizer.normalize_term(term)
                    definition = self.canonicalizer.normalize_definition(definition)
                    
                    ai_definitions.append(Definition(
                        term=term,
                        definition=definition,
                        page=page,
                        confidence=0.75,
                        extraction_method="groq_ai"
                    ))
            
            # Merge with existing definitions
            all_definitions = existing_definitions + ai_definitions
            
            # Deduplicate by term (case-insensitive)
            seen = set()
            unique_definitions = []
            for d in all_definitions:
                term_lower = d.term.lower()
                if term_lower not in seen:
                    seen.add(term_lower)
                    unique_definitions.append(d)
            
            self.logger.info(f"AI found {len(ai_definitions)} new definitions")
            self.logger.info(f"Total after merge: {len(unique_definitions)} definitions")
            
            return unique_definitions
            
        except Exception as e:
            self.logger.error(f"Groq API error: {e}")
            self.logger.info("Returning original definitions")
            return existing_definitions
