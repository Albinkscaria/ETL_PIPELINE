# Installation Guide

## Quick Start (5 minutes)

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Key

Create `.env` file:

```bash
GEMINI_API_KEY=your_api_key_here
```

### 3. Run Pipeline

```bash
python main.py
```

That's it! The pipeline will process all PDFs in the `Data/` directory.

---

## Full Installation (with all features)

### Prerequisites

- Python 3.9+ (3.12 recommended)
- 4GB RAM minimum (8GB recommended)
- 500MB disk space

### Step 1: Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate
```

### Step 2: Install Core Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- PDF processing (pdfplumber, PyMuPDF, pypdf)
- AI enhancement (google-generativeai)
- Text processing (fuzzywuzzy, python-Levenshtein)
- Schema validation (jsonschema)
- Testing (pytest, pytest-cov)

### Step 3: Install Optional Components

#### A. OCR Support (for scanned PDFs)

**Windows:**
1. Download Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
2. Install to: `C:\Program Files\Tesseract-OCR`
3. Add to PATH

**macOS:**
```bash
brew install tesseract tesseract-lang
```

**Linux:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-ara
```

Verify installation:
```bash
tesseract --version
```

#### B. NER Model (for entity recognition)

```bash
python -m spacy download en_core_web_sm
```

#### C. Embeddings (for semantic similarity)

Already included in requirements.txt. First run will download model automatically.

### Step 4: Configure

Edit `config.json`:

```json
{
  "pdf_directory": "Data",
  "output_file": "extracted_data.json",
  "use_ai_enhancement": false,
  "enable_ocr": true,
  "enable_ner": false,
  "use_embeddings": true,
  "enable_human_review_queue": true
}
```

Create `.env`:

```bash
GEMINI_API_KEY=your_gemini_api_key
```

Get Gemini API key: https://makersuite.google.com/app/apikey

### Step 5: Verify Installation

```bash
# Run tests
python run_tests.py

# Process single PDF
python test_single_pdf.py
```

---

## Docker Installation (Recommended for Production)

### Build Image

```bash
docker build -t uae-etl-pipeline .
```

### Run Container

```bash
docker run \
  -v $(pwd)/Data:/app/Data \
  -v $(pwd)/output:/app/output \
  -e GEMINI_API_KEY=your_key \
  uae-etl-pipeline
```

---

## Troubleshooting

### Issue: "No module named 'pytesseract'"

**Solution:**
```bash
pip install pytesseract
```

### Issue: "tesseract is not installed"

**Solution:** Install Tesseract OCR (see Step 3A above)

### Issue: "Can't find model 'en_core_web_sm'"

**Solution:**
```bash
python -m spacy download en_core_web_sm
```

### Issue: "Invalid API key"

**Solution:** Check `.env` file has correct `GEMINI_API_KEY`

### Issue: "Out of memory"

**Solution:** 
- Process fewer PDFs at once
- Disable AI enhancement: `"use_ai_enhancement": false`
- Increase system RAM

### Issue: "Permission denied"

**Solution:**
```bash
# Windows
icacls Data /grant Everyone:F

# macOS/Linux
chmod -R 755 Data
```

---

## Configuration Options

### Minimal (Fast, No AI)

```json
{
  "use_ai_enhancement": false,
  "enable_ocr": false,
  "enable_ner": false,
  "use_embeddings": false
}
```

Processing time: ~2 seconds/document

### Balanced (Recommended)

```json
{
  "use_ai_enhancement": false,
  "enable_ocr": true,
  "enable_ner": false,
  "use_embeddings": true
}
```

Processing time: ~5 seconds/document

### Maximum Accuracy (Slow)

```json
{
  "use_ai_enhancement": true,
  "enable_ocr": true,
  "enable_ner": true,
  "use_embeddings": true
}
```

Processing time: ~15 seconds/document

---

## Next Steps

1. **Test on sample PDF:**
   ```bash
   python test_single_pdf.py
   ```

2. **Run full pipeline:**
   ```bash
   python main.py
   ```

3. **Review output:**
   ```bash
   cat extracted_data.json
   ```

4. **Check review queue:**
   ```bash
   ls review_queue/
   ```

---

## Support

For issues, check:
1. This installation guide
2. README.md
3. GitHub Issues

Happy extracting! 🚀
