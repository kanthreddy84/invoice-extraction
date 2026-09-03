# Unstructured Document Extraction – Invoice Extraction Project

**Complete Starter Dataset Package for AI-Powered Document Intelligence**

## Project Overview

This project implements an intelligent invoice extraction system combining optical character recognition (OCR), large language models (LLMs), and human-in-the-loop validation. The system automatically extracts structured data from invoices in various formats (digital PDFs, scanned documents, phone photos) and presents results to human reviewers for validation and correction.

### Key Capabilities

- **Multi-format Document Processing**: Digital PDFs, scanned images, rotated/skewed documents, low-resolution scans
- **Intelligent Field Extraction**: Vendor info, invoice numbers, dates, line items, amounts, tax, payment terms
- **OCR + AI Pipeline**: Tesseract OCR for scanned documents → Claude AI for structured extraction
- **Human-in-the-Loop Review**: Web UI for reviewers to validate and correct AI-extracted data
- **Comprehensive Benchmarking**: Ground-truth data for accuracy measurement and model evaluation

---

## Dataset Contents

### Document Statistics
- **Total Documents**: 25 invoices
- **Digital PDFs**: 17 (68%)
- **Scanned/Image-based PDFs**: 8 (32%)
- **Ground-truth Annotations**: 10 invoices with hand-labeled JSON
- **Difficulty Levels**: Easy (5), Medium (8), Hard (9), Very Hard (1), Testing-only (2)

### Special Cases Included
The dataset is deliberately comprehensive, covering:

| Category | Examples |
|----------|----------|
| **Data Variations** | Standard layouts, many line items (18+), multi-page capable, dense layouts |
| **Missing Fields** | Missing PO numbers, missing due dates, optional fields |
| **Currencies** | USD, EUR, INR with appropriate tax rates (0%, 6%, 18%) |
| **Scan Quality** | Low-resolution, skewed, 90-degree rotated, shadowed, noisy, faded, very noisy |
| **Extraction Challenges** | Discount arithmetic, duplicate-looking totals, multiple dates, unusual descriptions |

---

## Folder Structure

```
unstructured_invoice_starter_dataset/
│
├── README.md                          # This file
│
└── data/
    │
    ├── raw/                           # Source documents (upload these)
    │   ├── invoice_001.pdf            # Digital PDF
    │   ├── invoice_002.pdf            # Digital PDF
    │   ├── ...
    │   ├── invoice_013_scan.pdf       # Image-based / scanned
    │   ├── invoice_014_scan.pdf       # Low-resolution scan
    │   ├── ...
    │   └── invoice_025_scan.pdf       # Very noisy scan
    │
    ├── ground_truth/                  # Gold-standard annotations
    │   ├── invoice_001.json           # Hand-labeled extraction
    │   ├── invoice_002.json           # Hand-labeled extraction
    │   ├── ...
    │   └── invoice_010.json           # Hand-labeled extraction
    │
    ├── processed/                     # Outputs go here
    │   ├── ocr_results/               # Raw OCR text per document
    │   ├── extractions/               # AI model JSON outputs
    │   ├── validated/                 # Human-reviewed & corrected extractions
    │   └── metrics/                   # Benchmark results
    │
    └── benchmark/                     # Reference files
        ├── expected_schema.json       # Expected output format
        ├── benchmark_manifest.json    # Complete document registry
        └── document_index.csv         # Quick reference (id, file, type, difficulty)
```

---

## Expected Data Schema

All invoice extractions should conform to this JSON schema:

```json
{
  "document_id": "invoice_001",
  "invoice_number": "INV-2026-0001",
  "invoice_date": "2026-01-12",
  "due_date": "2026-02-11",
  "vendor_name": "Acme Office Supplies",
  "vendor_address": "125 Main Street, Chicago, IL 60601",
  "customer_name": "ABC Healthcare",
  "customer_address": "500 Market Street, Detroit, MI 48226",
  "purchase_order_number": "PO-98001",
  "currency": "USD",
  "subtotal": 520.0,
  "discount": 0.0,
  "tax": 31.2,
  "total": 551.2,
  "payment_terms": "Net 30",
  "line_items": [
    {
      "description": "Desk Lamp",
      "quantity": 10.0,
      "unit_price": 25.0,
      "amount": 250.0
    }
  ]
}
```

