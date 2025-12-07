# Specific Discrepancy Examples

## Real Examples from Validation

This document shows actual examples of discrepancies found between the PDFs and JSON output.

---

## Example 1: Missing Definition - "Department of Finance"

**Document**: Cabinet Resolution No. (12) of 2025  
**Issue**: Term not found on specified page

**JSON Output Says**:
```json
{
  "term": "Department of Finance",
  "definition": "The official body in charge of financial affairs in the local emirate.",
  "page": 1,
  "confidence": 0.95,
  "extraction_method": "pymupdf_layout"
}
```

**Reality**: When checking page 1 of the PDF, the exact term "Department of Finance" does not appear on that page.

**Likely Cause**: 
- Term may appear on a different page
- Text extraction may have captured it from a different location
- Deduplication may have merged it from multiple pages

---

## Example 2: Missing Definition - "Investment Business"

**Document**: Cabinet Resolution No. (34) of 2025  
**Issue**: Term not found on specified page

**JSON Output Says**:
```json
{
  "term": "Investment Business",
  "definition": "An activity that involves the management of funds or assets...",
  "page": 1,
  "confidence": 0.95,
  "extraction_method": "pymupdf_layout"
}
```

**Reality**: Page 1 does not contain the term "Investment Business" in the extracted text.

**Likely Cause**: 
- Definition may be on a later page
- Layout extraction may have misattributed the page number
- Term may appear with different formatting

---

## Example 3: Schema Field Discrepancies

### What Requirements Specify:

```json
{
  "canonical_id": "fed_decree_law_47_2022",
  "raw_text": "Federal Decree by Law No. (47) of 2022 Concerning Corporate and Business Tax",
  "normalized": "fed_decree_law_47_2022",
  "type": "federal_decree_law",
  "number": 47,
  "year": 2022,
  "title": "Concerning Corporate and Business Tax",
  "document_url": "https://uaelegislation.gov.ae/en/legislations/1582",
  "provenance": [
    {
      "doc_id": "doc_01",
      "page": 2,
      "excerpt": "...Federal Decree by Law No. (47) of 2022..."
    }
  ],
  "confidence": 0.99
}
```

### What We Actually Have:

```json
{
  "text": "Federal Decree by Law No. (47) of 2022 Regarding Taxation of Corporations and Business The Cabinet: − Having Reviewed the Constitution",
  "canonical_id": "fed_decree_law_47_2022",
  "page": 1,
  "confidence": 1.0,
  "extraction_method": "regex"
}
```

### Missing Fields:
- ❌ `raw_text` (we have `text` instead)
- ❌ `normalized` (separate from canonical_id)
- ❌ `type`
- ❌ `number`
- ❌ `year`
- ❌ `title`
- ❌ `document_url`
- ❌ `provenance` array

---

## Example 4: Root Structure Discrepancy

### Requirements Specify:

```json
{
  "source_manifest": [
    {
      "doc_id": "doc_01",
      "filename": "federal_decree_law_47_2022.pdf",
      "source_url": "https://uaelegislation.gov.ae/en/legislations/1582",
      "pages": 12,
      "ingested_at": "2025-11-29T10:00:00Z"
    }
  ],
  "citations": [
    { /* all citations from all documents */ }
  ],
  "term_definitions": [
    { /* all definitions from all documents */ }
  ]
}
```

### What We Actually Have:

```json
{
  "Cabinet Resolution No. (12) of 2025...pdf": {
    "metadata": {
      "doc_id": "cabinet_resolution_12_2025",
      "pages": 5,
      "processing_date": "2025-12-07T11:08:58.780922Z",
      "processing_time_seconds": 1.26
    },
    "citations": [ /* citations from this document only */ ],
    "term_definitions": [ /* definitions from this document only */ ]
  },
  "Cabinet Resolution No. (34) of 2025...pdf": {
    /* ... */
  }
}
```

### Key Differences:
1. ❌ No `source_manifest` at root level
2. ❌ Data organized by filename, not flat arrays
3. ❌ Citations and definitions are per-document, not global
4. ❌ Cannot easily see all citations/definitions across documents

---

## Example 5: Large Document Issues

