"""Comprehensive system test to validate all components."""
import os
import json
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def test_imports():
    """Test that all modules can be imported."""
    logger.info("Testing imports...")
    
    try:
        from etl_orchestrator import ETLOrchestrator
        from document_ingestor import DocumentIngestor
        from page_extractor import PageExtractor
        from deterministic_extractor import DeterministicExtractor
        from gemini_enhancer import GeminiEnhancer
        from groq_enhancer import GroqEnhancer
        from canonicalizer import Canonicalizer
        from result_merger import ResultMerger
        from output_schema_exporter import OutputSchemaExporter
        from aws_storage import AWSStorage
        logger.info("✓ All imports successful")
        return True
    except Exception as e:
        logger.error(f"✗ Import failed: {e}")
        return False


def test_config():
    """Test configuration file."""
    logger.info("Testing configuration...")
    
    if not os.path.exists('config.json'):
        logger.error("✗ config.json not found")
        return False
    
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        required_keys = [
            'pdf_directory', 'output_file', 'use_ai_enhancement',
            'ai_provider', 'gemini_model', 'groq_model'
        ]
        
        for key in required_keys:
            if key not in config:
                logger.error(f"✗ Missing config key: {key}")
                return False
        
        logger.info("✓ Configuration valid")
        return True
    except Exception as e:
        logger.error(f"✗ Config test failed: {e}")
        return False


def test_data_directory():
    """Test that Data directory exists and has PDFs."""
    logger.info("Testing Data directory...")
    
    if not os.path.isdir('Data'):
        logger.error("✗ Data directory not found")
        return False
    
    pdf_files = list(Path('Data').glob('*.pdf'))
    if not pdf_files:
        logger.error("✗ No PDF files found in Data directory")
        return False
    
    logger.info(f"✓ Found {len(pdf_files)} PDF files")
    return True


def test_environment():
    """Test environment variables."""
    logger.info("Testing environment variables...")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    gemini_key = os.getenv('GEMINI_API_KEY')
    groq_key = os.getenv('GROQ_API_KEY')
    
    if not gemini_key:
        logger.warning("⚠ GEMINI_API_KEY not set")
    else:
        logger.info("✓ GEMINI_API_KEY found")
    
    if not groq_key or groq_key == 'YOUR_GROQ_API_KEY_HERE':
        logger.warning("⚠ GROQ_API_KEY not set (placeholder)")
    else:
        logger.info("✓ GROQ_API_KEY found")
    
    return True


def test_deterministic_extraction():
    """Test deterministic extraction on a sample."""
    logger.info("Testing deterministic extraction...")
    
    try:
        from deterministic_extractor import DeterministicExtractor
        from models import Page
        
        extractor = DeterministicExtractor()
        
        # Test citation extraction
        sample_text = """
        Having reviewed:
        - Federal Decree-Law No. (7) of 2017 on Excise Tax;
        - Cabinet Resolution No. (52) of 2017;
        - Federal Law No. (1) of 1972 Concerning the Competencies of Ministries;
        """
        
        page = Page(page_num=1, text=sample_text, layout_info={})
        citations = extractor.extract_citations([page])
        
        if len(citations) < 2:
            logger.error(f"✗ Expected at least 2 citations, got {len(citations)}")
            return False
        
        logger.info(f"✓ Extracted {len(citations)} citations")
        
        # Test definition extraction
        sample_def_text = """
        Article (1) - Definitions
        
        Ministry: Ministry of Finance.
        
        Authority: The Federal Tax Authority.
        
        Tax Period: The period for which tax is calculated.
        """
        
        page_def = Page(page_num=2, text=sample_def_text, layout_info={})
        definitions = extractor.extract_definitions([page_def])
        
        if len(definitions) < 2:
            logger.error(f"✗ Expected at least 2 definitions, got {len(definitions)}")
            return False
        
        logger.info(f"✓ Extracted {len(definitions)} definitions")
        return True
        
    except Exception as e:
        logger.error(f"✗ Deterministic extraction test failed: {e}")
        return False


