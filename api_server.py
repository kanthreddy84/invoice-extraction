from flask import Flask, request, jsonify
from flask_cors import CORS
from pathlib import Path
import json
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)
CORS(app)

# Database setup
DB_PATH = "invoices.db"
UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def init_db():
    """Initialize database schema"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        file_path TEXT NOT NULL,
        status TEXT DEFAULT 'uploaded',
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        processed_at TIMESTAMP
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS extractions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER NOT NULL,
        extracted_json TEXT,
        confidence REAL DEFAULT 0.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(document_id) REFERENCES documents(id)
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        extraction_id INTEGER NOT NULL,
        reviewer_name TEXT,
        approved BOOLEAN,
        comments TEXT,
        reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(extraction_id) REFERENCES extractions(id)
    )''')

    conn.commit()
    conn.close()

init_db()

# ============================================
# Health Check Endpoint
# ============================================
@app.route("/health", methods=["GET"])
def health_check():
    """Check if API is running"""
    return jsonify({
        "status": "healthy",
        "service": "Invoice Extraction API",
        "version": "1.0.0"
    })

# ============================================
# Document Upload Endpoints
# ============================================
@app.route("/api/documents/upload", methods=["POST"])
def upload_document():
    """Upload an invoice PDF for processing"""
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        # Save file
        file_path = UPLOAD_DIR / file.filename
        file.save(str(file_path))

        # Create document record
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO documents (filename, file_path, status) VALUES (?, ?, ?)",
            (file.filename, str(file_path), "uploaded")
        )
        conn.commit()
        doc_id = cursor.lastrowid
        conn.close()

        return jsonify({
            "message": "File uploaded successfully",
            "document_id": doc_id,
            "filename": file.filename,
            "status": "uploaded"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# ============================================
# Document List Endpoint
# ============================================
@app.route("/api/documents", methods=["GET"])
def list_documents():
    """List all uploaded documents"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, filename, status FROM documents ORDER BY uploaded_at DESC")
        documents = []
        for row in cursor.fetchall():
            documents.append({
                "id": row[0],
                "filename": row[1],
                "status": row[2]
            })
        conn.close()

        return jsonify({
            "total": len(documents),
            "documents": documents
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# ============================================
# Extraction Endpoints
# ============================================
@app.route("/api/documents/<int:document_id>/extraction", methods=["GET"])
def get_extraction(document_id):
    """Get extraction results for a document"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, document_id, extracted_json, confidence FROM extractions WHERE document_id = ?",
            (document_id,)
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            return jsonify({"error": "Extraction not found"}), 404

        return jsonify({
            "id": row[0],
            "document_id": row[1],
            "extracted_json": json.loads(row[2]) if row[2] else {},
            "confidence": row[3]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# ============================================
# Async Task Endpoints
# ============================================
@app.route("/api/documents/<int:document_id>/process-async", methods=["POST"])
def process_document_async(document_id):
    """Queue document for async processing"""
    try:
        # For now, return mock extraction immediately
        mock_extraction = {
            "invoice_number": "INV-2024-001",
            "invoice_date": "2024-09-01",
            "due_date": "2024-10-01",
            "vendor_name": "Acme Corp",
            "vendor_address": "123 Main St",
            "customer_name": "Your Company",
            "customer_address": "456 Oak Ave",
            "currency": "USD",
            "subtotal": 1000.00,
            "discount": 100.00,
            "tax": 108.00,
            "total": 1008.00,
            "line_items": []
        }

        task_id = f"task_{document_id}_{int(datetime.utcnow().timestamp())}"

        # Save extraction
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO extractions (document_id, extracted_json, confidence) VALUES (?, ?, ?)",
            (document_id, json.dumps(mock_extraction), 0.95)
        )
        conn.commit()
        conn.close()

        return jsonify({
            "message": "Document queued for processing",
            "document_id": document_id,
            "task_id": task_id,
            "status": "queued"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/tasks/<task_id>/status", methods=["GET"])
def get_task_status(task_id):
    """Get async task status"""
    return jsonify({
        "task_id": task_id,
        "status": "SUCCESS",
        "result": {
            "data": {
                "invoice_number": "INV-2024-001",
                "invoice_date": "2024-09-01",
                "due_date": "2024-10-01",
                "vendor_name": "Acme Corp",
                "vendor_address": "123 Main St",
                "customer_name": "Your Company",
                "customer_address": "456 Oak Ave",
                "currency": "USD",
                "subtotal": 1000.00,
                "discount": 100.00,
                "tax": 108.00,
                "total": 1008.00,
                "line_items": []
            },
            "confidence": 0.95
        }
    })

@app.route("/api/tasks/<task_id>/save-extraction/<int:document_id>", methods=["POST"])
def save_extraction_from_task(task_id, document_id):
    """Save extraction results from completed task to database"""
    try:
        mock_extraction = {
            "invoice_number": "INV-2024-001",
            "invoice_date": "2024-09-01",
            "due_date": "2024-10-01",
            "vendor_name": "Acme Corp",
            "vendor_address": "123 Main St",
            "customer_name": "Your Company",
            "customer_address": "456 Oak Ave",
            "currency": "USD",
            "subtotal": 1000.00,
            "discount": 100.00,
            "tax": 108.00,
            "total": 1008.00,
            "line_items": []
        }

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO extractions (document_id, extracted_json, confidence) VALUES (?, ?, ?)",
            (document_id, json.dumps(mock_extraction), 0.95)
        )
        extraction_id = cursor.lastrowid
        cursor.execute(
            "UPDATE documents SET status = ?, processed_at = ? WHERE id = ?",
            ("extracted", datetime.utcnow().isoformat(), document_id)
        )
        conn.commit()
        conn.close()

        return jsonify({
            "message": "Extraction saved successfully",
            "extraction_id": extraction_id,
            "document_id": document_id,
            "confidence": 0.95
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# ============================================
# Review Endpoints
# ============================================
@app.route("/api/extractions/<int:extraction_id>/review", methods=["POST"])
def review_extraction(extraction_id):
    """Submit review for an extraction"""
    try:
        data = request.get_json()

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO reviews (extraction_id, reviewer_name, approved, comments) VALUES (?, ?, ?, ?)",
            (extraction_id, data.get("reviewer_name"), data.get("approved"), data.get("comments"))
        )
        conn.commit()
        review_id = cursor.lastrowid
        conn.close()

        return jsonify({
            "message": "Review submitted successfully",
            "review_id": review_id,
            "approved": data.get("approved")
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# ============================================
# Metrics Endpoints
# ============================================
@app.route("/api/metrics", methods=["GET"])
def get_metrics():
    """Get system metrics"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM documents")
        total_docs = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM extractions")
        total_extractions = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM reviews")
        total_reviews = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM reviews WHERE approved = 1")
        approved_reviews = cursor.fetchone()[0]

        conn.close()

        approval_rate = approved_reviews / total_reviews if total_reviews > 0 else 0

        return jsonify({
            "total_documents": total_docs,
            "total_extractions": total_extractions,
            "total_reviews": total_reviews,
            "approved_reviews": approved_reviews,
            "approval_rate": approval_rate
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# ============================================
# Admin Endpoints
# ============================================
@app.route("/admin/cleanup", methods=["POST"])
def cleanup_database():
    """Clean up all documents, extractions, and reviews"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM reviews")
        cursor.execute("DELETE FROM extractions")
        cursor.execute("DELETE FROM documents")
        conn.commit()
        conn.close()

        # Clear uploads folder
        import shutil
        if UPLOAD_DIR.exists():
            shutil.rmtree(UPLOAD_DIR)
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        return jsonify({
            "message": "Database cleaned successfully",
            "status": "reset"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False)
