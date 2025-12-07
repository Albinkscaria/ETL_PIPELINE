# QUICK START GUIDE

Get up and running in **2 minutes**.

## Step 1: Verify System (30 seconds)

```bash
python validate_system.py
```

Expected output:
```
✓ ALL VALIDATIONS PASSED - System is ready!
```

## Step 2: Run Pipeline (1 minute)

```bash
python main.py
```

This will:
- Process all PDFs in `Data/` directory
- Extract citations and definitions
- Generate `extracted_data.json`
- Create review queue in `review_queue/`

## Step 3: Check Results (30 seconds)

```bash
# View output
cat extracted_data.json | head -100

# Check statistics
python -c "import json; d=json.load(open('extracted_data.json')); print(f\"Citations: {d['summary']['total_citations']}, Definitions: {d['summary']['total_terms']}\")"

# Check review queue
ls review_queue/
```

## That's It!

You now have:
- ✅ Extracted citations from all PDFs
- ✅ Extracted definitions from all PDFs
- ✅ Requirements-compliant JSON output
- ✅ Review queue for low-confidence items

---

## Optional: Enable Advanced Features

### Enable AI Enhancement

Edit `config.json`:
```json
{
  "use_ai_enhancement": true
}
```

Then run:
```bash
python main.py
```

### Enable NER

```bash
# Download model
python -m spacy download en_core_web_sm

# Edit config.json
{
  "enable_ner": true
}

# Run
python main.py
```

### Install FuzzyWuzzy

```bash
pip install python-Levenshtein fuzzywuzzy

# Run
python main.py
```

---

## Troubleshooting

### "No PDFs found"

```bash
# Check Data directory
ls Data/

# If empty, add PDFs
cp /path/to/pdfs/*.pdf Data/
```

### "Tesseract not found"

OCR is optional. To enable:

**Windows:** Download from https://github.com/UB-Mannheim/tesseract/wiki  
**macOS:** `brew install tesseract`  
**Linux:** `sudo apt-get install tesseract-ocr`

### "API key not found"

AI enhancement is optional. To enable:

```bash
# Create .env file
echo "GEMINI_API_KEY=your_key_here" > .env

# Edit config.json
{
  "use_ai_enhancement": true
}
```

---

## Next Steps

1. **Review output** - Check `extracted_data.json`
2. **Review queue** - Check `review_queue/*.csv` for low-confidence items
3. **Validate** - Run `python validate_system.py`
4. **Test** - Run `python run_tests.py`

---

## Need Help?

- **Installation issues**: See `INSTALLATION.md`
- **Usage questions**: See `README.md`
- **System details**: See `SYSTEM_COMPLETE.md`
- **Validation**: Run `python validate_system.py`

---

**You're all set! Start extracting.** 🚀
