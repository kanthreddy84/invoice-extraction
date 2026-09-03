from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pathlib import Path
import json
import shutil
from datetime import datetime

from database import Base, engine, get_db, Document, Extraction, Review
from schemas import DocumentResponse, ExtractionResponse, ReviewRequest, InvoiceExtraction

# Create tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Invoice Extraction API",
    description="API for extracting invoice data with human-in-the-loop validation",
    version="1.0.0"
)

# Add CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create upload directory
UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# ============================================
# Health Check Endpoint
# ============================================
@app.get("/health")
async def health_check():
    """Check if API is running"""
    return {
        "status": "healthy",
        "service": "Invoice Extraction API",
        "version": "1.0.0"
    }

@app.post("/admin/cleanup")
async def cleanup_database(db: Session = Depends(get_db)):
    """Clean up all documents, extractions, and reviews"""
    try:
        # Delete all data
        db.query(Review).delete()
        db.query(Extraction).delete()
        db.query(Document).delete()
        db.commit()

        # Clear uploads folder
        import shutil
        uploads_dir = Path("data/uploads")
        if uploads_dir.exists():
            shutil.rmtree(uploads_dir)
        uploads_dir.mkdir(exist_ok=True)

        return {
            "message": "Database cleaned successfully",
            "status": "reset"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

# ============================================
# Document Upload Endpoints
# ============================================
@app.post("/api/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload an invoice PDF for processing"""
    try:
        # Save file
        file_path = UPLOAD_DIR / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Create document record
        doc = Document(
            filename=file.filename,
            file_path=str(file_path),
            status="uploaded"
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        return {
            "message": "File uploaded successfully",
            "document_id": doc.id,
            "filename": doc.filename,
            "status": doc.status
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============================================
# Document List Endpoint
# ============================================
@app.get("/api/documents")
async def list_documents(db: Session = Depends(get_db)):
    """List all uploaded documents"""
    documents = db.query(Document).all()
    return {
        "total": len(documents),
        "documents": documents
    }

# ============================================
# Extraction Endpoints
# ============================================
@app.get("/api/documents/{document_id}/extraction")
async def get_extraction(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Get extraction results for a document"""
    extraction = db.query(Extraction).filter(
        Extraction.document_id == document_id
    ).first()

    if not extraction:
        raise HTTPException(status_code=404, detail="Extraction not found")

    return extraction

@app.post("/api/documents/{document_id}/extract")
async def create_extraction(
    document_id: int,
    extraction_data: InvoiceExtraction,
    db: Session = Depends(get_db)
):
    """Save extraction results for a document"""
    try:
        extraction = Extraction(
            document_id=document_id,
            extracted_json=extraction_data.dict(),
            confidence=extraction_data.confidence or 0.0
        )
        db.add(extraction)

        # Update document status
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            doc.status = "extracted"
            doc.processed_at = datetime.utcnow()

        db.commit()
        db.refresh(extraction)

        return {
            "message": "Extraction saved successfully",
            "extraction_id": extraction.id,
            "document_id": document_id
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

# ============================================
# Review Endpoints
# ============================================
@app.post("/api/extractions/{extraction_id}/review")
async def review_extraction(
    extraction_id: int,
    review: ReviewRequest,
    db: Session = Depends(get_db)
):
    """Submit review for an extraction"""
    try:
        review_record = Review(
            extraction_id=extraction_id,
            reviewer_name=review.reviewer_name,
            approved=review.approved,
            comments=review.comments
        )
        db.add(review_record)

        # Update extraction
        extraction = db.query(Extraction).filter(
            Extraction.id == extraction_id
        ).first()
        if extraction:
            extraction.confidence = 1.0 if review.approved else 0.0

        db.commit()

        return {
            "message": "Review submitted successfully",
            "review_id": review_record.id,
            "approved": review.approved
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/extractions/{extraction_id}/reviews")
async def get_reviews(
    extraction_id: int,
    db: Session = Depends(get_db)
):
    """Get all reviews for an extraction"""
    reviews = db.query(Review).filter(
        Review.extraction_id == extraction_id
    ).all()
    return {"reviews": reviews}

# ============================================
# Metrics Endpoints
# ============================================
@app.get("/api/metrics")
async def get_metrics(db: Session = Depends(get_db)):
    """Get system metrics"""
    total_docs = db.query(Document).count()
    total_extractions = db.query(Extraction).count()
    total_reviews = db.query(Review).count()
    approved_reviews = db.query(Review).filter(Review.approved == True).count()

    return {
        "total_documents": total_docs,
        "total_extractions": total_extractions,
        "total_reviews": total_reviews,
        "approved_reviews": approved_reviews,
        "approval_rate": approved_reviews / total_reviews if total_reviews > 0 else 0
    }

# ============================================
# Async Task Endpoints
# ============================================
@app.post("/api/documents/{document_id}/process-async")
async def process_document_async(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Queue document for async processing"""
    from task_queue import queue_task

    try:
        # Get document
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        # Queue task
        task_id = queue_task("process_invoice", {"pdf_path": doc.file_path})

        return {
            "message": "Document queued for processing",
            "document_id": document_id,
            "task_id": task_id,
            "status": "queued"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/tasks/{task_id}/status")
async def get_task_status(task_id: str):
    """Get async task status"""
    from task_queue import get_task_status as get_status

    try:
        task_info = get_status(task_id)

        if not task_info:
            raise HTTPException(status_code=404, detail="Task not found")

        return task_info
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/tasks/{task_id}/save-extraction/{document_id}")
async def save_extraction_from_task(
    task_id: str,
    document_id: int,
    db: Session = Depends(get_db)
):
    """Save extraction results from completed task to database"""
    from task_queue import get_task_status as get_status

    try:
        # Get task result
        task_info = get_status(task_id)
        if not task_info:
            raise HTTPException(status_code=404, detail="Task not found")

        if task_info['status'] != "SUCCESS":
            raise HTTPException(status_code=400, detail=f"Task not completed: {task_info['status']}")

        result = task_info.get('result', {})

        # Create extraction record
        extraction = Extraction(
            document_id=document_id,
            extracted_json=result.get('data', {}),
            confidence=result.get('confidence', 0.0)
        )
        db.add(extraction)

        # Update document status
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            doc.status = "extracted"
            doc.processed_at = datetime.utcnow()

        db.commit()
        db.refresh(extraction)

        return {
            "message": "Extraction saved successfully",
            "extraction_id": extraction.id,
            "document_id": document_id,
            "confidence": result.get('confidence', 0.0)
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/tasks/queue-status")
async def get_queue_status():
    """Get message queue status"""
    from task_queue import task_store, task_queue

    try:
        active_tasks = sum(1 for t in task_store.values() if t.status == "STARTED")
        pending_tasks = task_queue.qsize()

        return {
            "queue_name": "task_queue",
            "active_tasks": active_tasks,
            "pending_tasks": pending_tasks,
            "total_tasks": len(task_store),
            "broker": "Threading (In-Process)"
        }
    except Exception as e:
        return {
            "status": "ok",
            "message": "Task queue ready",
            "broker": "Threading (In-Process)"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
