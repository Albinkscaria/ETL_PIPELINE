"""Validate extraction accuracy by comparing results against source PDFs."""
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple
import fitz  # PyMuPDF
from collections import defaultdict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


class AccuracyValidator:
    """Validates extraction accuracy against source PDFs."""
    
    def __init__(self, extracted_data_path: str, pdf_directory: str):
        """Initialize validator.
        
        Args:
            extracted_data_path: Path to extracted_data.json
            pdf_directory: Path to Data/ folder with PDFs
        """
        self.logger = logging.getLogger(__name__)
        self.extracted_data_path = extracted_data_path
        self.pdf_directory = Path(pdf_directory)
        
        # Load extracted data
        with open(extracted_data_path, 'r', encoding='utf-8') as f:
            self.extracted_data = json.load(f)
    
    def validate_all_documents(self) -> Dict:
        """Validate all documents and generate accuracy report.
        
        Returns:
            Dictionary with validation results
        """
        self.logger.info("=" * 80)
        self.logger.info("ACCURACY VALIDATION REPORT")
        self.logger.info("=" * 80)
        
        results = {
            'total_documents': len(self.extracted_data),
            'documents': {},
            'overall_stats': {
                'total_citations_extracted': 0,
                'total_citations_verified': 0,
                'total_definitions_extracted': 0,
                'total_definitions_verified': 0,
                'citation_accuracy': 0.0,
                'definition_accuracy': 0.0
            }
        }
        
        for pdf_name, data in self.extracted_data.items():
            self.logger.info(f"\n{'='*80}")
            self.logger.info(f"Validating: {pdf_name}")
            self.logger.info(f"{'='*80}")
            
            pdf_path = self.pdf_directory / pdf_name
            
            if not pdf_path.exists():
                self.logger.error(f"PDF not found: {pdf_path}")
                continue
            
            # Validate this document
            doc_results = self.validate_document(pdf_path, data)
            results['documents'][pdf_name] = doc_results
            
            # Update overall stats
            results['overall_stats']['total_citations_extracted'] += doc_results['citations']['total_extracted']
            results['overall_stats']['total_citations_verified'] += doc_results['citations']['verified_count']
            results['overall_stats']['total_definitions_extracted'] += doc_results['definitions']['total_extracted']
            results['overall_stats']['total_definitions_verified'] += doc_results['definitions']['verified_count']
        
        # Calculate overall accuracy
        if results['overall_stats']['total_citations_extracted'] > 0:
            results['overall_stats']['citation_accuracy'] = round(
                results['overall_stats']['total_citations_verified'] / 
                results['overall_stats']['total_citations_extracted'] * 100, 2
            )
        
        if results['overall_stats']['total_definitions_extracted'] > 0:
            results['overall_stats']['definition_accuracy'] = round(
                results['overall_stats']['total_definitions_verified'] / 
                results['overall_stats']['total_definitions_extracted'] * 100, 2
            )
        
        # Print summary
        self.print_summary(results)
        
        # Save detailed report
        self.save_report(results)
        
        return results
    
    def validate_document(self, pdf_path: Path, extracted_data: Dict) -> Dict:
        """Validate a single document.
        
        Args:
            pdf_path: Path to PDF file
            extracted_data: Extracted data for this document
            
        Returns:
            Validation results for this document
        """
        results = {
            'citations': {
                'total_extracted': len(extracted_data['citations']),
                'verified_count': 0,
                'verified_items': [],
                'unverified_items': [],
                'accuracy': 0.0
            },
            'definitions': {
                'total_extracted': len(extracted_data['term_definitions']),
                'verified_count': 0,
                'verified_items': [],
                'unverified_items': [],
                'accuracy': 0.0
            }
        }
        
        # Extract full text from PDF
        pdf_text = self.extract_pdf_text(pdf_path)
        
        # Validate citations
        self.logger.info(f"\nValidating {len(extracted_data['citations'])} citations...")
        for citation in extracted_data['citations']:
            is_valid = self.validate_citation(citation, pdf_text)
            if is_valid:
                results['citations']['verified_count'] += 1
                results['citations']['verified_items'].append(citation['text'][:100])
            else:
                results['citations']['unverified_items'].append(citation['text'][:100])
        
        # Validate definitions
        self.logger.info(f"Validating {len(extracted_data['term_definitions'])} definitions...")
        for definition in extracted_data['term_definitions']:
            is_valid = self.validate_definition(definition, pdf_text)
            if is_valid:
                results['definitions']['verified_count'] += 1
                results['definitions']['verified_items'].append(definition['term'])
            else:
                results['definitions']['unverified_items'].append(definition['term'])
        
        # Calculate accuracy
        if results['citations']['total_extracted'] > 0:
            results['citations']['accuracy'] = round(
                results['citations']['verified_count'] / 
                results['citations']['total_extracted'] * 100, 2
            )
        
        if results['definitions']['total_extracted'] > 0:
            results['definitions']['accuracy'] = round(
                results['definitions']['verified_count'] / 
                results['definitions']['total_extracted'] * 100, 2
            )
        
        # Log results
        self.logger.info(f"\nCitations: {results['citations']['verified_count']}/{results['citations']['total_extracted']} verified ({results['citations']['accuracy']}%)")
        self.logger.info(f"Definitions: {results['definitions']['verified_count']}/{results['definitions']['total_extracted']} verified ({results['definitions']['accuracy']}%)")
        
        return results
    
    def extract_pdf_text(self, pdf_path: Path) -> Dict[int, str]:
        """Extract text from PDF by page.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary mapping page number to text
        """
        pdf_text = {}
        
        try:
            doc = fitz.open(pdf_path)
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                pdf_text[page_num + 1] = text  # 1-indexed
            doc.close()
        except Exception as e:
            self.logger.error(f"Error extracting text from {pdf_path}: {e}")
        
        return pdf_text
    
    def validate_citation(self, citation: Dict, pdf_text: Dict[int, str]) -> bool:
        """Validate if citation exists in PDF.
        
        Args:
            citation: Citation dictionary
            pdf_text: PDF text by page
            
        Returns:
            True if citation is found in PDF
        """
        citation_text = citation['text']
        page = citation['page']
        
        # Check if page exists
        if page not in pdf_text:
            return False
        
        # Normalize text for comparison
        citation_normalized = self.normalize_text(citation_text)
        page_text_normalized = self.normalize_text(pdf_text[page])
        
        # Check if citation text appears in the page
        # For citations, we look for key parts (numbers and years)
        citation_parts = citation_normalized.split()
        
        # Look for significant parts (numbers, years)
        significant_parts = [part for part in citation_parts if any(c.isdigit() for c in part)]
        
        if not significant_parts:
            # If no numbers, check if substantial text matches
            return citation_normalized[:50] in page_text_normalized
        
        # Check if most significant parts are present
        matches = sum(1 for part in significant_parts if part in page_text_normalized)
        return matches >= len(significant_parts) * 0.7  # 70% threshold
    
    def validate_definition(self, definition: Dict, pdf_text: Dict[int, str]) -> bool:
        """Validate if definition exists in PDF.
        
        Args:
            definition: Definition dictionary
            pdf_text: PDF text by page
            
        Returns:
            True if definition is found in PDF
        """
        term = definition['term']
        definition_text = definition['definition']
        page = definition['page']
        
        # Check if page exists
        if page not in pdf_text:
            return False
        
        # Normalize text
        term_normalized = self.normalize_text(term)
        definition_normalized = self.normalize_text(definition_text)
        page_text_normalized = self.normalize_text(pdf_text[page])
        
        # Check if term appears on the page
        if term_normalized not in page_text_normalized:
            return False
        
        # Check if definition text appears (at least 50% of it)
        definition_words = definition_normalized.split()
        if len(definition_words) < 3:
            # Short definition - must match exactly
            return definition_normalized in page_text_normalized
        
        # For longer definitions, check if significant portion matches
        matches = sum(1 for word in definition_words if len(word) > 3 and word in page_text_normalized)
        return matches >= len(definition_words) * 0.5  # 50% threshold
    
    def normalize_text(self, text: str) -> str:
        """Normalize text for comparison.
        
        Args:
            text: Text to normalize
            
        Returns:
            Normalized text
        """
        # Convert to lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove common punctuation that might differ
        for char in [',', '.', ':', ';', '(', ')', '[', ']', '{', '}', '"', "'", '−', '–', '—']:
            text = text.replace(char, ' ')
        
        # Remove extra spaces again
        text = ' '.join(text.split())
        
        return text
    
    def print_summary(self, results: Dict):
        """Print validation summary.
        
        Args:
            results: Validation results
        """
        self.logger.info("\n" + "=" * 80)
        self.logger.info("OVERALL ACCURACY SUMMARY")
        self.logger.info("=" * 80)
        
        stats = results['overall_stats']
        
        self.logger.info(f"\nTotal Documents Validated: {results['total_documents']}")
        self.logger.info(f"\nCitations:")
        self.logger.info(f"  Total Extracted: {stats['total_citations_extracted']}")
        self.logger.info(f"  Verified: {stats['total_citations_verified']}")
        self.logger.info(f"  Accuracy: {stats['citation_accuracy']}%")
        
        self.logger.info(f"\nDefinitions:")
        self.logger.info(f"  Total Extracted: {stats['total_definitions_extracted']}")
        self.logger.info(f"  Verified: {stats['total_definitions_verified']}")
        self.logger.info(f"  Accuracy: {stats['definition_accuracy']}%")
        
        # Document-level breakdown
        self.logger.info(f"\n{'='*80}")
        self.logger.info("DOCUMENT-LEVEL ACCURACY")
        self.logger.info(f"{'='*80}")
        
        for pdf_name, doc_results in results['documents'].items():
            self.logger.info(f"\n{pdf_name}:")
            self.logger.info(f"  Citations: {doc_results['citations']['accuracy']}% ({doc_results['citations']['verified_count']}/{doc_results['citations']['total_extracted']})")
            self.logger.info(f"  Definitions: {doc_results['definitions']['accuracy']}% ({doc_results['definitions']['verified_count']}/{doc_results['definitions']['total_extracted']})")
    
    def save_report(self, results: Dict):
        """Save detailed validation report.
        
        Args:
            results: Validation results
        """
        report_path = 'accuracy_validation_report.json'
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"\n{'='*80}")
        self.logger.info(f"Detailed report saved to: {report_path}")
        self.logger.info(f"{'='*80}")


def main():
    """Main function."""
    validator = AccuracyValidator(
        extracted_data_path='extracted_data.json',
        pdf_directory='Data'
    )
    
    results = validator.validate_all_documents()
    
    print("\n" + "=" * 80)
    print("VALIDATION COMPLETE")
    print("=" * 80)
    print(f"\nOverall Citation Accuracy: {results['overall_stats']['citation_accuracy']}%")
    print(f"Overall Definition Accuracy: {results['overall_stats']['definition_accuracy']}%")
    print(f"\nDetailed report: accuracy_validation_report.json")
    print("=" * 80)


if __name__ == '__main__':
    main()
