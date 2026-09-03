# Quick Start Guide – Invoice Extraction

Get up and running with the invoice extraction pipeline in 5 minutes.

## 1. Explore the Dataset

```bash
cd unstructured_invoice_starter_dataset

# List all documents
ls data/raw/*.pdf

# View one sample extraction
cat data/ground_truth/invoice_001.json | jq .
```

**What you have:**
- **data/raw/**: 25 invoice PDFs (17 digital + 8 scanned)
- **data/ground_truth/**: 10 hand-labeled JSON ground-truth files
- **data/benchmark/**: Expected schema, manifest, and metadata

## 2. Check the Expected Schema

All extractions must match this structure:

```bash
cat data/benchmark/expected_schema.json
```

Key fields:
- `invoice_number`, `invoice_date`, `due_date` (required text/dates)
- `vendor_name`, `customer_name` (required)
- `total` (required decimal)
- `line_items[]` with `description`, `quantity`, `unit_price`, `amount`

## 3. Install Dependencies

```bash
# Python 3.9+
python -m venv venv
source venv/bin/activate  # or: venv\Scripts\activate on Windows

# Core packages
pip install fastapi uvicorn pydantic

# Document processing
pip install pytesseract pillow pdf2image PyPDF2

# Claude API
pip install anthropic

# Optional: for notebooks/debugging
pip install jupyter
```

## 4. Extract Your First Invoice

Create a simple extraction script:

```python
# extract_sample.py
import json
from anthropic import Anthropic

client = Anthropic()

# Read a PDF's text (simplified example)
# In production, use pdfplumber or PyPDF2
text = "Invoice INV-2026-0001 from Acme Office Supplies..."

# Use Claude to extract structured data
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": f"""Extract invoice data as JSON matching this schema:
        
{{
  "invoice_number": "string",
  "invoice_date": "YYYY-MM-DD",
  "vendor_name": "string",
  "customer_name": "string",
  "total": float,
  "line_items": [
    {{"description": "string", "amount": float}}
  ]
}}

Invoice text:
{text}

Return ONLY valid JSON, no other text."""
    }]
)

result = json.loads(response.content[0].text)
print(json.dumps(result, indent=2))
```

Run it:
```bash
python extract_sample.py
```

## 5. Benchmark Against Ground Truth

Compare your extraction to the first ground-truth invoice:

```python
# benchmark_sample.py
import json

# Load extraction
with open("data/ground_truth/invoice_001.json") as f:
    ground_truth = json.load(f)

# Your extraction (from above)
extracted = {
    "invoice_number": "INV-2026-0001",
    "invoice_date": "2026-01-12",
    "total": 551.2,
    # ...
}

# Simple comparison
matches = {}
for key in ["invoice_number", "invoice_date", "total"]:
    match = extracted.get(key) == ground_truth.get(key)
    matches[key] = match
    status = "✓" if match else "✗"
    print(f"{status} {key}: {extracted.get(key)} vs {ground_truth.get(key)}")

accuracy = sum(matches.values()) / len(matches)
print(f"\nAccuracy: {accuracy:.0%}")
```

## 6. Launch the Web UI (Optional)

```bash
# Backend (FastAPI)
uvicorn main:app --reload --port 8000

# Frontend (React, in a separate terminal)
cd frontend
npm start
```

Open http://localhost:3000

## 7. Process All Documents (Production)

```python
# process_batch.py
from pathlib import Path
import json
import subprocess

input_dir = Path("data/raw")
output_dir = Path("data/processed/extractions")
output_dir.mkdir(parents=True, exist_ok=True)

for pdf in sorted(input_dir.glob("*.pdf")):
    print(f"Processing {pdf.name}...")
    
    # Extract text (use pdfplumber or PyPDF2)
    # Run Claude extraction
    # Save to output_dir/{name}.json
    
    print(f"  → {output_dir / pdf.stem}.json")
```

## 8. Generate Benchmark Report

For invoices 001–010 (which have ground truth):

```python
# benchmark_full.py
import json
from pathlib import Path

ground_truth_dir = Path("data/ground_truth")
extracted_dir = Path("data/processed/extractions")

total_fields = 0
correct_fields = 0

for gt_file in ground_truth_dir.glob("*.json"):
    doc_id = gt_file.stem
    
    with open(gt_file) as f:
        ground_truth = json.load(f)
    
    with open(extracted_dir / f"{doc_id}.json") as f:
        extracted = json.load(f)
    
    # Count matching fields
    for key in ground_truth.keys():
        if key == "line_items":
            continue  # Handle separately
        total_fields += 1
        if extracted.get(key) == ground_truth.get(key):
            correct_fields += 1

accuracy = correct_fields / total_fields
print(f"Field Accuracy: {accuracy:.1%}")
print(f"Correct: {correct_fields}/{total_fields}")
```

## Next Steps

✅ Explored the dataset  
✅ Checked the schema  
✅ Installed dependencies  
✅ Extracted one invoice  
✅ Benchmarked against ground truth  

**Now:**
1. Extract all 25 invoices
2. Compare extractions 001–010 to ground truth
3. Review difficult documents (scanned, hard cases) manually
4. Deploy the web UI for team review
5. Iterate on extraction quality based on benchmark results

## Common Issues

**Q: PDF text extraction returns empty**  
A: Use `pdfplumber` for better PDF text handling:
```python
import pdfplumber
with pdfplumber.open("invoice.pdf") as pdf:
    text = pdf.pages[0].extract_text()
```

**Q: Claude returns incomplete JSON**  
A: Increase `max_tokens`, ensure the prompt specifies "return ONLY JSON"

**Q: Ground truth doesn't match production invoices**  
A: Ground truth (001–010) is for benchmarking. Invoices 011–025 are testing/edge cases.

---

For full documentation, see `README.md`