### Field Types and Constraints

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `invoice_number` | string | Yes | Unique identifier for the invoice |
| `invoice_date` | date (YYYY-MM-DD) | Yes | Date invoice was issued |
| `due_date` | date (YYYY-MM-DD) | No | Payment due date |
| `vendor_name` | string | Yes | Business providing goods/services |
| `vendor_address` | string | No | Full mailing address |
| `customer_name` | string | Yes | Business receiving goods/services |
| `customer_address` | string | No | Full mailing address |
| `purchase_order_number` | string | No | PO reference if present |
| `currency` | string | Yes | ISO 4217 code (USD, EUR, INR, etc.) |
| `subtotal` | decimal | Yes | Sum of line item amounts |
| `discount` | decimal | No | Total discount amount |
| `tax` | decimal | No | Total tax amount |
| `total` | decimal | **Always required** | Final amount due |
| `payment_terms` | string | No | Terms text (e.g., "Net 30", "2/10 Net 30") |
| `line_items` | array | Yes | One or more line items |

### Line Item Fields

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `description` | string | Yes | Item description |
| `quantity` | decimal | No | Units ordered |
| `unit_price` | decimal | No | Price per unit |
| `amount` | decimal | Yes | Line total (quantity × unit_price) |

---

## Getting Started

### 1. Environment Setup

```bash
# Python 3.9+
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn python-multipart pydantic
pip install pytesseract pillow pdf2image
pip install anthropic  # For Claude API calls
```

### 2. Upload Documents for Processing

Place new invoices in `data/raw/`:

```bash
# Copy your invoice PDFs
cp your_invoices/*.pdf data/raw/

# The system will process all files in this directory
```

### 3. Run Extraction Pipeline

```python
# Pseudocode for extraction pipeline
from pathlib import Path
from invoice_extractor import extract_invoice_batch

# Extract from raw documents
result = extract_invoice_batch(
    input_dir="data/raw",
    output_dir="data/processed/extractions",
    ocr_output_dir="data/processed/ocr_results"
)

print(f"Processed: {result['total']}")
print(f"Successful: {result['successful']}")
print(f"Errors: {result['errors']}")
```

### 4. Review Extractions via Web UI

```bash
# Start FastAPI backend
uvicorn main:app --reload --port 8000

# Start React frontend (separate terminal)
cd frontend
npm start
```

Open http://localhost:3000 to begin reviewing extractions.

### 5. Generate Benchmarks (First 10 Documents Only)

```python
from benchmarking import compare_extraction_to_ground_truth

# Benchmark against ground truth
metrics = compare_extraction_to_ground_truth(
    extracted_dir="data/processed/validated",  # After human review
    ground_truth_dir="data/ground_truth",
    output_file="data/processed/metrics/benchmark_results.json"
)

print(f"Field Accuracy: {metrics['field_accuracy']:.2%}")
print(f"Critical Field Accuracy: {metrics['critical_field_accuracy']:.2%}")
print(f"Line Item Accuracy: {metrics['line_item_accuracy']:.2%}")
```

---

## Benchmarking Guide

### Evaluation Methodology

**Use documents `invoice_001` through `invoice_010` for your benchmark.**

These 10 invoices have hand-labeled ground-truth JSON files that serve as the gold standard.

### Recommended Normalization

Before comparing extracted values to ground truth, apply these transformations:

```python
def normalize_for_comparison(extracted, ground_truth):
    # Text fields
    text = lambda s: s.strip().lower() if s else None
    
    # Dates: normalize to YYYY-MM-DD
    date = lambda s: s if s and len(s) == 10 else None
    
    # Numeric fields: remove symbols, parse as float
    number = lambda s: float(s.replace('$', '').replace(',', '')) if s else None
    
    # Currency: uppercase
    currency = lambda s: s.upper() if s else None
    
    # Line items: match by normalized description + rounded amount
    line_item = lambda items: [
        (text(item['description']), round(number(item['amount']), 2))
        for item in items
    ]
    
    return {
        'invoice_number': text(extracted['invoice_number']),
        'dates': date(extracted['invoice_date']),
        'amounts': number(extracted['total']),
        'line_items': line_item(extracted['line_items'])
    }
```

