"""Main entry point for the ETL pipeline."""
import os
import logging
from dotenv import load_dotenv
from etl_orchestrator import ETLOrchestrator


def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def main():
    """Main function to run the ETL pipeline."""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("UAE Legal Documents ETL Pipeline")
    logger.info("=" * 80)
    
    # Load environment variables
    load_dotenv()
    
    # Validate API key
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        logger.error("GEMINI_API_KEY not found in environment")
        logger.error("Please create a .env file with your Gemini API key")
        logger.error("Example: GEMINI_API_KEY=your_api_key_here")
        return
    
    logger.info("✓ API key found")
    
    # Check if config file exists
    if not os.path.exists('config.json'):
        logger.error("config.json not found")
        return
    
    logger.info("✓ Configuration file found")
    
    try:
        # Initialize and run pipeline
        orchestrator = ETLOrchestrator(config_path='config.json')
        results = orchestrator.run_pipeline()
        
        # Print final summary
        print("\n" + "=" * 80)
        print("PIPELINE EXECUTION SUMMARY")
        print("=" * 80)
        print(f"Documents processed: {results['summary']['total_documents']}")
        print(f"Total citations extracted: {results['summary']['total_citations']}")
        print(f"Total definitions extracted: {results['summary']['total_terms']}")
        print(f"Processing time: {results['summary']['processing_time_seconds']} seconds")
        print(f"Output file: extracted_data.json")
        print("=" * 80)
        
        if 'errors' in results and results['errors']:
            print(f"\n⚠ Warning: {len(results['errors'])} document(s) failed to process")
            for error in results['errors']:
                print(f"  - {error['filename']}: {error['error']}")
        
        logger.info("Pipeline execution completed successfully")
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    main()
