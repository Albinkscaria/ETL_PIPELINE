"""Rule-based extraction using regex and layout."""
import re
import logging
from typing import List, Optional, Tuple
from models import Page, Citation, Definition
from canonicalizer import Canonicalizer


class DeterministicExtractor:
    """Rule-based extraction using regex and layout."""
    
    def __init__(self, pdf_path: Optional[str] = None):
        """Initialize the deterministic extractor.
        
        Args:
            pdf_path: Optional path to PDF file (needed for PyMuPDF extraction)
        """
        self.logger = logging.getLogger(__name__)
        self.canonicalizer = Canonicalizer()
        self.pdf_path = pdf_path
        
        # Citation patterns - Enhanced for maximum recall
        self.citation_patterns = [
            # Federal Decree-Law variations (with and without "by")
            r'Federal Decree[- ]?Law No\.?\s*\(?\d+\)?\s+of\s+\d{4}[^.;]*',
            r'Federal Decree[- ]?Law\s+\(?\d+\)?\s+of\s+\d{4}[^.;]*',
            r'Federal Decree by Law No\.?\s*\(?\d+\)?\s+of\s+\d{4}[^.;]*',
            r'Federal Decree by Law\s+\(?\d+\)?\s+of\s+\d{4}[^.;]*',
            
            # Cabinet Resolution variations
            r'Cabinet Resolution No\.?\s*\(?\d+\)?\s+of\s+\d{4}[^.;]*',
            r'Cabinet Resolution\s+\(?\d+\)?\s+of\s+\d{4}[^.;]*',
            
            # Federal Law variations (including "Issuing", "Promulgating")
            r'Federal Law No\.?\s*\(?\d+\)?\s+of\s+\d{4}[^.;]*',
            r'Federal Law\s+\(?\d+\)?\s+of\s+\d{4}[^.;]*',
            r'Federal Law No\.?\s*\(?\d+\)?\s+Issuing[^.;]*',
            r'Federal Law No\.?\s*\(?\d+\)?\s+Promulgating[^.;]*',
            
            # Ministerial variations
            r'Ministerial Resolution No\.?\s*\(?\d+\)?\s+of\s+\d{4}[^.;]*',
            r'Ministerial Decision No\.?\s*\(?\d+\)?\s+of\s+\d{4}[^.;]*',
            
            # With "as amended" suffix
            r'Federal Decree[- ]?Law No\.?\s*\(?\d+\)?\s+of\s+\d{4},?\s+as\s+amended',
            r'Federal Decree by Law No\.?\s*\(?\d+\)?\s+of\s+\d{4},?\s+as\s+amended',
            r'Cabinet Resolution No\.?\s*\(?\d+\)?\s+of\s+\d{4},?\s+as\s+amended',
            r'Federal Law No\.?\s*\(?\d+\)?\s+of\s+\d{4},?\s+as\s+amended',
            
            # Bullet point format (common in legal docs)
            r'[−–—•]\s*Federal Decree[- ]?Law No\.?\s*\(?\d+\)?\s+of\s+\d{4}[^.;]*',
            r'[−–—•]\s*Federal Decree by Law No\.?\s*\(?\d+\)?\s+of\s+\d{4}[^.;]*',
            r'[−–—•]\s*Cabinet Resolution No\.?\s*\(?\d+\)?\s+of\s+\d{4}[^.;]*',
            r'[−–—•]\s*Federal Law No\.?\s*\(?\d+\)?\s+of\s+\d{4}[^.;]*',
            
            # Abbreviated formats (Decree-Law, Dec-Law)
            r'Decree[- ]?Law No\.?\s*\(?\d+\)?\s+of\s+\d{4}[^.;]*',
            
            # With "Regarding", "Concerning", "on" in title
            r'Federal Decree[- ]?Law No\.?\s*\(?\d+\)?\s+of\s+\d{4}\s+(Regarding|Concerning|on)[^.;]*',
            r'Cabinet Resolution No\.?\s*\(?\d+\)?\s+of\s+\d{4}\s+(Regarding|Concerning|on)[^.;]*',
        ]
        
        # Definition section patterns - Enhanced for maximum recall
        self.definition_section_patterns = [
            # Article 1 variations (most common)
            r'Article\s*\(?\s*1\s*\)?\s*[–-—:]*\s*Definitions',
            r'Article\s+One\s*[–-—:]*\s*Definitions',
            r'ARTICLE\s*\(?\s*1\s*\)?\s*[–-—:]*\s*DEFINITIONS',
            r'Article\s*\(?\s*1\s*\)?\s*[–-—:]*\s*DEFINITIONS',
            r'Article\s*\(?\s*1\s*\)?\s*[–-—:]*\s*Definition',  # Singular
            
            # Alternative section headers
            r'Definitions?\s*and\s*Interpretations?',
            r'DEFINITIONS?\s*AND\s*INTERPRETATIONS?',
            r'Meaning\s+of\s+Terms',
            r'MEANING\s+OF\s+TERMS',
            r'Interpretation\s+of\s+Terms',
            r'INTERPRETATION\s+OF\s+TERMS',
            r'Interpretation\s+and\s+Application',
            r'INTERPRETATION\s+AND\s+APPLICATION',
            
            # Chapter-based
            r'Chapter\s+\d+\s*[–-—:]*\s*Definitions',
            r'CHAPTER\s+\d+\s*[–-—:]*\s*DEFINITIONS',
            r'Chapter\s+One\s*[–-—:]*\s*Definitions',
            
            # Section-based
            r'Section\s+\d+\s*[–-—:]*\s*Definitions',
            r'SECTION\s+\d+\s*[–-—:]*\s*DEFINITIONS',
            
            # Part-based
            r'Part\s+One\s*[–-—:]*\s*Definitions',
            r'PART\s+ONE\s*[–-—:]*\s*DEFINITIONS',
            
            # Just "Definitions" header (standalone)
            r'\n\s*Definitions\s*\n',
            r'\n\s*DEFINITIONS\s*\n',
            
            # With "For the purpose of"
            r'For\s+the\s+purpose[s]?\s+of\s+this\s+(Law|Decree|Resolution)[,:]?\s+the\s+following',
            r'For\s+the\s+purposes\s+of\s+applying\s+the\s+provisions',
        ]
        
        # Term-definition patterns - FIXED: Handles multi-line terms with flexible whitespace
        # Pattern: Term can span multiple lines, then colon (with REQUIRED spaces before it), then definition
        # IMPORTANT: Colon must have spaces before it to be a true term-definition pair
        self.term_def_patterns = [
            # PRIMARY PATTERN: Multi-line Term  : Definition
            # Handles: "Government\nAuthorities  :" or "Real Estate Investment Trust (REIT)  :"
            # REQUIRES at least one space before colon (not "Cabinet:" but "Authority  :")
            # Updated to capture complete multi-line definitions and terms with parentheses
            r'([A-Z][A-Za-z\s&\(\),"\']+(?:\n[A-Za-z\s&\(\),"\']+)*?)\s+[:–—]\s*(.+?)(?=\n\s*[A-Z][A-Za-z\s&\(\),"\']+\s+[:–—]|\n\s*Article\s+\(|\Z)',
            
            # "means" variations (very common) - capture complete definitions
            r'([A-Z][A-Za-z\s&\(\)"\']+?)\s+means\s+(.+?)(?=\n\s*[A-Z][A-Za-z\s&\(\)"\']+?\s+means|\n\s*Article\s+\(|\n\n\n|\Z)',
            r'([A-Z][A-Za-z\s&\(\)"\']+?)\s+shall mean\s+(.+?)(?=\n\s*[A-Z][A-Za-z\s&\(\)"\']+?\s+shall mean|\n\s*Article\s+\(|\n\n\n|\Z)',
            
            # Quoted terms (common in some docs) - also require space before colon
            r'"([^"]+)"\s+[:–—]\s*(.+?)(?=\n\s*"[^"]+"\s+[:–—]|\n\s*Article\s+\(|\n\n\n|\Z)',
            r'"([^"]+)"\s+means\s+(.+?)(?=\n\s*"[^"]+"\s+means|\n\s*Article\s+\(|\n\n\n|\Z)',
            
            # "refers to" / "is defined as"
            r'([A-Z][A-Za-z\s&\(\)"\']+?)\s+refers to\s+(.+?)(?=\n\s*[A-Z][A-Za-z\s&\(\)"\']+?\s+refers to|\n\s*Article\s+\(|\n\n\n|\Z)',
            r'([A-Z][A-Za-z\s&\(\)"\']+?)\s+is defined as\s+(.+?)(?=\n\s*[A-Z][A-Za-z\s&\(\)"\']+?\s+is defined as|\n\s*Article\s+\(|\n\n\n|\Z)',
        ]
    
    def extract_citations(self, pages: List[Page]) -> List[Citation]:
        """Extract citations using regex patterns.
        
        Args:
            pages: List of Page objects
            
        Returns:
            List of Citation objects
        """
        citations = []
        
        # Detect document title from first page (header/self-reference)
        document_title = self._extract_document_title(pages)
        
        for page in pages:
            text = page.text
            
            # Remove header and footer from text
            text = self._remove_headers_footers(text, page.page_num)
            
            for pattern in self.citation_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
                
                for match in matches:
                    citation_text = match.group(0).strip()
                    
                    # Clean up citation text
                    citation_text = self._clean_citation_text(citation_text)
                    
                    # Skip if too short or too long
                    if len(citation_text) < 20 or len(citation_text) > 200:
                        continue
                    
                    # Skip if this is the document title (self-reference/header)
                    if self._is_document_title(citation_text, document_title):
                        self.logger.debug(f"Skipping document title/header: {citation_text[:80]}...")
                        continue
                    
                    # Skip if this looks like a header (starts at beginning of page)
                    if self._is_header_citation(citation_text, text):
                        self.logger.debug(f"Skipping header citation: {citation_text[:80]}...")
                        continue
                    
                    # Generate canonical ID
                    canonical_id = self.canonicalizer.canonicalize_citation(citation_text)
                    
                    # Calculate confidence based on pattern strength
                    confidence = self._calculate_citation_confidence(citation_text)
                    
                    citations.append(Citation(
                        text=citation_text,
                        canonical_id=canonical_id,
                        page=page.page_num,
                        confidence=confidence,
                        extraction_method="regex"
                    ))
        
        self.logger.info(f"Extracted {len(citations)} citations using regex")
        return citations
    
    def _extract_document_title(self, pages: List[Page]) -> str:
        """Extract document title from first page.
        
        Args:
            pages: List of Page objects
            
        Returns:
            Document title (first 3 lines typically)
        """
        if not pages:
            return ""
        
        first_page_text = pages[0].text
        lines = first_page_text.split('\n')
        
        # Title is typically in first 3-5 lines
        title_lines = []
        for line in lines[:5]:
            line = line.strip()
            if line and not line.startswith('−') and not line.startswith('•'):
                title_lines.append(line)
                if len(title_lines) >= 3:
                    break
        
        return ' '.join(title_lines)
    
    def _is_document_title(self, citation_text: str, document_title: str) -> bool:
        """Check if citation is actually the document title.
        
        Args:
            citation_text: Citation text to check
            document_title: Document title from first page
            
        Returns:
            True if citation is the document title
        """
        if not document_title:
            return False
        
        # Extract key parts from both
        citation_lower = citation_text.lower()
        title_lower = document_title.lower()
        
        # Check if citation text is contained in title (or vice versa)
        # This catches cases where the citation is the document referring to itself
        if len(citation_text) > 50:  # Only check longer citations
            # Extract number and year from citation
            cit_match = re.search(r'no\.?\s*\(?\d+\)?\s+of\s+\d{4}', citation_lower)
            title_match = re.search(r'no\.?\s*\(?\d+\)?\s+of\s+\d{4}', title_lower)
            
            if cit_match and title_match:
                # If both have same number and year, likely same document
                if cit_match.group(0) == title_match.group(0):
                    return True
        
        return False
    
    def _is_header_citation(self, citation_text: str, page_text: str) -> bool:
        """Check if citation appears to be from a header.
        
        Args:
            citation_text: Citation text to check
            page_text: Full page text
            
        Returns:
            True if citation is likely from header
        """
        # Headers are typically in first 200 characters of page
        # and are NOT preceded by bullet points or "Having reviewed"
        
        citation_pos = page_text.find(citation_text)
        if citation_pos < 0:
            return False
        
        # If citation is in first 200 chars and not preceded by bullet/dash
        if citation_pos < 200:
            # Check what comes before
            before_text = page_text[:citation_pos].strip()
            
            # If nothing before, or only title-like text, it's a header
            if not before_text or len(before_text) < 50:
                return True
            
            # If preceded by "The Cabinet:" or similar, it's NOT a header (it's in preamble)
            if before_text.endswith(('The Cabinet:', 'We,', 'Having reviewed')):
                return False
        
        return False
    
    def _remove_headers_footers(self, text: str, page_num: int) -> str:
        """Remove headers and footers from page text.
        
        Args:
            text: Page text
            page_num: Page number
            
        Returns:
            Text with headers/footers removed
        """
        lines = text.split('\n')
        
        if len(lines) < 10:
            return text  # Too short to have meaningful headers/footers
        
        # Remove first 2 lines if they look like headers (short, no punctuation)
        cleaned_lines = []
        start_idx = 0
        
        for i, line in enumerate(lines[:3]):
            line_stripped = line.strip()
            # Skip if line is short and looks like a title/header
            if len(line_stripped) < 80 and not line_stripped.endswith(('.', ';', ':')):
                start_idx = i + 1
            else:
                break
        
        # Remove last 3 lines if they look like footers (page numbers, repeated text)
        end_idx = len(lines)
        for i in range(len(lines) - 1, max(len(lines) - 4, 0), -1):
            line_stripped = lines[i].strip()
            # Skip if line is just a number (page number) or very short
            if line_stripped.isdigit() or len(line_stripped) < 10:
                end_idx = i
            else:
                break
        
        cleaned_lines = lines[start_idx:end_idx]
        return '\n'.join(cleaned_lines)
    
    def _remove_footer_from_definition(self, definition: str) -> str:
        """Remove footer text that may have been captured in definition.
        
        Args:
            definition: Definition text
            
        Returns:
            Definition with footer text removed
        """
        # Common footer patterns that appear in definitions
        # These are document titles that appear at the bottom of pages
        footer_patterns = [
            r'\s+Federal Decree-Law of \d{4} [Oo]n .+\.\s*$',  # "Federal Decree-Law of 2022 on Tax Procedures."
            r'\s+Federal Decree-Law of \d{4} [Oo]n .+$',   # Same without period
            r'\s+Federal Decree of \d{4} [Oo]n .+\.\s*$',
            r'\s+Federal Decree of \d{4} [Oo]n .+$',
            r'\s+Cabinet Resolution of \d{4} [Rr]egarding .+\.\s*$',  # "Cabinet Resolution of 2025 Regarding..."
            r'\s+Cabinet Resolution of \d{4} [Rr]egarding .+$',
            r'\s+Federal Decree-Law of \d{4} On .+\.\s*$',  # Capital O
            r'\s+Federal Decree-Law of \d{4} On .+$',
        ]
        
        cleaned = definition
        
        for pattern in footer_patterns:
            # Find and remove footer text
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Also remove if definition ends with document title pattern + page number
        # Example: "...Federal Decree-Law of 2022 on Tax Procedures 5"
        cleaned = re.sub(r'\s+Federal Decree[- ]?Law of \d{4}[^.]*\d+\s*$', '', cleaned)
        cleaned = re.sub(r'\s+Cabinet Resolution of \d{4}[^.]*\d+\s*$', '', cleaned)
        
        # Remove trailing "Federal Decree-Law of 2022 On..." patterns (capital O)
        cleaned = re.sub(r'\s+Federal Decree-Law of \d{4} On [A-Z][^.]*$', '', cleaned)
        
        return cleaned.strip()
    
    def _clean_citation_text(self, text: str) -> str:
        """Clean citation text."""
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove leading bullet points or dashes
        text = re.sub(r'^[−–—•]\s*', '', text)
        
        # Remove trailing punctuation except periods
        text = text.rstrip(',;:')
        
        # Remove trailing "and" or semicolons
        text = re.sub(r';\s*and\s*$', '', text, flags=re.IGNORECASE)
        text = re.sub(r';\s*$', '', text)
        
        # Normalize spaces around "No."
        text = re.sub(r'No\.\s*\(', 'No. (', text)
        text = re.sub(r'\)\s*of\s*', ') of ', text)
        
        return text
    
    def _calculate_citation_confidence(self, text: str) -> float:
        """Calculate confidence score for citation."""
        confidence = 0.85  # Base confidence for regex match
        
        # Increase confidence if has number in parentheses
        if re.search(r'\(\d+\)', text):
            confidence += 0.05
        
        # Increase confidence if has year
        if re.search(r'\d{4}', text):
            confidence += 0.05
        
        # Increase confidence if has "concerning" or "on"
        if re.search(r'concerning|on|regarding', text, re.IGNORECASE):
            confidence += 0.05
        
        return min(confidence, 1.0)
    
    def _is_valid_term_definition(self, term: str, definition: str) -> bool:
        """Structural validation to reject garbage term-definition extractions.
        
        Instead of maintaining endless pattern lists, this uses STRUCTURAL rules:
        1. Valid terms are NOUN PHRASES (not sentences)
        2. Valid terms have specific grammatical structure
        3. Valid terms don't have sentence-like characteristics
        
        This approach scales to ANY garbage pattern without adding new rules.
        
        Args:
            term: Term text
            definition: Definition text
            
        Returns:
            True if valid, False if garbage/invalid
        """
        # 1. Basic length checks
        if len(term) < 2 or len(definition) < 5:
            return False
        
        # 2. Term too long (likely captured sentence)
        MAX_TERM_LENGTH = 60
        if len(term) > MAX_TERM_LENGTH:
            self.logger.debug(f"Rejecting term (too long): {term[:80]}")
            return False
        
        # 3. Definition too long (likely captured too much)
        if len(definition) > 2000:
            return False
        
        # === STRUCTURAL VALIDATION (scales to any garbage) ===
        
        # 4. Check if term is a NOUN PHRASE (not a sentence)
        # This single check replaces 15+ pattern checks and scales to ANY garbage
        if not self._is_noun_phrase(term):
            self.logger.debug(f"Rejecting term (not a noun phrase): {term[:80]}")
            return False
        
        # 5. Definition validation (check if definition is valid)
        if not self._is_valid_definition(definition):
            self.logger.debug(f"Rejecting definition (invalid): {definition[:80]}")
            return False
        
        return True
    
    def _is_valid_definition(self, definition: str) -> bool:
        """Check if definition is valid (not preamble or citation).
        
        Args:
            definition: Definition text
            
        Returns:
            True if valid definition, False if invalid
        """
        # Reject if definition starts with preamble words
        if re.match(r'^(Having reviewed|And based on|Hereby resolves|The Cabinet|Upon the proposal)', definition, re.IGNORECASE):
            return False
        
        # Reject if definition is just a reference to another article
        if re.match(r'^(Article|Chapter|Section)\s+\d+', definition, re.IGNORECASE):
            return False
        
        # Reject if definition looks like a citation (not a definition)
        if re.match(r'^(Cabinet Resolution|Federal Decree|Federal Law)', definition, re.IGNORECASE):
            return False
        
        return True
    
    def _is_noun_phrase(self, term: str) -> bool:
        """Check if term is a valid noun phrase (not a sentence).
        
        Valid noun phrases:
        - Start with capital letter or article + capital
        - Don't contain verbs in -ing form at start (Notifying, Providing)
        - Don't contain sentence connectors (whereas, therefore, however)
        - Don't contain preposition chains (of the, to the, by the)
        - Don't contain modal verbs (shall, must, may, should)
        
        This catches ANY sentence-like pattern without listing every word.
        
        Args:
            term: Term text
            
        Returns:
            True if valid noun phrase, False if sentence-like
        """
        term_lower = term.lower()
        words = term.split()
        
        if not words:
            return False
        
        first_word = words[0].lower()
        
        # Rule 1: Reject if starts with sentence connectors
        # These words NEVER start noun phrases, always start sentences
        sentence_starters = {
            'whereas', 'therefore', 'however', 'moreover', 'furthermore',
            'nevertheless', 'accordingly', 'consequently', 'hence', 'thus',
            'when', 'where', 'while', 'although', 'though', 'unless',
            'if', 'because', 'since', 'as', 'after', 'before', 'until'
        }
        if first_word in sentence_starters:
            return False
        
        # Rule 2: Reject if starts with verb in -ing form (gerund at sentence start)
        # "Notifying the person..." is a sentence, not a term
        # But "Licensing Authority" is OK (noun, not verb)
        if first_word.endswith('ing') and len(first_word) > 6:
            # Check if it's a common verb-ing (not noun-ing)
            verb_ings = {
                'notifying', 'providing', 'submitting', 'issuing', 'establishing',
                'creating', 'forming', 'making', 'taking', 'giving', 'receiving',
                'sending', 'filing', 'requesting', 'requiring', 'ensuring',
                'determining', 'calculating', 'processing', 'reviewing', 'approving'
            }
            if first_word in verb_ings:
                return False
        
        # Rule 2b: Reject single-word determiners (not noun phrases)
        # "The", "Any", "All" alone are NOT terms
        if len(words) == 1 and first_word in ['the', 'any', 'all', 'each', 'every', 'some']:
            return False
        
        # Rule 2c: Reject two-word determiner phrases
        # "Any other", "The following", "All such" are NOT terms
        if len(words) == 2:
            second_word = words[1].lower()
            if first_word in ['the', 'any', 'all', 'each', 'every', 'some']:
                if second_word in ['other', 'following', 'such', 'said', 'aforementioned']:
                    return False
        
        # Rule 3: Reject if starts with determiners that indicate sentence fragments
        # "The person shall..." vs "The Authority" (OK)
        # Check if followed by common nouns (indicates fragment)
        if first_word in ['the', 'any', 'all', 'each', 'every', 'some']:
            if len(words) > 1:
                second_word = words[1].lower()
                # If followed by common verbs or prepositions, it's a fragment
                if second_word in ['person', 'persons', 'authority', 'authorities'] and len(words) > 3:
                    # "The person of the..." is fragment
                    # "The Authority" is OK
                    if ' of ' in term_lower or ' to ' in term_lower or ' by ' in term_lower:
                        return False
        
        # Rule 4: Reject if contains preposition chains (sentence fragments)
        # "Registration of the Recipient of such Goods by the Authority"
        # Count prepositions - too many = sentence fragment
        prepositions = ['of the', 'to the', 'by the', 'for the', 'in the', 'on the', 'at the']
        prep_count = sum(1 for prep in prepositions if prep in term_lower)
        if prep_count >= 2:  # Multiple preposition chains = fragment
            return False
        
        # Rule 5: Reject if contains modal verbs (sentence characteristic)
        # "Article shall" - modal verb indicates sentence
        modals = [' shall ', ' must ', ' may ', ' should ', ' would ', ' could ', ' will ']
        if any(modal in term_lower for modal in modals):
            return False
        
        # Rule 6: Reject if contains conjunctions in middle (sentence characteristic)
        # "Corporations and Businesses; and" - conjunction + semicolon = list item
        if '; and' in term_lower or ';and' in term_lower:
            return False
        
        # Rule 7: Reject if ends with sentence-like patterns
        # "as follows", "otherwise", "the following" - these end sentences
        # Also reject if ends with preposition (incomplete phrase)
        sentence_endings = ['as follows', 'otherwise', 'the following', 'shall be', 'as amended']
        if any(term_lower.endswith(ending) for ending in sentence_endings):
            return False
        
        # Reject if ends with preposition (incomplete phrase)
        # "Goods and services related to the supply of" - ends with "of"
        preposition_endings = [' of', ' to', ' by', ' for', ' in', ' on', ' at', ' with', ' from']
        if any(term_lower.endswith(ending) for ending in preposition_endings):
            return False
        
        # Rule 8: Reject if contains document structure keywords
        # "Article (1)", "Chapter 2", "Section 3" - these are structure, not terms
        # Also reject "Article shall" - article text, not a term
        if re.search(r'\b(article|chapter|section|part|clause|paragraph)\s*\(?\d+\)?', term_lower):
            return False
        if re.search(r'\barticle\s+(shall|must|may|should|will)', term_lower):
            return False
        
        # Rule 9: Reject if term is just a generic document word
        generic_words = {
            'article', 'chapter', 'section', 'part', 'clause', 'paragraph',
            'procedures', 'regulations', 'resolution', 'decree', 'law',
            'cabinet', 'constitution'
        }
        if term_lower in generic_words:
            return False
        
        # Rule 10: Reject if contains incomplete abbreviations
        # "MOA of the Company" - abbreviation + preposition = fragment
        if re.search(r'\b(moa|aoa)\s+of\s+the\b', term_lower):
            return False
        
        # Rule 11: Reject very short terms (likely fragments from hyphenation)
        # "er", "tion", "sure", "ment" - these are broken words
        if len(term) <= 4 and term.islower():
            return False
        
        # Rule 12: Reject if term is ALL lowercase (not a proper noun)
        # Proper terms should start with capital: "Authority", "Tax Period"
        # All lowercase = fragment: "er", "tion", "sure"
        if term.islower():
            return False
        
        # Rule 13: Reject if term ends with incomplete phrase markers
        # "Maintenance services provided for the" - ends with "the"
        # "Conversion services provided for the" - ends with "the"
        incomplete_endings = [' the', ' a', ' an', ' this', ' that', ' these', ' those']
        if any(term_lower.endswith(ending) for ending in incomplete_endings):
            return False
        
        # Rule 14: Reject if term contains "provided for the" (incomplete phrase)
        if 'provided for the' in term_lower and not term_lower.endswith('provided for the'):
            # If it contains this phrase but doesn't end with it, still reject
            # because it's likely an incomplete extraction
            pass
        if term_lower.endswith('provided for the'):
            return False
        
        # Rule 15: Reject if term is just a number or contains only numbers
        if term.replace(' ', '').replace('(', '').replace(')', '').isdigit():
            return False
        
        # Rule 16: Reject if term contains lowercase words at the end (incomplete)
        # "Assets held on capital account" is OK (all words meaningful)
        # "Authorities on Tax Disputes Objection" is OK
        # But "Maintenance services provided for the" is NOT (ends with "the")
        words_list = term.split()
        if len(words_list) > 1:
            last_word = words_list[-1].lower()
            # If last word is a common article/preposition/conjunction, reject
            if last_word in ['the', 'a', 'an', 'of', 'to', 'for', 'in', 'on', 'at', 'by', 'with', 'from', 'and', 'or']:
                return False
        
        # Rule 17: Reject specific problematic compound terms from PDF layout issues
        # These are terms that got merged due to PDF formatting
        problematic_compounds = [
            'Fine Assessment Stockpiler',  # Should be just "Stockpiler"
            'Fine Assessment',  # This is not a standalone term
            'Number (TRN)',  # Should be "Tax Registration Number (TRN)"
        ]
        if term in problematic_compounds:
            return False
        
        # Rule 18: Reject standalone "Administrative" (should be "Administrative Fines" or "Administrative Fine Assessment")
        if term == 'Administrative':
            return False
        
        # Rule 19: Reject if term contains "Assessment" + another capitalized word (likely compound error)
        # "Fine Assessment Stockpiler" - "Assessment" + "Stockpiler" = compound error
        if 'Assessment' in term and len(words_list) > 2:
            # Check if it's a valid term like "Tax Assessment" (2 words OK)
            # But "Fine Assessment Stockpiler" (3+ words with Assessment) is suspicious
            if words_list.count('Assessment') > 0:
                assessment_idx = words_list.index('Assessment')
                if assessment_idx < len(words_list) - 1:
                    # There's a word after "Assessment"
                    next_word = words_list[assessment_idx + 1]
                    # If next word is capitalized and not a common continuation, reject
                    if next_word[0].isupper() and next_word not in ['Number', 'Date', 'Period', 'Amount']:
                        return False
        
        return True
    
    def extract_definitions(self, pages: List[Page]) -> List[Definition]:
        """Extract term-definition pairs.
        
        Args:
            pages: List of Page objects
            
        Returns:
            List of Definition objects
        """
        definitions = []
        
        # Find ALL pages with definitions (not just the first one)
        def_section_pages = self.find_all_definitions_sections(pages)
        
        if def_section_pages:
            # Use PyMuPDF for each definitions section (better multi-line handling)
            if self.pdf_path:
                for start_page in def_section_pages:
                    definitions.extend(self._extract_from_definitions_section_pymupdf(pages, start_page))
            else:
                # Fallback to regular extraction if no PDF path
                for start_page in def_section_pages:
                    definitions.extend(self._extract_from_definitions_section(pages, start_page))
        
        # Also try to extract from entire document
        definitions.extend(self._extract_definitions_general(pages))
        
        self.logger.info(f"Extracted {len(definitions)} definitions using regex")
        return definitions
    
    def find_all_definitions_sections(self, pages: List[Page]) -> List[int]:
        """Find ALL pages containing definitions sections.
        
        Args:
            pages: List of Page objects
            
        Returns:
            List of page numbers (1-indexed) with definitions
        """
        definition_pages = []
        
        # Look for explicit definition section headers
        for page in pages[:15]:  # Check first 15 pages
            for pattern in self.definition_section_patterns:
                if re.search(pattern, page.text, re.IGNORECASE):
                    if page.page_num not in definition_pages:
                        self.logger.info(f"Found definitions section on page {page.page_num} using pattern")
                        definition_pages.append(page.page_num)
                    break
        
        # Also look for pages with high density of "means" or colon patterns
        for page in pages[:15]:
            if page.page_num in definition_pages:
                continue  # Skip if already found
                
            means_count = len(re.findall(r'\b[A-Z][A-Za-z\s]{2,40}\s+means\s+', page.text))
            colon_count = len(re.findall(r'\b[A-Z][A-Za-z\s]{2,40}\s*:\s*[A-Z]', page.text))
            
            # If page has 3+ definition-like patterns, treat it as definitions section
            if means_count >= 3 or colon_count >= 5:
                self.logger.info(f"Found likely definitions section on page {page.page_num} (means={means_count}, colon={colon_count})")
                definition_pages.append(page.page_num)
        
        return sorted(definition_pages)
    
    def find_definitions_section(self, pages: List[Page]) -> Optional[int]:
        """Find the page containing the definitions section.
        
        Args:
            pages: List of Page objects
            
        Returns:
            Page number (1-indexed) or None
        """
        # First try: Look for explicit definition section headers
        for page in pages[:15]:  # Check first 15 pages (increased from 10)
            for pattern in self.definition_section_patterns:
                if re.search(pattern, page.text, re.IGNORECASE):
                    self.logger.info(f"Found definitions section on page {page.page_num} using pattern")
                    return page.page_num
        
        # Second try: Look for pages with high density of "means" or colon patterns
        # This catches documents without explicit "Definitions" headers
        for page in pages[:15]:
            means_count = len(re.findall(r'\b[A-Z][A-Za-z\s]{2,40}\s+means\s+', page.text))
            colon_count = len(re.findall(r'\b[A-Z][A-Za-z\s]{2,40}\s*:\s*[A-Z]', page.text))
            
            # If page has 3+ definition-like patterns, treat it as definitions section
            if means_count >= 3 or colon_count >= 5:
                self.logger.info(f"Found likely definitions section on page {page.page_num} (means={means_count}, colon={colon_count})")
                return page.page_num
        
        return None
    
    def _extract_from_definitions_section(self, pages: List[Page], start_page: int) -> List[Definition]:
        """Extract definitions from the definitions section."""
        definitions = []
        
        # Get text from definitions section (current page and next few pages)
        # Remove headers and footers from each page
        section_text = ""
        for page in pages:
            if start_page <= page.page_num <= start_page + 5:
                cleaned_text = self._remove_headers_footers(page.text, page.page_num)
                section_text += cleaned_text + "\n"
        
        # Find where definitions section ends (next article)
        end_match = re.search(r'\n\s*Article\s*\(?\s*[2-9]\d*\s*\)?', section_text, re.IGNORECASE)
        if end_match:
            section_text = section_text[:end_match.start()]
        
        # Also try to find "Chapter" or "Section" endings
        if not end_match:
            end_match = re.search(r'\n\s*(Chapter|Section)\s+[2-9]', section_text, re.IGNORECASE)
            if end_match:
                section_text = section_text[:end_match.start()]
        
        # Extract term-definition pairs
        for pattern in self.term_def_patterns:
            matches = re.finditer(pattern, section_text, re.DOTALL | re.IGNORECASE)
            
            for match in matches:
                term = match.group(1).strip()
                definition = match.group(2).strip()
                
                # Clean and validate
                term = self.canonicalizer.normalize_term(term)
                definition = self.canonicalizer.normalize_definition(definition)
                
                # Remove footer text from definition
                definition = self._remove_footer_from_definition(definition)
                
                # COMPREHENSIVE VALIDATION - Reject garbage extractions
                if not self._is_valid_term_definition(term, definition):
                    continue
                
                # Calculate page number (approximate)
                page_num = start_page
                
                definitions.append(Definition(
                    term=term,
                    definition=definition,
                    page=page_num,
                    confidence=0.90,
                    extraction_method="layout_regex"
                ))
        
        # Try alternative extraction for newline-separated format
        definitions.extend(self._extract_newline_separated_definitions(section_text, start_page))
        
        return definitions
    
    def _extract_from_definitions_section_pymupdf(self, pages: List[Page], start_page: int) -> List[Definition]:
        """Extract definitions using PyMuPDF for better multi-line term handling.
        
        Args:
            pages: List of Page objects
            start_page: Starting page number for definitions section
            
        Returns:
            List of Definition objects
        """
        from page_extractor import PageExtractor
        
        definitions = []
        
        try:
            # Use PyMuPDF to extract definitions section with layout awareness
            extractor = PageExtractor(self.pdf_path)
            end_page = min(start_page + 5, len(pages))
            
            # Get formatted text with multi-line terms merged
            section_text = extractor.extract_definitions_section_with_pymupdf(start_page, end_page)
            
            self.logger.info(f"Using PyMuPDF for definitions section (pages {start_page}-{end_page})")
            
            # Find where definitions section ends (next article)
            end_match = re.search(r'\n\s*Article\s*\(?\s*[2-9]\d*\s*\)?', section_text, re.IGNORECASE)
            if end_match:
                section_text = section_text[:end_match.start()]
            
            # Also try to find "Chapter" or "Section" endings
            if not end_match:
                end_match = re.search(r'\n\s*(Chapter|Section)\s+[2-9]', section_text, re.IGNORECASE)
                if end_match:
                    section_text = section_text[:end_match.start()]
            
            # Extract term-definition pairs using improved patterns
            for pattern in self.term_def_patterns:
                matches = re.finditer(pattern, section_text, re.DOTALL | re.IGNORECASE)
                
                for match in matches:
                    term = match.group(1).strip()
                    definition = match.group(2).strip()
                    
                    # Clean and validate
                    term = self.canonicalizer.normalize_term(term)
                    definition = self.canonicalizer.normalize_definition(definition)
                    
                    # COMPREHENSIVE VALIDATION - Reject garbage extractions
                    if not self._is_valid_term_definition(term, definition):
                        continue
                    
                    # Calculate page number (approximate)
                    page_num = start_page
                    
                    definitions.append(Definition(
                        term=term,
                        definition=definition,
                        page=page_num,
                        confidence=0.95,  # Higher confidence with PyMuPDF
                        extraction_method="pymupdf_layout"
                    ))
            
            # Try alternative extraction for newline-separated format
            definitions.extend(self._extract_newline_separated_definitions(section_text, start_page))
            
            self.logger.info(f"Extracted {len(definitions)} definitions using PyMuPDF")
            
        except Exception as e:
            self.logger.error(f"PyMuPDF extraction failed, falling back to regular extraction: {e}")
            # Fallback to regular extraction
            definitions = self._extract_from_definitions_section(pages, start_page)
        
        return definitions
    
    def _extract_newline_separated_definitions(self, text: str, page_num: int) -> List[Definition]:
        """Extract definitions in newline-separated format (common in legal docs)."""
        definitions = []
        
        # Pattern: Term on one line, definition on next line(s)
        # Example:
        # State
        # : United Arab Emirates.
        lines = text.split('\n')
        i = 0
        while i < len(lines) - 1:
            line = lines[i].strip()
            next_line = lines[i + 1].strip() if i + 1 < len(lines) else ''
            
            # Check if current line is a potential term (short, capitalized)
            if (len(line) > 2 and len(line) < 50 and 
                line[0].isupper() and 
                not line.endswith('.') and
                not line.startswith('Article') and
                not line.startswith('Chapter')):
                
                # Check if next line starts with colon or is a definition
                if next_line.startswith(':') or next_line.startswith('−') or next_line.startswith('–'):
                    # Collect definition (may span multiple lines)
                    definition_parts = []
                    j = i + 1
                    while j < len(lines):
                        def_line = lines[j].strip()
                        if not def_line:
                            break
                        # Stop if we hit another term
                        if (len(def_line) < 50 and def_line[0].isupper() and 
                            not def_line.startswith(':') and
                            not def_line.startswith('−') and
                            not def_line.startswith('–') and
                            j > i + 1):
                            break
                        definition_parts.append(def_line)
                        j += 1
                    
                    if definition_parts:
                        term = self.canonicalizer.normalize_term(line)
                        definition = ' '.join(definition_parts)
                        definition = self.canonicalizer.normalize_definition(definition)
                        
                        # Remove leading colon/dash
                        definition = re.sub(r'^[:−–—]\s*', '', definition)
                        
                        # COMPREHENSIVE VALIDATION - Reject garbage extractions
                        if self._is_valid_term_definition(term, definition):
                            definitions.append(Definition(
                                term=term,
                                definition=definition,
                                page=page_num,
                                confidence=0.88,
                                extraction_method="layout_regex"
                            ))
                        i = j
                        continue
            i += 1
        
        return definitions
    
    def _extract_definitions_general(self, pages: List[Page]) -> List[Definition]:
        """Extract definitions from entire document (not just definitions section)."""
        definitions = []
        
        for page in pages:
            text = page.text
            
            # Pattern 1: "X means Y" (most common)
            patterns = [
                r'\b([A-Z][A-Za-z\s\(\)]{2,50})\s+means\s+([^.]+\.)',
                r'\b([A-Z][A-Za-z\s\(\)]{2,50})\s+shall mean\s+([^.]+\.)',
                r'\b([A-Z][A-Za-z\s\(\)]{2,50})\s+mean\s+([^.]+\.)',
                
                # Pattern 2: "X refers to Y"
                r'\b([A-Z][A-Za-z\s\(\)]{2,50})\s+refers to\s+([^.]+\.)',
                r'\b([A-Z][A-Za-z\s\(\)]{2,50})\s+shall refer to\s+([^.]+\.)',
                
                # Pattern 3: "X is defined as Y"
                r'\b([A-Z][A-Za-z\s\(\)]{2,50})\s+is defined as\s+([^.]+\.)',
                
                # Pattern 4: "X denotes Y"
                r'\b([A-Z][A-Za-z\s\(\)]{2,50})\s+denotes\s+([^.]+\.)',
                
                # Pattern 5: Quoted terms
                r'"([^"]{2,50})"\s+means\s+([^.]+\.)',
                r'"([^"]{2,50})"\s+shall mean\s+([^.]+\.)',
                r'"([^"]{2,50})"\s+refers to\s+([^.]+\.)',
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.MULTILINE)
                
                for match in matches:
                    term = self.canonicalizer.normalize_term(match.group(1))
                    definition = self.canonicalizer.normalize_definition(match.group(2))
                    
                    # COMPREHENSIVE VALIDATION - Reject garbage extractions
                    if self._is_valid_term_definition(term, definition):
                        definitions.append(Definition(
                            term=term,
                            definition=definition,
                            page=page.page_num,
                            confidence=0.82,
                            extraction_method="regex"
                        ))
        
        return definitions
