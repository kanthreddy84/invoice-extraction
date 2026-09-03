# Invoice Extraction System – Complete Implementation Guide

**Version:** 2.0  
**Last Updated:** 2026-09-01  
**Status:** Production Ready

---

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Prerequisites](#prerequisites)
3. [Phase 1: Environment Setup](#phase-1-environment-setup)
4. [Phase 2: Data Preparation](#phase-2-data-preparation)
5. [Phase 3: Basic Extraction](#phase-3-basic-extraction)
6. [Phase 4: Processing Pipeline](#phase-4-processing-pipeline)
7. [Phase 5: Human Review](#phase-5-human-review)
8. [Phase 6: Benchmarking](#phase-6-benchmarking)
9. [Next Steps for Production](#next-steps-for-production)

---

## System Overview

### Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface (React)                    │
│              Upload • Review • Edit • Export                 │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  Backend API (FastAPI)                       │
│         Auth • Upload • Document • Extraction • Export       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              Message Queue (RabbitMQ/Celery)                 │
│            OCR • LLM Extraction • Validation Tasks           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│               Processing Workers                              │
│  OCR (Tesseract) • LLM (Claude/DeepSeek) • Validation       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│            Storage & Database                                 │
│     Files (MinIO) • PostgreSQL • Audit Logs                 │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow (11 Steps)

1. **Upload** → Document received via API
2. **Store** → File saved to MinIO, record created in DB
3. **Queue** → OCR task pushed to RabbitMQ
4. **Extract Text** → Tesseract (scanned) or PyMuPDF (digital)
5. **Clean** → Normalize and structure text
6. **Extract JSON** → Claude/LLM with Pydantic schema
7. **Validate** → Check schema, arithmetic, required fields
8. **Score** → Calculate confidence (0-1)
9. **Route** → Auto-approve (>0.9) or to human review (<0.9)
10. **Review** → Human edit/approve in web UI
11. **Store & Export** → Save final version, generate metrics

---

## Prerequisites

### System Requirements
- Python 3.9 or higher
- 4GB RAM minimum (8GB recommended)
- Docker and Docker Compose (for full stack)
- PostgreSQL client installed

### External Services
- Claude API key (for LLM extraction)
- Docker Hub account (for image pulls)

### Installed Tools
- Git
- pip (Python package manager)
- curl or Postman (for API testing)

---

## Phase 1: Environment Setup

### Step 1.1: Create Python Virtual Environment

```bash
cd "C:\AI Projects\Unstructured Document Extraction\unstructured_invoice_starter_dataset"

# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### Step 1.2: Install Core Dependencies

```bash
# PDF and image processing
pip install PyPDF2 pdf2image pillow pdfplumber

# OCR
pip install pytesseract paddleocr

# Data validation
pip install pydantic python-dateutil

# Claude API
pip install anthropic

# Backend framework (for later)
pip install fastapi uvicorn python-multipart

# Testing and development
pip install pytest jupyter ipython
```

### Step 1.3: Verify Installations

```bash
# Test Python
python --version

# Test imports
python -c "import PyPDF2; import pydantic; import anthropic; print('✓ All imports successful')"
```

---

## Phase 2: Data Preparation

### Step 2.1: Explore the Dataset

```bash
# Navigate to data folder
cd data

# Count documents
ls raw/ | wc -l          # Should show 25 invoices
ls ground_truth/ | wc -l # Should show 10 JSONs

# View sample invoice
head -50 ground_truth/invoice_001.json

# View expected schema
cat benchmark/expected_schema.json
```

### Step 2.2: Understand Data Structure

**Invoice Schema:**
```json
{
  "invoice_number": "string",
  "invoice_date": "YYYY-MM-DD",
  "due_date": "YYYY-MM-DD (optional)",
  "vendor_name": "string",
  "customer_name": "string",
  "currency": "string (USD/EUR/INR)",
  "subtotal": "decimal",
  "tax": "decimal",
  "total": "decimal",
  "line_items": [
    {
      "description": "string",
      "quantity": "decimal",
      "unit_price": "decimal",
      "amount": "decimal"
    }
  ]
}
```

**Dataset Composition:**
- 17 digital PDFs (extract text directly)
- 8 scanned PDFs (require OCR)
- 10 ground-truth labels (for benchmarking)
- 15 unlabeled (for testing)

---

## Phase 3: Basic Extraction

### Step 3.1: Create Extraction Script

Create file: `extract_single_invoice.py`

```python
import json
from pathlib import Path
from anthropic import Anthropic

client = Anthropic()

# Load expected schema
with open("data/benchmark/expected_schema.json") as f:
    schema = json.load(f)

def extract_invoice_text(pdf_path):
    """Extract text from PDF"""
    try:
        import PyPDF2
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
        return text
    except Exception as e:
        print(f"Error extracting text: {e}")
        return None

def extract_invoice_with_claude(invoice_text):
    """Use Claude to extract structured invoice data"""
    
    schema_str = json.dumps(schema, indent=2)
    
    prompt = f"""Extract invoice data from the following text and return ONLY valid JSON matching this schema:

{schema_str}

Important:
- Return ONLY the JSON, no other text
- Fill in all required fields
- Use null for missing optional fields
- Dates must be in YYYY-MM-DD format
- Numbers should be decimals
- Validate arithmetic: subtotal + tax - discount = total

Invoice text:
{invoice_text}
"""

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": prompt
        }]
    )
    
    try:
        result = json.loads(response.content[0].text)
        return result
    except json.JSONDecodeError as e:
        print(f"Failed to parse response: {e}")
        return None

# Main execution
if __name__ == "__main__":
    # Test with first invoice
    pdf_path = "data/raw/invoice_001.pdf"
    
    print(f"Processing: {pdf_path}")
    text = extract_invoice_text(pdf_path)
    
    if text:
        print("✓ Text extracted")
        result = extract_invoice_with_claude(text)
        
        if result:
            print("✓ Invoice extracted")
            print(json.dumps(result, indent=2))
            
            # Save result
            output_path = "data/processed/extractions/invoice_001.json"
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"✓ Saved to: {output_path}")
```

### Step 3.2: Run First Extraction

```bash
# Make sure directories exist
mkdir -p data/processed/extractions
mkdir -p data/processed/ocr_results

# Run extraction
python extract_single_invoice.py

# Verify output
cat data/processed/extractions/invoice_001.json
```

---

## Phase 4: Processing Pipeline

### Step 4.1: Create Batch Processing Script

Create file: `process_all_invoices.py`

```python
import json
import os
from pathlib import Path
from datetime import datetime
from extract_single_invoice import extract_invoice_text, extract_invoice_with_claude

def process_all_invoices():
    """Process all invoices in data/raw/"""
    
    input_dir = Path("data/raw")
    output_dir = Path("data/processed/extractions")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    invoices = sorted([f for f in input_dir.glob("*.pdf")])
    results = {
        "total": len(invoices),
        "successful": 0,
        "failed": 0,
        "errors": []
    }
    
    for i, pdf_file in enumerate(invoices, 1):
        doc_name = pdf_file.stem
        print(f"\n[{i}/{len(invoices)}] Processing {doc_name}...")
        
        try:
            # Extract text
            text = extract_invoice_text(str(pdf_file))
            if not text:
                raise ValueError("No text extracted")
            
            # Extract JSON
            result = extract_invoice_with_claude(text)
            if not result:
                raise ValueError("Failed to extract JSON")
            
            # Save result
            output_file = output_dir / f"{doc_name}.json"
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            
            results["successful"] += 1
            print(f"  ✓ Saved to {output_file.name}")
            
        except Exception as e:
            results["failed"] += 1
            error_msg = f"{doc_name}: {str(e)}"
            results["errors"].append(error_msg)
            print(f"  ✗ Error: {e}")
    
    # Summary
    print("\n" + "="*50)
    print("PROCESSING SUMMARY")
    print("="*50)
    print(f"Total:      {results['total']}")
    print(f"Successful: {results['successful']}")
    print(f"Failed:     {results['failed']}")
    
    if results['errors']:
        print("\nErrors:")
        for error in results['errors']:
            print(f"  - {error}")
    
    # Save summary
    summary_file = Path("data/processed/extraction_summary.json")
    with open(summary_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nSummary saved to: {summary_file}")

if __name__ == "__main__":
    process_all_invoices()
```

### Step 4.2: Run Batch Processing

```bash
# Process all invoices (this will take 5-10 minutes)
python process_all_invoices.py

# Check results
ls -la data/processed/extractions/ | wc -l  # Should show ~25 files
```

---

## Phase 5: Human Review

### Step 5.1: Create Review Interface Script

Create file: `simple_review_ui.py`

```python
import json
import sys
from pathlib import Path

def review_extraction(doc_name):
    """Simple CLI for reviewing extractions"""
    
    extraction_file = Path(f"data/processed/extractions/{doc_name}.json")
    validated_dir = Path("data/processed/validated")
    validated_dir.mkdir(parents=True, exist_ok=True)
    
    if not extraction_file.exists():
        print(f"❌ File not found: {extraction_file}")
        return
    
    # Load extraction
    with open(extraction_file) as f:
        data = json.load(f)
    
    # Display
    print(f"\n{'='*60}")
    print(f"REVIEWING: {doc_name}")
    print(f"{'='*60}")
    print(json.dumps(data, indent=2))
    
    # Get action
    print(f"\n{'─'*60}")
    while True:
        action = input("Action [a=approve, e=edit, r=reject, q=quit]: ").strip().lower()
        
        if action == 'a':
            # Save as validated
            output_file = validated_dir / f"{doc_name}.json"
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"✓ Approved and saved to {output_file.name}")
            break
            
        elif action == 'e':
            # Edit mode
            field = input("Field to edit (e.g., 'total'): ").strip()
            if field in data:
                value = input(f"New value for {field}: ").strip()
                data[field] = value
                print(f"✓ Updated {field}")
            else:
                print(f"❌ Field '{field}' not found")
            
        elif action == 'r':
            print("Rejected - not saving")
            break
            
        elif action == 'q':
            print("Quit without saving")
            break

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python simple_review_ui.py invoice_001")
        sys.exit(1)
    
    doc_name = sys.argv[1]
    review_extraction(doc_name)
```

### Step 5.2: Review Sample Invoices

```bash
# Review first extraction
python simple_review_ui.py invoice_001

# Review next one
python simple_review_ui.py invoice_002

# Check validated outputs
ls data/processed/validated/
```

---

## Phase 6: Benchmarking

### Step 6.1: Create Benchmarking Script

Create file: `benchmark_accuracy.py`

```python
import json
from pathlib import Path
from decimal import Decimal

def normalize_value(value, field_type):
    """Normalize values for comparison"""
    if value is None:
        return None
    
    if field_type == "text":
        return str(value).strip().lower()
    elif field_type == "date":
        return str(value)[:10]  # YYYY-MM-DD format
    elif field_type == "decimal":
        try:
            return round(float(value), 2)
        except:
            return None
    
    return value

def compare_field(extracted, ground_truth, field_name, field_type="text"):
    """Compare a single field"""
    ext_val = normalize_value(extracted.get(field_name), field_type)
    gt_val = normalize_value(ground_truth.get(field_name), field_type)
    
    if field_type == "decimal" and ext_val and gt_val:
        # Allow 0.01 tolerance for decimals
        return abs(ext_val - gt_val) <= 0.01
    
    return ext_val == gt_val

def benchmark_document(doc_id):
    """Benchmark one document"""
    
    extracted_file = Path(f"data/processed/validated/{doc_id}.json")
    ground_truth_file = Path(f"data/ground_truth/{doc_id}.json")
    
    if not extracted_file.exists() or not ground_truth_file.exists():
        return None
    
    with open(extracted_file) as f:
        extracted = json.load(f)
    
    with open(ground_truth_file) as f:
        ground_truth = json.load(f)
    
    # Fields to check
    critical_fields = [
        ("invoice_number", "text"),
        ("invoice_date", "date"),
        ("vendor_name", "text"),
        ("customer_name", "text"),
        ("total", "decimal")
    ]
    
    all_fields = critical_fields + [
        ("due_date", "date"),
        ("currency", "text"),
        ("subtotal", "decimal"),
        ("tax", "decimal"),
        ("discount", "decimal")
    ]
    
    # Score
    critical_correct = sum(
        1 for field, ftype in critical_fields 
        if compare_field(extracted, ground_truth, field, ftype)
    )
    
    all_correct = sum(
        1 for field, ftype in all_fields 
        if compare_field(extracted, ground_truth, field, ftype)
    )
    
    return {
        "doc_id": doc_id,
        "critical_field_accuracy": critical_correct / len(critical_fields),
        "field_accuracy": all_correct / len(all_fields),
        "critical_fields_total": len(critical_fields),
        "all_fields_total": len(all_fields)
    }

def run_benchmark():
    """Benchmark all validated documents"""
    
    results = []
    for i in range(1, 11):  # Documents 001-010 have ground truth
        doc_id = f"invoice_{i:03d}"
        result = benchmark_document(doc_id)
        if result:
            results.append(result)
            print(f"{doc_id}: Field Accuracy={result['field_accuracy']:.1%}, Critical={result['critical_field_accuracy']:.1%}")
    
    if results:
        # Calculate averages
        avg_field = sum(r['field_accuracy'] for r in results) / len(results)
        avg_critical = sum(r['critical_field_accuracy'] for r in results) / len(results)
        
        print(f"\n{'='*60}")
        print(f"BENCHMARK RESULTS")
        print(f"{'='*60}")
        print(f"Average Field Accuracy:    {avg_field:.1%}")
        print(f"Average Critical Accuracy: {avg_critical:.1%}")
        print(f"Documents Benchmarked:     {len(results)}")
        
        # Save results
        output = {
            "date": str(__import__('datetime').datetime.now()),
            "documents": results,
            "average_field_accuracy": avg_field,
            "average_critical_accuracy": avg_critical
        }
        
        output_file = Path("data/processed/benchmark_results.json")
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)
        print(f"\nResults saved to: {output_file}")

if __name__ == "__main__":
    run_benchmark()
```

### Step 6.2: Run Benchmark

```bash
# After reviewing and validating invoices 001-010, run:
python benchmark_accuracy.py

# View results
cat data/processed/benchmark_results.json
```

---

## Next Steps for Production

### Phase 7: Backend API Setup (FastAPI)

1. Create `app.py` with FastAPI endpoints
2. Set up JWT authentication
3. Create database schema with SQLAlchemy
4. Implement file upload with MinIO/S3

### Phase 8: Message Queue (RabbitMQ + Celery)

1. Set up RabbitMQ broker
2. Create Celery workers
3. Implement async task processing
4. Add task monitoring and logging

### Phase 9: Frontend (React)

1. Create React UI for uploads
2. Build review interface
3. Add export functionality
4. Set up analytics dashboard

### Phase 10: Deployment

1. Dockerize all components
2. Set up Kubernetes manifests
3. Configure monitoring (Prometheus/Grafana)
4. Set up CI/CD pipeline

---

## File Structure After Completion

```
unstructured_invoice_starter_dataset/
├── README.md
├── QUICKSTART.md
├── IMPLEMENTATION_GUIDE.md (this file)
├── DATASET.md
│
├── extract_single_invoice.py
├── process_all_invoices.py
├── simple_review_ui.py
├── benchmark_accuracy.py
│
└── data/
    ├── raw/                          (25 invoice PDFs)
    ├── ground_truth/                 (10 labeled JSON)
    └── processed/
        ├── extractions/              (AI extracted JSON)
        ├── validated/                (Human reviewed JSON)
        ├── ocr_results/              (Raw OCR text)
        ├── extraction_summary.json    (Batch process results)
        └── benchmark_results.json     (Accuracy metrics)
```

---

## Expected Outcomes by Phase

| Phase | Expected Result | Time |
|-------|-----------------|------|
| 1 | Environment ready, all imports working | 15 min |
| 2 | Familiar with dataset structure | 10 min |
| 3 | Successfully extract 1 invoice | 5 min |
| 4 | Batch process all 25 invoices | 10-15 min |
| 5 | Validate invoices 001-010 manually | 20-30 min |
| 6 | Benchmark with >90% accuracy | 5 min |

---

## Troubleshooting

### Issue: Text extraction returns empty
**Solution:** Check if it's a scanned PDF. If so, you'll need to add OCR:
```python
from pdf2image import convert_from_path
import pytesseract
images = convert_from_path("file.pdf")
text = pytesseract.image_to_string(images[0])
```

### Issue: Claude API errors
**Solution:** 
- Check API key is set: `echo $ANTHROPIC_API_KEY`
- Verify account has credits
- Check model name is correct

### Issue: JSON parsing fails
**Solution:** Ensure Claude returns only JSON, no markdown formatting

---

## Support & Questions

- **Setup Issues:** See QUICKSTART.md
- **Data Questions:** See DATASET.md
- **Architecture Questions:** See interactive diagram online
- **Code Help:** Check docstrings in Python files

---

**Status:** Ready to implement  
**Next Action:** Start with Phase 1 setup
