"""OCR processor for scanned pages."""
import logging
from typing import Optional, Tuple
from dataclasses import dataclass
import fitz  # PyMuPDF
from PIL import Image
import io

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    logging.warning("pytesseract not available - OCR will be disabled")


@dataclass
class OCRResult:
    """Result from OCR processing."""
    text: str
    confidence: float
    method: str


class OCRProcessor:
    """Handles OCR for scanned pages or low-quality text extraction."""
    
    def __init__(self, languages: list = None, dpi: int = 300):
        """Initialize OCR processor.
        
        Args:
            languages: List of language codes (e.g., ['eng', 'ara'])
            dpi: DPI for image rendering
        """
        self.logger = logging.getLogger(__name__)
        self.languages = languages or ['eng']
        self.dpi = dpi
        self.tesseract_available = TESSERACT_AVAILABLE
        
        if not self.tesseract_available:
            self.logger.warning("Tesseract not available. OCR functionality disabled.")
            self.logger.warning("To enable OCR, install Tesseract:")
            self.logger.warning("  Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki")
            self.logger.warning("  macOS: brew install tesseract")
            self.logger.warning("  Linux: sudo apt-get install tesseract-ocr")
    
    def needs_ocr(self, text: str, page_area: float = 1.0) -> bool:
        """Determine if page needs OCR.
        
        Args:
            text: Extracted text from page
            page_area: Page area in square inches
            
        Returns:
            True if OCR is needed
        """
        if not text or len(text.strip()) < 50:
            self.logger.debug("Page has minimal text - OCR needed")
            return True
        
        # Calculate text density (chars per square inch)
        text_density = len(text) / max(page_area, 1.0)
        
        if text_density < 100:  # Very low density
            self.logger.debug(f"Low text density ({text_density:.1f}) - OCR may help")
            return True
        
        return False
    
    def perform_ocr(self, pdf_path: str, page_num: int) -> Optional[OCRResult]:
        """Perform OCR on a PDF page.
        
        Args:
            pdf_path: Path to PDF file
            page_num: Page number (0-indexed)
            
        Returns:
            OCRResult or None if OCR failed
        """
        if not self.tesseract_available:
            self.logger.warning(f"OCR requested for page {page_num+1} but Tesseract not available")
            return None
        
        try:
            # Convert PDF page to image
            doc = fitz.open(pdf_path)
            page = doc[page_num]
            
            # Render at high DPI for better OCR
            mat = fitz.Matrix(self.dpi / 72, self.dpi / 72)
            pix = page.get_pixmap(matrix=mat)
            
            # Convert to PIL Image
            img_data = pix.tobytes("png")
            image = Image.open(io.BytesIO(img_data))
            
            doc.close()
            
            # Preprocess image
            image = self._preprocess_image(image)
            
            # Run Tesseract OCR
            lang_str = '+'.join(self.languages)
            custom_config = r'--oem 3 --psm 6'  # LSTM + Block segmentation
            
            text = pytesseract.image_to_string(
                image,
                lang=lang_str,
                config=custom_config
            )
            
            # Get confidence (if available)
            try:
                data = pytesseract.image_to_data(image, lang=lang_str, output_type=pytesseract.Output.DICT)
                confidences = [int(conf) for conf in data['conf'] if conf != '-1']
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            except:
                avg_confidence = 0.7  # Default confidence
            
            self.logger.info(f"OCR completed for page {page_num+1}: {len(text)} chars, confidence {avg_confidence:.2f}")
            
            return OCRResult(
                text=text,
                confidence=avg_confidence / 100.0,  # Normalize to 0-1
                method="tesseract"
            )
            
        except Exception as e:
            self.logger.error(f"OCR failed for page {page_num+1}: {e}")
            return None
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR.
        
        Args:
            image: PIL Image
            
        Returns:
            Preprocessed image
        """
        # Convert to grayscale
        if image.mode != 'L':
            image = image.convert('L')
        
        # Simple contrast enhancement
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.5)
        
        return image