def test_canonicalization():
    """Test canonicalization."""
    logger.info("Testing canonicalization...")
    
    try:
        from canonicalizer import Canonicalizer
        
        canon = Canonicalizer()
        
        # Test citation canonicalization
        test_cases = [
            ("Federal Decree by Law No. (47) of 2022 Concerning Corporate Tax", "fed_decree_law_47_2022"),
            ("Cabinet Resolution No. (52) of 2017", "cabinet_resolution_52_2017"),
            ("Federal Law No. (1) of 1972", "federal_law_1_1972"),
        ]
        
        for input_text, expected in test_cases:
            result = canon.canonicalize_citation(input_text)
            if result != expected:
                logger.error(f"✗ Canonicalization failed: {input_text} → {result} (expected {expected})")
                return False
        
        logger.info("✓ Canonicalization working correctly")
        return True
        
    except Exception as e:
        logger.error(f"✗ Canonicalization test failed: {e}")
        return False


def test_output_schema():
    """Test output schema exporter."""
    logger.info("Testing output schema...")
    
    try:
        from output_schema_exporter import OutputSchemaExporter
        
        # Create sample data
        sample_docs = [
            {
                'doc_id': 'test_doc_1',
                'source_filename': 'test.pdf',
                'metadata': {
                    'pages': 10,
                    'processing_date': '2025-12-07T10:00:00Z',
                    'processing_time_seconds': 5.0
                },
                'citations': [
                    {
                        'text': 'Federal Law No. (1) of 1972',
                        'canonical_id': 'federal_law_1_1972',
                        'page': 1,
                        'confidence': 0.95,
                        'extraction_method': 'regex'
                    }
                ],
                'terms_definitions': [
                    {
                        'term': 'Ministry',
                        'definition': 'Ministry of Finance',
                        'page': 2,
                        'confidence': 0.90,
                        'extraction_method': 'layout'
                    }
                ]
            }
        ]
        
        # Export
        exporter = OutputSchemaExporter('test_output.json')
        exporter.export(sample_docs, processing_time=5.0)
        
        # Verify files exist
        if not os.path.exists('test_output.json'):
            logger.error("✗ test_output.json not created")
            return False
        
        if not os.path.exists('test_output_requirements_format.json'):
            logger.error("✗ test_output_requirements_format.json not created")
            return False
        
        # Verify requirements format
        with open('test_output_requirements_format.json', 'r') as f:
            output = json.load(f)
        
        required_keys = ['source_manifest', 'citations', 'term_definitions', 'summary']
        for key in required_keys:
            if key not in output:
                logger.error(f"✗ Missing key in requirements format: {key}")
                return False
        
        # Cleanup
        os.remove('test_output.json')
        os.remove('test_output_requirements_format.json')
        
        logger.info("✓ Output schema working correctly")
        return True
        
    except Exception as e:
        logger.error(f"✗ Output schema test failed: {e}")
        return False


def test_aws_storage():
    """Test AWS storage (without actual upload)."""
    logger.info("Testing AWS storage...")
    
    try:
        from aws_storage import AWSStorage
        
        # Test initialization (disabled)
        storage = AWSStorage(
            bucket_name='test-bucket',
            region='us-east-1',
            enabled=False
        )
        
        logger.info("✓ AWS storage module working")
        return True
        
    except Exception as e:
        logger.error(f"✗ AWS storage test failed: {e}")
        return False


def main():
    """Run all tests."""
    logger.info("=" * 80)
    logger.info("COMPREHENSIVE SYSTEM TEST")
    logger.info("=" * 80)
    
    tests = [
        ("Imports", test_imports),
        ("Configuration", test_config),
        ("Data Directory", test_data_directory),
        ("Environment", test_environment),
        ("Deterministic Extraction", test_deterministic_extraction),
        ("Canonicalization", test_canonicalization),
        ("Output Schema", test_output_schema),
        ("AWS Storage", test_aws_storage),
    ]
    
    results = []
    for name, test_func in tests:
        logger.info(f"\n{'='*80}")
        logger.info(f"TEST: {name}")
        logger.info(f"{'='*80}")
        result = test_func()
        results.append((name, result))
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status}: {name}")
    
    logger.info("=" * 80)
    logger.info(f"TOTAL: {passed}/{total} tests passed")
    logger.info("=" * 80)
    
    if passed == total:
        logger.info("🎉 ALL TESTS PASSED!")
        return 0
    else:
        logger.error(f"⚠ {total - passed} test(s) failed")
        return 1


if __name__ == '__main__':
    exit(main())
