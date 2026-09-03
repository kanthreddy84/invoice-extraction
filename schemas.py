from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# Invoice Line Item
class LineItem(BaseModel):
    description: str
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    amount: float

# Invoice Extraction
class InvoiceExtraction(BaseModel):
    invoice_number: str
    invoice_date: str
    due_date: Optional[str] = None
    vendor_name: str
    vendor_address: Optional[str] = None
    customer_name: str
    customer_address: Optional[str] = None
    currency: str
    subtotal: float
    discount: Optional[float] = None
    tax: Optional[float] = None
    total: float
    line_items: List[LineItem]
    confidence: Optional[float] = None

# Document Response
class DocumentResponse(BaseModel):
    id: int
    filename: str
    status: str
    uploaded_at: datetime

    class Config:
        from_attributes = True

# Extraction Response
class ExtractionResponse(BaseModel):
    id: int
    document_id: int
    extracted_json: dict
    confidence: float
    created_at: datetime

    class Config:
        from_attributes = True

# Review Request
class ReviewRequest(BaseModel):
    extraction_id: int
    reviewer_name: str
    approved: bool
    comments: Optional[str] = None

# User models
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class User(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool

    class Config:
        from_attributes = True