**Document**: Cabinet Resolution No. (52) of 2017 (76 pages)  
**Issues**: 55 validation failures

**Sample Issues**:
1. "Value Added Tax (VAT)" - not found on page 1
2. "GCC States" - not found on page 1
3. "Applying States" - not found on page 1
4. "Standard Rate" - not found on page 1
5. "Relevant Goods" - not found on page 1

**Pattern**: Many definitions claim to be on page 1, but validation cannot find them.

**Likely Cause**: 
- Definitions section may start on page 2 or 3
- Page numbering may be off by 1
- Deduplication merged definitions from multiple pages

---

## Example 6: Perfect Validation

**Document**: Cabinet Resolution No. (74) of 2023  
**Result**: 100% validation (0 issues)

**What Worked**:
- 3 citations: All validated ✅
- 2 definitions: All validated ✅
- Page counts match ✅
- All fields present ✅

**Why This Worked**:
- Smaller document (31 pages)
- Clear definition section
- Less deduplication needed
- Simpler structure

---

## Example 7: Citation Success Story

**All Documents**: 100% citation validation

**Example Citation**:
```json
{
  "text": "Federal Decree Law No. (28) of 2022 on Tax Procedures, as amended",
  "canonical_id": "fed_decree_law_28_2022",
  "page": 1,
  "confidence": 1.0,
  "extraction_method": "regex"
}
```

**Validation**: ✅ Found on page 1 of PDF

**Why Citations Work**:
- Structured format (Law No. X of Year)
- Unique identifiers (numbers, years)
- Less text transformation
- No deduplication issues

---

## Example 8: Definition with Low Confidence

**Document**: Federal Decree by Law No. (47) of 2022

**JSON Output**:
```json
{
  "term": "Objection",
  "definition": "A written or electronic objection filed by the Government Authorities with the Committee in accordance with the provisions of this Resolution.",
  "page": 1,
  "confidence": 0.88,
  "extraction_method": "layout_regex"
}
```

**Validation**: ❌ Term not found on page 1

**Analysis**:
- Lower confidence (0.88 vs 0.95)
- Mixed extraction method (layout_regex)
- Suggests system was uncertain
- Validation confirms the uncertainty

---

## Example 9: Duplicate Documents

**Documents**: 
- Federal Decree by Law No. (37) of 2022 Concerning the Family Businesses.pdf
- Federal Decree by Law No. (37) of 2022 Concerning the Family Businesses (1).pdf

**Result**: Identical validation results
- Both have 18 pages
- Both have 9 citations (100% validated)
- Both have 16 definitions (44% validated)
- Both have 9 issues

**Observation**: These appear to be duplicate files, both processed separately.

---

## Example 10: Largest Document

**Document**: Federal Decree Law No. (32) of 2021 (157 pages)

**Stats**:
- Pages: 157 (largest document)
- Citations: 1 (100% validated)
- Definitions: 21 (48% validated)
- Issues: 11

**Interesting**: Despite being the largest document, it has relatively few issues. This suggests:
- Document structure is clear
- Fewer definitions to extract
- Better text extraction quality

---

## Summary of Patterns

### What Causes Validation Failures:

1. **Deduplication**: Merging definitions from multiple pages
2. **Page Attribution**: Wrong page number assigned
3. **Text Extraction**: Layout issues in multi-column documents
4. **Exact Matching**: Validation too strict (case, punctuation)
5. **Large Documents**: More pages = more opportunities for errors

### What Works Well:

1. **Citations**: Structured format, unique identifiers
2. **Small Documents**: Less complexity, fewer issues
3. **Clear Sections**: Well-defined "Definitions" sections
4. **Simple Layouts**: Single-column, clear formatting

---

## Recommendations Based on Examples

1. **Fix Page Attribution**: Ensure definitions point to correct pages
2. **Improve Validation**: Use fuzzy matching, not exact matching
3. **Track Provenance**: Record all pages where term appears
4. **Handle Duplicates**: Detect and skip duplicate files
5. **Better Deduplication**: Track which pages were merged

---

**Document Purpose**: Provide concrete examples of validation issues  
**Date**: December 7, 2025  
**Examples**: Real data from validation run
