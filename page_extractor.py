"""Extracts text and layout from PDF pages."""
import logging
import re
from typing import List, Dict, Any, Optional
import pdfplumber
import fitz  # PyMuPDF
try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False
from models import Page


class PageExtractor:
    """Extracts text and layout from PDF pages."""
    
    def __init__(self, pdf_path: str):
        """Initialize the page extractor.
        
        Args:
            pdf_path: Path to the PDF file
        """
        self.pdf_path = pdf_path
        self.logger = logging.getLogger(__name__)
    
    def extract_pages(self) -> List[Page]:
        """Extract all pages from the PDF.
        
        Returns:
            List of Page objects
        """
        pages = []
        
        # Try pypdf first (best text extraction)
        if PYPDF_AVAILABLE:
            try:
                pages = self._extract_with_pypdf()
                if pages:
                    self.logger.info(f"Extracted {len(pages)} pages using pypdf")
                    return pages
            except Exception as e:
                self.logger.warning(f"pypdf extraction failed: {e}")
        
        # Try pdfplumber second
        try:
            pages = self._extract_with_pdfplumber()
            if pages:
                self.logger.info(f"Extracted {len(pages)} pages using pdfplumber")
                return pages
        except Exception as e:
            self.logger.warning(f"pdfplumber extraction failed: {e}")
        
        # Fallback to PyMuPDF
        try:
            pages = self._extract_with_pymupdf()
            self.logger.info(f"Extracted {len(pages)} pages using PyMuPDF")
            return pages
        except Exception as e:
            self.logger.error(f"PyMuPDF extraction failed: {e}")
            raise
    
    def _extract_with_pypdf(self) -> List[Page]:
        """Extract pages using pypdf (best text extraction)."""
        pages = []
        
        reader = PdfReader(self.pdf_path)
        
        for page_num, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            
            # Handle hyphenated line breaks and multi-line terms
            text = self._dehyphenate_text(text)
            
            # pypdf doesn't provide detailed layout info, so use empty dict
            layout_info = {"chars": [], "words": [], "lines": []}
            
            pages.append(Page(
                page_num=page_num,
                text=text,
                layout_info=layout_info
            ))
        
        return pages
    
    def _extract_with_pdfplumber(self) -> List[Page]:
        """Extract pages using pdfplumber."""
        pages = []
        
        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                
                # Handle hyphenated line breaks and multi-line terms
                text = self._dehyphenate_text(text)
                
                # Extract layout information
                layout_info = self._extract_layout_pdfplumber(page)
                
                pages.append(Page(
                    page_num=page_num,
                    text=text,
                    layout_info=layout_info
                ))
        
        return pages
    
    def _dehyphenate_text(self, text: str) -> str:
        """Remove hyphenation at line breaks and merge multi-line terms.
        
        Handles cases like:
        - "Stock-\npiler" → "Stockpiler"
        - "legisla-\ntion" → "legislation"
        - "Warehouse Keep-\ner" → "Warehouse Keeper"
        - "Administrative\nFines" → "Administrative Fines" (for definition terms)
        - "Customs Legisla-\ntion" → "Customs Legislation"
        
        Args:
            text: Raw text with potential hyphenation
            
        Returns:
            Text with hyphenation removed and multi-line terms merged
        """
        # Step 1: Handle hyphenated line breaks with lowercase continuation
        # "legisla-\ntion" → "legislation"
        text = re.sub(r'-\s*\n\s*([a-z])', r'\1', text)
        
        # Step 2: Handle hyphenated line breaks with uppercase continuation (broken words)
        # "Keep-\ner" → "Keeper"
        text = re.sub(r'-\s*\n\s*([a-z]{1,3})\b', r'\1', text)
        
        # Step 3: Handle multi-line terms in definitions (Term\nContinuation : Definition)
        # Look for pattern: "Word\nWord :" where both words start with capital
        # "Administrative\nFines :" → "Administrative Fines :"
        text = re.sub(r'\b([A-Z][a-z]+)\s*\n\s*([A-Z][a-z]+)\s*:', r'\1 \2:', text)
        
        # Step 4: Handle three-word multi-line terms
        # "Tax Registration\nNumber (TRN) :" → "Tax Registration Number (TRN) :"
        text = re.sub(r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\s*\n\s*([A-Z][a-z]+(?:\s*\([^)]+\))?)\s*:', r'\1 \2:', text)
        
        # Step 5: Handle compound terms split across lines
        # "Fine Assessment\nStockpiler :" → "Fine Assessment Stockpiler :"
        text = re.sub(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*\n\s*([A-Z][a-z]+)\s*:', r'\1 \2:', text)
        
        return text
    
    def _extract_layout_pdfplumber(self, page) -> Dict[str, Any]:
        """Extract layout information from pdfplumber page."""
        layout = {
            "chars": [],
            "words": [],
            "lines": []
        }
        
        try:
            # Extract character-level information
            chars = page.chars
            if chars:
                layout["chars"] = [{
                    "text": c.get("text", ""),
                    "x0": c.get("x0", 0),
                    "y0": c.get("y0", 0),
                    "fontname": c.get("fontname", ""),
                    "size": c.get("size", 0)
                } for c in chars[:1000]]  # Limit to avoid memory issues
            
            # Extract words
            words = page.extract_words()
            if words:
                layout["words"] = [{
                    "text": w.get("text", ""),
                    "x0": w.get("x0", 0),
                    "y0": w.get("y0", 0)
                } for w in words[:500]]
        except Exception as e:
            self.logger.warning(f"Error extracting layout: {e}")
        
        return layout
    
    def _extract_with_pymupdf(self) -> List[Page]:
        """Extract pages using PyMuPDF."""
        pages = []
        
        doc = fitz.open(self.pdf_path)
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            
            # Handle hyphenated line breaks and multi-line terms
            text = self._dehyphenate_text(text)
            
            # Extract layout information
            layout_info = self._extract_layout_pymupdf(page)
            
            pages.append(Page(
                page_num=page_num + 1,
                text=text,
                layout_info=layout_info
            ))
        
        doc.close()
        return pages
    
    def _extract_layout_pymupdf(self, page) -> Dict[str, Any]:
        """Extract layout information from PyMuPDF page."""
        layout = {
            "chars": [],
            "words": [],
            "lines": []
        }
        
        try:
            # Extract text with formatting
            blocks = page.get_text("dict")["blocks"]
            
            for block in blocks[:100]:  # Limit blocks
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            layout["words"].append({
                                "text": span.get("text", ""),
                                "x0": span.get("bbox", [0])[0],
                                "y0": span.get("bbox", [0, 0])[1],
                                "fontname": span.get("font", ""),
                                "size": span.get("size", 0),
                                "flags": span.get("flags", 0)
                            })
        except Exception as e:
            self.logger.warning(f"Error extracting PyMuPDF layout: {e}")
        
        return layout
    
    def extract_text_with_layout(self, page_num: int) -> Dict:
        """Extract text with layout for a specific page.
        
        Args:
            page_num: Page number (1-indexed)
            
        Returns:
            Dictionary with text and layout information
        """
        pages = self.extract_pages()
        
        if page_num < 1 or page_num > len(pages):
            raise ValueError(f"Invalid page number: {page_num}")
        
        page = pages[page_num - 1]
        return {
            "text": page.text,
            "layout": page.layout_info
        }
    
    def extract_definitions_section_with_pymupdf(self, start_page: int, end_page: int) -> str:
        """Extract definitions section using PyMuPDF with layout awareness.
        
        This method uses PyMuPDF to extract text with coordinate information,
        allowing detection of multi-line terms that are vertically aligned.
        
        Args:
            start_page: Starting page number (1-indexed)
            end_page: Ending page number (1-indexed)
            
        Returns:
            Formatted text with multi-line terms properly merged
        """
        try:
            doc = fitz.open(self.pdf_path)
            
            # Collect all text blocks with coordinates
            all_blocks = []
            
            for page_num in range(start_page - 1, min(end_page, len(doc))):
                page = doc[page_num]
                blocks = page.get_text("dict")["blocks"]
                
                for block in blocks:
                    if block.get("type") == 0:  # Text block
                        all_blocks.append({
                            "page": page_num + 1,
                            "bbox": block.get("bbox"),
                            "lines": block.get("lines", [])
                        })
            
            doc.close()
            
            # Process blocks to merge multi-line terms
            formatted_text = self._format_definitions_from_blocks(all_blocks)
            
            self.logger.info(f"Extracted definitions section using PyMuPDF (pages {start_page}-{end_page})")
            return formatted_text
            
        except Exception as e:
            self.logger.error(f"PyMuPDF definitions extraction failed: {e}")
            # Fallback to regular extraction
            pages = self.extract_pages()
            text = ""
            for page in pages:
                if start_page <= page.page_num <= end_page:
                    text += page.text + "\n"
            return text
    
    def _format_definitions_from_blocks(self, blocks: List[Dict]) -> str:
        """Format text from blocks, merging multi-line terms.
        
        Detects when words are vertically aligned (similar X-coordinate)
        and merges them into single terms.
        
        Args:
            blocks: List of text blocks with coordinate information
            
        Returns:
            Formatted text with multi-line terms merged
        """
        formatted_lines = []
        
        for block in blocks:
            lines = block.get("lines", [])
            
            i = 0
            while i < len(lines):
                line = lines[i]
                line_text = ""
                line_x0 = None
                line_y0 = None
                
                # Extract text, X-coordinate, and Y-coordinate from spans
                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    if text:
                        line_text += text + " "
                        if line_x0 is None:
                            bbox = span.get("bbox", [0, 0, 0, 0])
                            line_x0 = bbox[0]
                            line_y0 = bbox[1]
                
                line_text = line_text.strip()
                
                # Skip if this looks like a footer
                # Footers typically:
                # 1. Are at the bottom of the page (high Y coordinate)
                # 2. Contain page numbers
                # 3. Repeat document title
                if self._is_footer_line(line_text, line_y0, block.get("page", 1)):
                    i += 1
                    continue
                
                # Check if this looks like a term (short, capitalized, no colon yet)
                if (line_text and 
                    len(line_text) < 50 and 
                    line_text[0].isupper() and 
                    ':' not in line_text and
                    line_x0 is not None):
                    
                    # Look ahead for continuation lines
                    merged_term = line_text
                    j = i + 1
                    
                    while j < len(lines):
                        next_line = lines[j]
                        next_text = ""
                        next_x0 = None
                        
                        for span in next_line.get("spans", []):
                            text = span.get("text", "").strip()
                            if text:
                                next_text += text + " "
                                if next_x0 is None:
                                    next_x0 = span.get("bbox", [0])[0]
                        
                        next_text = next_text.strip()
                        
                        # Check if next line is a continuation (similar X-coordinate, no colon)
                        if (next_text and 
                            next_x0 is not None and
                            abs(next_x0 - line_x0) < 20 and  # Similar X position (within 20 points)
                            ':' not in next_text and
                            len(next_text) < 50):
                            
                            # Check if it's a continuation word (starts with capital or lowercase)
                            if (next_text[0].isupper() or 
                                next_text.startswith('of ') or 
                                next_text.startswith('and ') or
                                next_text.startswith('the ')):
                                
                                merged_term += " " + next_text
                                j += 1
                            else:
                                break
                        else:
                            # Found the definition line (has colon) or different structure
                            break
                    
                    # Add the merged term
                    formatted_lines.append(merged_term)
                    i = j
                else:
                    # Regular line (definition or other text)
                    if line_text:
                        formatted_lines.append(line_text)
                    i += 1
        
        return "\n".join(formatted_lines)
    
    def _is_footer_line(self, line_text: str, y_coord: float, page_num: int) -> bool:
        """Check if a line is part of a footer.
        
        Args:
            line_text: Text of the line
            y_coord: Y-coordinate of the line (higher = lower on page)
            page_num: Page number
            
        Returns:
            True if line is likely a footer
        """
        if not line_text:
            return False
        
        # Check if line is just a page number
        if line_text.strip().isdigit() and len(line_text.strip()) <= 3:
            return True
        
        # Check if line contains common footer patterns
        footer_patterns = [
            r'^\d+$',  # Just a number (page number)
            r'of \d{4} Regarding.*\d+$',  # "of 2025 Regarding... 2"
            r'Cabinet Resolution of \d{4}',  # Footer with document title
            r'Federal Decree.*of \d{4}.*\d+$',  # Footer with decree title and page number
            r'^Page \d+',  # "Page 1", "Page 2", etc.
        ]
        
        for pattern in footer_patterns:
            if re.search(pattern, line_text):
                return True
        
        # Check if line ends with just a page number (common footer format)
        # Example: "Cabinet Resolution of 2025 Regarding... 2"
        if re.search(r'\s+\d+\s*$', line_text) and len(line_text) > 50:
            # Long line ending with a number - likely footer
            return True
        
        return False
