"""Handles PDF file discovery and loading."""
import os
import logging
from typing import List


class DocumentIngestor:
    """Handles PDF file discovery and loading."""
    
    def __init__(self, pdf_directory: str):
        """Initialize the document ingestor.
        
        Args:
            pdf_directory: Path to directory containing PDF files
        """
        self.pdf_directory = pdf_directory
        self.logger = logging.getLogger(__name__)
        
        if not os.path.exists(pdf_directory):
            raise ValueError(f"PDF directory does not exist: {pdf_directory}")
    
    def list_pdfs(self) -> List[str]:
        """List all PDF files in the directory.
        
        Returns:
            List of PDF filenames
        """
        try:
            files = [f for f in os.listdir(self.pdf_directory) 
                    if f.lower().endswith('.pdf')]
            self.logger.info(f"Found {len(files)} PDF files in {self.pdf_directory}")
            return sorted(files)
        except Exception as e:
            self.logger.error(f"Error listing PDFs: {e}")
            return []
    
    def load_pdf(self, filename: str) -> bytes:
        """Load a PDF file as bytes.
        
        Args:
            filename: Name of the PDF file
            
        Returns:
            PDF file content as bytes
        """
        filepath = os.path.join(self.pdf_directory, filename)
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"PDF file not found: {filepath}")
        
        try:
            with open(filepath, 'rb') as f:
                content = f.read()
            self.logger.info(f"Loaded PDF: {filename} ({len(content)} bytes)")
            return content
        except Exception as e:
            self.logger.error(f"Error loading PDF {filename}: {e}")
            raise
    
    def get_pdf_path(self, filename: str) -> str:
        """Get full path to a PDF file.
        
        Args:
            filename: Name of the PDF file
            
        Returns:
            Full path to the PDF file
        """
        return os.path.join(self.pdf_directory, filename)
