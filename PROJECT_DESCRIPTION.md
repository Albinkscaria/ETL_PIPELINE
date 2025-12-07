# UAE Legal Documents ETL Pipeline

**Automated extraction of citations and legal definitions from UAE government PDF documents**

## Overview

A production-ready ETL (Extract, Transform, Load) pipeline that processes UAE legal documents (Federal Laws, Cabinet Resolutions, Decrees) to extract structured data including legal citations and term definitions. Built with Python, featuring deterministic extraction, smart deduplication, and optional AI enhancement.

## Key Features

- **Deterministic Extraction**: Regex patterns + PyMuPDF layout analysis for high-accuracy extraction
- **Smart Deduplication**: Fuzzy matching with semantic embeddings (56% reduction in duplicates)
- **Multi-Method Extraction**: Combines regex, layout analysis, and optional AI enhancement (Gemini/Groq)
- **OCR Fallback**: Tesseract integration for scanned documents
- **Human Review Queue**: Flags low-confidence extractions for manual review
- **Document-Organized Output**: JSON structured by source PDF for easy navigation

## What It Extracts

- **Legal Citations**: References to other laws, decrees, and resolutions with canonical IDs
- **Term Definitions**: Legal terminology with definitions, page numbers, and confidence scores
- **Metadata**: Document info, processing timestamps, extraction methods

## Tech Stack

- **Core**: Python 3.8+, PyMuPDF, pypdf
- **ML/NLP**: SpaCy, sentence-transformers, Tesseract OCR
- **AI Enhancement**: Google Gemini API (optional), Groq API (optional)
- **Deployment**: Docker support, configurable pipeline

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Add PDFs to Data/ folder
# Run pipeline
python main.py

# Output: extracted_data.json
```

## Output Format

```json
{
  "Federal Decree Law No. (32) of 2021.pdf": {
    "metadata": {
      "doc_id": "fed_decree_law_32_2021",
      "pages": 157,
      "processing_date": "2025-12-07T...",
      "processing_time_seconds": 11.2
    },
    "citations": [
      {
        "text": "Federal Law No. (1) of 1972...",
        "canonical_id": "federal_law_1_1972",
        "page": 5,
        "confidence": 1.0,
        "extraction_method": "regex"
      }
    ],
    "term_definitions": [
      {
        "term": "Commercial Company",
        "definition": "A company established for...",
        "page": 3,
        "confidence": 0.95,
        "extraction_method": "pymupdf_layout"
      }
    ]
  }
}
```

## Performance

- **Processing Speed**: ~18 seconds per document average
- **Accuracy**: 95%+ high-confidence extractions
- **Deduplication**: 40-57% reduction in duplicate entries
- **Scalability**: Handles documents from 2 to 157 pages

## Use Cases

- Legal research and analysis
- Regulatory compliance tracking
- Document cross-referencing
- Legal knowledge base construction
- Citation network analysis

## Documentation

- [Installation Guide](INSTALLATION.md)
- [Quick Start](QUICKSTART.md)
- [Full Documentation](README.md)
- [API Reference](FINAL_REPORT.md)

## License

MIT License

## Contributing

Contributions welcome! Please read our contributing guidelines before submitting PRs.

---

**Built for UAE legal document processing | Production-ready | Fully tested**