### Metrics to Report

| Metric | Definition |
|--------|-----------|
| **Field Accuracy** | Correct fields / Total expected fields |
| **Critical Field Accuracy** | Accuracy on required fields only (invoice #, dates, vendor, customer, total) |
| **Line Item Accuracy** | Correctly extracted line items / Total line items across all documents |
| **Review Rate** | Number of documents sent to human review / Total documents |
| **Auto-Approved Accuracy** | Accuracy on auto-approved (zero-review) documents |
| **False Auto-Approval Rate** | Incorrect auto-approvals / Total auto-approvals |

### Example Benchmark Output

```json
{
  "benchmark_date": "2026-09-01",
  "model": "claude-3-5-sonnet",
  "documents_evaluated": 10,
  "total_fields": 210,
  "correct_fields": 195,
  "field_accuracy": 0.9286,
  "critical_field_accuracy": 0.95,
  "line_item_accuracy": 0.92,
  "review_rate": 0.25,
  "auto_approved_accuracy": 0.98,
  "false_auto_approval_rate": 0.02,
  "processing_time_seconds": 45.3,
  "ocr_processing_time_seconds": 12.1
}
```

---

## Extraction Pipeline Overview

### High-Level Flow

```
Raw Invoice PDF
    ↓
[Digital or Scanned Check]
    ↓
[OCR (Tesseract if scanned)]
    ↓
[Text Extraction]
    ↓
[Claude AI → Structured JSON]
    ↓
[Validation Rules Check]
    ↓
[Human Review UI]
    ↓
[Corrected Output JSON]
    ↓
[Store in validated/ directory]
```

### Document Type Handling

**Digital PDFs** (invoice_001-012, 020-024):
- Extract text directly using PyPDF2 or pdfplumber
- Skip OCR for efficiency
- Faster processing, higher accuracy

**Scanned/Image-based PDFs** (invoice_013-019, 025):
- Convert to images using pdf2image
- Run Tesseract OCR
- Handle rotation, skew, noise
- Longer processing, may need review
- 32% of dataset exercises OCR

---

## Human-in-the-Loop Review Workflow

### Review UI Features

1. **Side-by-side Comparison**
   - Original document (left pane)
   - Extracted JSON (right pane)
   - Highlight confidence scores

2. **Edit Capabilities**
   - Modify any extracted field
   - Add/remove/edit line items
   - Flag uncertain extractions

3. **Batch Operations**
   - Mark as approved
   - Mark for follow-up
   - Generate corrected output

4. **Quality Control**
   - Track reviewer edits
   - Measure inter-reviewer agreement
   - Log reasons for corrections

### Review Checklist

- [ ] Invoice number matches original
- [ ] All dates are formatted consistently
- [ ] Vendor and customer names match
- [ ] Currency and amounts are correct
- [ ] Line items match document content
- [ ] Tax calculation is accurate
- [ ] Total amount is correct
- [ ] All required fields are present

---

## File Naming Conventions

### Raw Documents
- `invoice_NNN.pdf` — Digital PDFs (e.g., invoice_001.pdf)
- `invoice_NNN_scan.pdf` — Scanned/image-based (e.g., invoice_013_scan.pdf)

### Extracted Data
- `invoice_NNN.json` — Extracted structured data (same base name as PDF)

### Processed Outputs
- `ocr_results/invoice_NNN.txt` — Raw OCR text
- `extractions/invoice_NNN.json` — AI model output (before review)
- `validated/invoice_NNN.json` — After human validation
- `metrics/invoice_NNN_metrics.json` — Per-document accuracy metrics

---

## Known Challenges & Edge Cases

### OCR Challenges
- **Low-resolution scans**: May miss small text or numbers
- **Skewed documents**: Tesseract has trouble with angles > 45°
- **Rotated 90°**: Must be auto-corrected before OCR
- **Shadows/glare**: Phone photo artifacts
- **Faded text**: Reduced contrast makes OCR difficult

### Extraction Challenges
- **Dense layouts**: Multiple columns, dense text
- **Unusual formats**: Non-standard invoice layouts
- **Ambiguous fields**: Multiple dates (invoice date vs. due date)
- **Duplicate numbers**: Invoice totals that look like other amounts
- **Symbol confusion**: Currency symbols, discount notations

### Arithmetic Validation
- Always recalculate: `subtotal + tax - discount = total`
- Watch for rounding errors in floating-point arithmetic
- Some invoices intentionally have discount arithmetic as a test case

---

## Integration with FastAPI + React

### Backend API Endpoints

```
POST /api/extract           # Submit document for extraction
GET  /api/documents         # List all processed documents
GET  /api/documents/{id}    # Get extraction result
PUT  /api/documents/{id}    # Update extraction after review
POST /api/validate          # Run validation rules
GET  /api/benchmark         # Generate benchmark metrics
```

### React Components

- **DocumentUpload**: Drag-and-drop or file picker
- **ExtractionViewer**: Display PDF + extracted JSON
- **FieldEditor**: Inline editing of extraction results
- **LineItemTable**: Edit line items with validation
- **BenchmarkDashboard**: View accuracy metrics and trends

---

## Performance Expectations

### Processing Time (Per Document)

| Step | Time | Notes |
|------|------|-------|
| OCR (if scanned) | 5-15s | Depends on image quality |
| AI Extraction | 2-4s | Claude API call |
| Validation | 0.5s | Local rule checks |
| Human Review | 1-3m | Depends on complexity |

**Total for 25 documents**: ~2-3 minutes (automated) + variable human time

### Accuracy Targets

- **Digital PDFs**: >95% field accuracy
- **Standard scans**: >90% field accuracy
- **Difficult scans**: 75-85% (requires review)
- **Overall**: Target 92%+ after human review

---

## Data Privacy & Security

⚠️ **Important**: These invoices are **100% synthetic** and contain no real customer, vendor, or financial information. They are safe to use in development, testing, and public demonstrations.

- Use this dataset freely in your project
- Share with team members and stakeholders without concern
- Reference in documentation and technical reports
- No anonymization needed

---

## Support & Troubleshooting

### Common Issues

**Q: OCR output is very poor for scan_013**
- A: Tesseract sometimes struggles with specific fonts. Consider preprocessing: deskew, denoise, or increase contrast.

**Q: Claude extraction is missing fields**
- A: Check OCR quality first. If OCR text is missing, extraction will fail downstream. Also verify the invoice has those fields (some are optional).

**Q: Benchmark scores don't add up**
- A: Remember to normalize numeric fields before comparison. Rounding, currency symbols, and formatting matter.

**Q: How do I add more training data?**
- A: Generate synthetic invoices using the same format, place in `data/raw/`, and create corresponding `data/ground_truth/` JSON files.

### Debugging

Enable verbose logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check intermediate outputs:
- OCR text: `data/processed/ocr_results/`
- Raw extractions: `data/processed/extractions/`
- Validation results: Check logs for field-by-field output

---

## Next Steps

1. **Set up environment** — Install Python dependencies
2. **Review dataset** — Open a few PDFs and corresponding ground-truth JSONs
3. **Run extraction** — Process first 3-5 documents
4. **Validate output** — Use web UI to review and correct
5. **Benchmark** — Compare against ground truth for documents 001-010
6. **Iterate** — Refine extraction logic based on results
7. **Scale** — Process remaining documents (011-025)

---

## Citation & References

**Dataset Version**: 1.0  
**Created**: 2026  
**Documents**: 25 invoices (17 digital, 8 scanned)  
**Ground Truth**: 10 hand-labeled invoices  
**Difficulty Levels**: 5 easy, 8 medium, 9 hard, 1 very hard, 2 testing-only  
**Use Cases**: AI model development, benchmarking, human-in-the-loop validation

For more information on invoice extraction best practices, see:
- Tesseract OCR documentation
- Claude API documentation
- PDFX, pdfplumber, or similar Python PDF libraries

---

**Last Updated**: 2026-09-01  
**Maintainer**: AI Projects Team  
**License**: MIT (for dataset) | Modify as needed for your organization
