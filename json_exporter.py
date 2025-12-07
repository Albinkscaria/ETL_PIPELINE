"""Exports final dataset to JSON."""
import json
import logging
from typing import Dict


class JSONExporter:
    """Exports final dataset to JSON."""
    
    def __init__(self, output_path: str):
        """Initialize the JSON exporter.
        
        Args:
            output_path: Path to output JSON file
        """
        self.output_path = output_path
        self.logger = logging.getLogger(__name__)
    
    def export(self, data: Dict) -> None:
        """Export data to JSON file.
        
        Args:
            data: Data dictionary to export
        """
        try:
            with open(self.output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Exported data to {self.output_path}")
            
            # Log file size
            import os
            file_size = os.path.getsize(self.output_path)
            self.logger.info(f"Output file size: {file_size:,} bytes")
            
        except Exception as e:
            self.logger.error(f"Error exporting to JSON: {e}")
            raise
