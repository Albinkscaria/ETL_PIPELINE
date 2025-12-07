"""JSON schema validation for output data."""
import logging
from typing import Dict, List, Any
import jsonschema
from jsonschema import validate, ValidationError


class SchemaValidator:
    """Validates output against JSON schema."""
    
    def __init__(self):
        """Initialize schema validator."""
        self.logger = logging.getLogger(__name__)
        self.schema = self._create_schema()
    
    def _create_schema(self) -> Dict:
        """Create JSON schema for output validation.
        
        Returns:
            JSON schema dictionary
        """
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "required": ["source_manifest", "citations", "term_definitions"],
            "properties": {
                "source_manifest": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["doc_id", "filename", "pages"],
                        "properties": {
                            "doc_id": {"type": "string"},
                            "filename": {"type": "string"},
                            "source_url": {"type": "string"},
                            "pages": {"type": "integer", "minimum": 1},
                            "ingested_at": {"type": "string", "format": "date-time"},
                            "file_size": {"type": "integer"},
                            "file_hash": {"type": "string"}
                        }
                    }
                },
                "citations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["canonical_id", "raw_text", "type", "number", "year"],
                        "properties": {
                            "canonical_id": {"type": "string"},
                            "raw_text": {"type": "string"},
                            "normalized": {"type": "string"},
                            "type": {"type": "string"},
                            "number": {"type": ["integer", "string"]},
                            "year": {"type": "integer", "minimum": 1900, "maximum": 2100},
                            "title": {"type": "string"},
                            "document_url": {"type": "string"},
                            "provenance": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": ["doc_id", "page"],
                                    "properties": {
                                        "doc_id": {"type": "string"},
                                        "page": {"type": "integer"},
                                        "excerpt": {"type": "string"}
                                    }
                                }
                            },
                            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                            "extraction_method": {"type": "string"}
                        }
                    }
                },
                "term_definitions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["term", "definition"],
                        "properties": {
                            "term": {"type": "string", "minLength": 1},
                            "definition": {"type": "string", "minLength": 1},
                            "normalized_term": {"type": "string"},
                            "provenance": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": ["doc_id", "page"],
                                    "properties": {
                                        "doc_id": {"type": "string"},
                                        "page": {"type": "integer"},
                                        "excerpt": {"type": "string"}
                                    }
                                }
                            },
                            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                            "extraction_method": {"type": "string"}
                        }
                    }
                },
                "summary": {
                    "type": "object",
                    "properties": {
                        "total_documents": {"type": "integer"},
                        "total_citations": {"type": "integer"},
                        "total_terms": {"type": "integer"},
                        "processing_time_seconds": {"type": "number"},
                        "processing_date": {"type": "string"},
                        "pipeline_version": {"type": "string"}
                    }
                },
                "metadata": {
                    "type": "object",
                    "properties": {
                        "extraction_methods": {"type": "object"},
                        "confidence_distribution": {"type": "object"},
                        "quality_metrics": {"type": "object"}
                    }
                }
            }
        }
    
    def validate(self, data: Dict) -> tuple[bool, List[str]]:
        """Validate data against schema.
        
        Args:
            data: Data dictionary to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        try:
            validate(instance=data, schema=self.schema)
            self.logger.info("Schema validation passed")
            return True, []
            
        except ValidationError as e:
            error_msg = f"Schema validation failed: {e.message}"
            self.logger.error(error_msg)
            errors.append(error_msg)
            
            # Add path information
            if e.path:
                path_str = " -> ".join(str(p) for p in e.path)
                errors.append(f"Error at: {path_str}")
            
            return False, errors
        
        except Exception as e:
            error_msg = f"Validation error: {str(e)}"
            self.logger.error(error_msg)
            return False, [error_msg]
    
    def validate_business_rules(self, data: Dict) -> tuple[bool, List[str]]:
        """Validate business logic rules.
        
        Args:
            data: Data dictionary to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Rule 1: Must have at least one citation or definition
        total_citations = len(data.get('citations', []))
        total_definitions = len(data.get('term_definitions', []))
        
        if total_citations == 0 and total_definitions == 0:
            errors.append("No citations or definitions extracted")
        
        # Rule 2: Canonical IDs must be unique
        citation_ids = [c.get('canonical_id') for c in data.get('citations', [])]
        if len(citation_ids) != len(set(citation_ids)):
            errors.append("Duplicate canonical IDs found in citations")
        
        # Rule 3: Terms must be unique (case-insensitive)
        terms = [t.get('term', '').lower() for t in data.get('term_definitions', [])]
        if len(terms) != len(set(terms)):
            errors.append("Duplicate terms found in definitions")
        
        # Rule 4: Confidence scores must be valid
        for citation in data.get('citations', []):
            conf = citation.get('confidence', 0)
            if not (0 <= conf <= 1):
                errors.append(f"Invalid confidence score: {conf}")
        
        for definition in data.get('term_definitions', []):
            conf = definition.get('confidence', 0)
            if not (0 <= conf <= 1):
                errors.append(f"Invalid confidence score: {conf}")
        
        # Rule 5: Years must be reasonable
        for citation in data.get('citations', []):
            year = citation.get('year', 0)
            if year and not (1900 <= year <= 2100):
                errors.append(f"Invalid year: {year}")
        
        if errors:
            self.logger.warning(f"Business rule validation failed: {len(errors)} errors")
            return False, errors
        
        self.logger.info("Business rule validation passed")
        return True, []
    
    def validate_all(self, data: Dict) -> tuple[bool, List[str]]:
        """Run all validations.
        
        Args:
            data: Data dictionary to validate
            
        Returns:
            Tuple of (is_valid, all_error_messages)
        """
        all_errors = []
        
        # Schema validation
        schema_valid, schema_errors = self.validate(data)
        all_errors.extend(schema_errors)
        
        # Business rules validation
        rules_valid, rules_errors = self.validate_business_rules(data)
        all_errors.extend(rules_errors)
        
        is_valid = schema_valid and rules_valid
        
        if is_valid:
            self.logger.info("All validations passed")
        else:
            self.logger.error(f"Validation failed with {len(all_errors)} errors")
        
        return is_valid, all_errors
