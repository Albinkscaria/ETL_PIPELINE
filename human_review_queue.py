"""Human review queue for low-confidence extractions."""
import logging
import csv
import json
from typing import List, Dict, Any, Union
from datetime import datetime
from pathlib import Path
from models import Citation, Definition


class HumanReviewQueue:
    """Manages entities requiring human review."""
    
    def __init__(self, threshold: float = 0.7, output_dir: str = "review_queue"):
        """Initialize review queue.
        
        Args:
            threshold: Confidence threshold below which entities need review
            threshold: Minimum confidence threshold
            output_dir: Directory for review files
        """
        self.logger = logging.getLogger(__name__)
        self.threshold = threshold
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.queue: List[Dict[str, Any]] = []
    
    def add_to_queue(self, entity: Union[Citation, Definition], 
                     reason: str, context: str = ""):
        """Add entity to review queue.
        
        Args:
            entity: Citation or Definition object
            reason: Reason for review
            context: Additional context
        """
        entity_type = "citation" if isinstance(entity, Citation) else "definition"
        
        review_item = {
            "entity_type": entity_type,
            "entity_id": f"{entity_type}_{len(self.queue)}",
            "text": entity.text if isinstance(entity, Citation) else entity.term,
            "definition": entity.definition if isinstance(entity, Definition) else "",
            "page": entity.page,
            "confidence": entity.confidence,
            "extraction_method": entity.extraction_method,
            "reason": reason,
            "context": context,
            "status": "pending",
            "added_at": datetime.utcnow().isoformat() + 'Z'
        }
        
        self.queue.append(review_item)
        self.logger.debug(f"Added {entity_type} to review queue: {reason}")
    
    def check_and_add(self, entities: List[Union[Citation, Definition]]):
        """Check entities and add low-confidence ones to queue.
        
        Args:
            entities: List of Citation or Definition objects
        """
        for entity in entities:
            if entity.confidence < self.threshold:
                reason = f"Low confidence ({entity.confidence:.2f})"
                self.add_to_queue(entity, reason)
    
    def export_review_batch(self, format: str = "csv") -> str:
        """Export review queue for human review.
        
        Args:
            format: Output format ('csv' or 'json')
            
        Returns:
            Path to exported file
        """
        if not self.queue:
            self.logger.info("Review queue is empty - nothing to export")
            return ""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format == "csv":
            output_path = self.output_dir / f"review_batch_{timestamp}.csv"
            self._export_csv(output_path)
        else:
            output_path = self.output_dir / f"review_batch_{timestamp}.json"
            self._export_json(output_path)
        
        self.logger.info(f"Exported {len(self.queue)} items to {output_path}")
        return str(output_path)
    
    def _export_csv(self, output_path: Path):
        """Export queue to CSV."""
        fieldnames = [
            "entity_id", "entity_type", "text", "definition", 
            "page", "confidence", "extraction_method", 
            "reason", "context", "status", "added_at",
            "reviewed_by", "reviewed_at", "corrected_text", "notes"
        ]
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for item in self.queue:
                # Add empty fields for review
                item['reviewed_by'] = ''
                item['reviewed_at'] = ''
                item['corrected_text'] = ''
                item['notes'] = ''
                writer.writerow(item)
    
    def _export_json(self, output_path: Path):
        """Export queue to JSON."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                "export_date": datetime.utcnow().isoformat() + 'Z',
                "total_items": len(self.queue),
                "items": self.queue
            }, f, indent=2, ensure_ascii=False)
    
    def import_reviewed_batch(self, input_path: str) -> Dict[str, Any]:
        """Import human-reviewed corrections.
        
        Args:
            input_path: Path to reviewed file (CSV or JSON)
            
        Returns:
            Dictionary with correction statistics
        """
        input_path = Path(input_path)
        
        if not input_path.exists():
            self.logger.error(f"Review file not found: {input_path}")
            return {"error": "File not found"}
        
        if input_path.suffix == '.csv':
            corrections = self._import_csv(input_path)
        else:
            corrections = self._import_json(input_path)
        
        stats = {
            "total_reviewed": len(corrections),
            "accepted": sum(1 for c in corrections if c.get('status') == 'accepted'),
            "rejected": sum(1 for c in corrections if c.get('status') == 'rejected'),
            "corrected": sum(1 for c in corrections if c.get('corrected_text')),
        }
        
        self.logger.info(f"Imported {stats['total_reviewed']} reviewed items")
        return stats
    
    def _import_csv(self, input_path: Path) -> List[Dict]:
        """Import corrections from CSV."""
        corrections = []
        
        with open(input_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('reviewed_by'):  # Only import reviewed items
                    corrections.append(row)
        
        return corrections
    
    def _import_json(self, input_path: Path) -> List[Dict]:
        """Import corrections from JSON."""
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        corrections = [item for item in data.get('items', []) 
                      if item.get('reviewed_by')]
        
        return corrections
    
    def get_queue_summary(self) -> Dict[str, Any]:
        """Get summary of review queue.
        
        Returns:
            Dictionary with queue statistics
        """
        if not self.queue:
            return {"total": 0}
        
        by_type = {}
        by_reason = {}
        
        for item in self.queue:
            entity_type = item['entity_type']
            reason = item['reason']
            
            by_type[entity_type] = by_type.get(entity_type, 0) + 1
            by_reason[reason] = by_reason.get(reason, 0) + 1
        
        return {
            "total": len(self.queue),
            "by_type": by_type,
            "by_reason": by_reason,
            "avg_confidence": sum(item['confidence'] for item in self.queue) / len(self.queue)
        }
    
    def clear_queue(self):
        """Clear the review queue."""
        self.queue.clear()
        self.logger.info("Review queue cleared")
