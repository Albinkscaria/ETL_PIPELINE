"""
Comprehensive Validation Script
Validates all 15 PDFs against their JSON outputs according to requirements
"""

import json
import fitz  # PyMuPDF
import re
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

class ComprehensiveValidator:
    def __init__(self):
        self.results = {
            "validation_date": datetime.now().isoformat(),
            "documents_validated": 0,
            "total_issues": 0,
            "documents": {}
        }
        
    def load_json_output(self, json_path: str) -> Dict:
        """Load the extracted JSON data"""
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def validate_document(self, pdf_path: str, json_data: Dict) -> Dict:
        """Validate a single PDF against its JSON output"""
        issues = []
        stats = {
            "pdf_pages": 0,
            "json_pages": 0,
            "citations_found": 0,
            "citations_validated": 0,
            "definitions_found": 0,
            "definitions_validated": 0,
            "missing_fields": [],
            "schema_issues": [],
            "content_issues": []
        }
        
        try:
            # Open PDF
            doc = fitz.open(pdf_path)
            stats["pdf_pages"] = len(doc)
            stats["json_pages"] = json_data.get("metadata", {}).get("pages", 0)
            
            # Check page count match
            if stats["pdf_pages"] != stats["json_pages"]:
                issues.append({
                    "severity": "ERROR",
                    "type": "page_count_mismatch",
                    "message": f"PDF has {stats['pdf_pages']} pages but JSON reports {stats['json_pages']} pages"
                })
            
            # Validate metadata schema
            metadata = json_data.get("metadata", {})
            required_metadata = ["doc_id", "pages", "processing_date", "processing_time_seconds"]
            for field in required_metadata:
                if field not in metadata:
                    stats["missing_fields"].append(f"metadata.{field}")
                    issues.append({
                        "severity": "ERROR",
                        "type": "missing_metadata",
                        "message": f"Required metadata field '{field}' is missing"
                    })
            
            # Validate citations
            citations = json_data.get("citations", [])
            stats["citations_found"] = len(citations)
            
            for idx, citation in enumerate(citations):
                # Check required fields per requirements
                required_citation_fields = ["text", "canonical_id", "page", "confidence", "extraction_method"]
                missing = [f for f in required_citation_fields if f not in citation]
                if missing:
                    stats["missing_fields"].extend([f"citations[{idx}].{f}" for f in missing])
                    issues.append({
                        "severity": "ERROR",
                        "type": "missing_citation_fields",
                        "message": f"Citation {idx} missing fields: {missing}"
                    })
                
                # Validate citation against PDF
                if "page" in citation and "text" in citation:
                    page_num = citation["page"] - 1  # 0-indexed
                    if 0 <= page_num < len(doc):
                        page_text = doc[page_num].get_text()
                        citation_text = citation["text"]
                        
                        # Check if citation appears in PDF
                        if self._validate_citation_in_text(citation_text, page_text):
                            stats["citations_validated"] += 1
                        else:
                            issues.append({
                                "severity": "WARNING",
                                "type": "citation_not_found",
                                "message": f"Citation '{citation_text[:50]}...' not found on page {citation['page']}"
                            })
            
            # Validate definitions
            definitions = json_data.get("term_definitions", [])
            stats["definitions_found"] = len(definitions)
            
            for idx, defn in enumerate(definitions):
                # Check required fields
                required_defn_fields = ["term", "definition", "page", "confidence", "extraction_method"]
                missing = [f for f in required_defn_fields if f not in defn]
                if missing:
                    stats["missing_fields"].extend([f"term_definitions[{idx}].{f}" for f in missing])
                    issues.append({
                        "severity": "ERROR",
                        "type": "missing_definition_fields",
                        "message": f"Definition {idx} (term: {defn.get('term', 'unknown')}) missing fields: {missing}"
                    })
                
                # Validate definition against PDF
                if "page" in defn and "term" in defn:
                    page_num = defn["page"] - 1
                    if 0 <= page_num < len(doc):
                        page_text = doc[page_num].get_text()
                        term = defn["term"]
                        definition = defn.get("definition", "")
                        
                        # Check if term appears on the page
                        if term.lower() in page_text.lower():
                            stats["definitions_validated"] += 1
                        else:
                            issues.append({
                                "severity": "WARNING",
                                "type": "term_not_found",
                                "message": f"Term '{term}' not found on page {defn['page']}"
                            })
            
            # Check for requirements compliance
            self._check_requirements_compliance(json_data, issues, stats)
            
            doc.close()
            
        except Exception as e:
            issues.append({
                "severity": "CRITICAL",
                "type": "validation_error",
                "message": f"Error during validation: {str(e)}"
            })
        
        return {
            "stats": stats,
            "issues": issues,
            "total_issues": len(issues)
        }
    
    def _validate_citation_in_text(self, citation: str, page_text: str) -> bool:
        """Check if citation appears in page text"""
        # Extract key parts of citation
        citation_normalized = re.sub(r'\s+', ' ', citation.lower().strip())
        page_normalized = re.sub(r'\s+', ' ', page_text.lower().strip())
        
        # Check for number and year patterns
        numbers = re.findall(r'\d+', citation)
        if len(numbers) >= 2:
            # Check if both number and year appear
            return all(num in page_text for num in numbers[-2:])
        
        # Check for partial match (at least 50% of words)
        citation_words = [w for w in citation_normalized.split() if len(w) > 3]
        if not citation_words:
            return True
        
        matches = sum(1 for word in citation_words if word in page_normalized)
        return matches / len(citation_words) >= 0.5
    
    def _check_requirements_compliance(self, json_data: Dict, issues: List, stats: Dict):
        """Check compliance with requirements document"""
        
        # Requirement: Citations should have canonical_id in snake_case
        citations = json_data.get("citations", [])
        for idx, citation in enumerate(citations):
            canonical_id = citation.get("canonical_id", "")
            if canonical_id and not re.match(r'^[a-z_0-9]+$', canonical_id):
                issues.append({
                    "severity": "WARNING",
                    "type": "canonical_id_format",
                    "message": f"Citation {idx} canonical_id '{canonical_id}' not in snake_case format"
                })
        
        # Requirement: Confidence scores should be between 0 and 1
        all_items = citations + json_data.get("term_definitions", [])
        for idx, item in enumerate(all_items):
            confidence = item.get("confidence")
            if confidence is not None and not (0 <= confidence <= 1):
                issues.append({
                    "severity": "ERROR",
                    "type": "invalid_confidence",
                    "message": f"Item {idx} has invalid confidence score: {confidence}"
                })
        
        # Requirement: extraction_method should be documented
        for idx, item in enumerate(all_items):
            method = item.get("extraction_method")
            if not method:
                issues.append({
                    "severity": "WARNING",
                    "type": "missing_extraction_method",
                    "message": f"Item {idx} missing extraction_method"
                })
        
        # Check for provenance (requirements mention it but current schema doesn't have it)
        if citations and "provenance" not in citations[0]:
            stats["schema_issues"].append("Citations missing 'provenance' field (required by spec)")
        
        if json_data.get("term_definitions") and "provenance" not in json_data["term_definitions"][0]:
            stats["schema_issues"].append("Definitions missing 'provenance' field (required by spec)")
        
        # Check for additional required fields per spec
        for citation in citations:
            if "type" not in citation:
                stats["schema_issues"].append("Citations missing 'type' field (required by spec)")
                break
            if "number" not in citation:
                stats["schema_issues"].append("Citations missing 'number' field (required by spec)")
                break
            if "year" not in citation:
                stats["schema_issues"].append("Citations missing 'year' field (required by spec)")
                break
    
    def validate_all(self, data_dir: str, json_path: str) -> Dict:
        """Validate all PDFs against JSON output"""
        print("Loading JSON output...")
        json_data = self.load_json_output(json_path)
        
        print(f"Found {len(json_data)} documents in JSON\n")
        
        data_path = Path(data_dir)
        pdf_files = list(data_path.glob("*.pdf"))
        
        print(f"Found {len(pdf_files)} PDF files\n")
        print("="*80)
        
        for pdf_file in sorted(pdf_files):
            pdf_name = pdf_file.name
            print(f"\nValidating: {pdf_name}")
            print("-"*80)
            
            if pdf_name not in json_data:
                print(f"❌ ERROR: PDF not found in JSON output!")
                self.results["documents"][pdf_name] = {
                    "status": "MISSING_FROM_JSON",
                    "issues": [{
                        "severity": "CRITICAL",
                        "type": "missing_document",
                        "message": "Document not found in JSON output"
                    }]
                }
                self.results["total_issues"] += 1
                continue
            
            doc_json = json_data[pdf_name]
            validation_result = self.validate_document(str(pdf_file), doc_json)
            
            self.results["documents"][pdf_name] = validation_result
            self.results["documents_validated"] += 1
            self.results["total_issues"] += validation_result["total_issues"]
            
            # Print summary
            stats = validation_result["stats"]
            print(f"  Pages: PDF={stats['pdf_pages']}, JSON={stats['json_pages']}")
            print(f"  Citations: {stats['citations_found']} found, {stats['citations_validated']} validated")
            print(f"  Definitions: {stats['definitions_found']} found, {stats['definitions_validated']} validated")
            print(f"  Issues: {validation_result['total_issues']}")
            
            if validation_result["issues"]:
                print(f"\n  Issues found:")
                for issue in validation_result["issues"][:5]:  # Show first 5
                    print(f"    [{issue['severity']}] {issue['type']}: {issue['message']}")
                if len(validation_result["issues"]) > 5:
                    print(f"    ... and {len(validation_result['issues']) - 5} more issues")
        
        print("\n" + "="*80)
        print(f"\nValidation Complete!")
        print(f"Documents validated: {self.results['documents_validated']}")
        print(f"Total issues found: {self.results['total_issues']}")
        
        return self.results

if __name__ == "__main__":
    validator = ComprehensiveValidator()
    results = validator.validate_all("Data", "extracted_data.json")
    
    # Save results
    with open("comprehensive_validation_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to: comprehensive_validation_results.json")
