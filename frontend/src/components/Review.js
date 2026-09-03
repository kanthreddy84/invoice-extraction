import React, { useState, useEffect } from "react";
import { getExtraction, submitReview, listDocuments } from "../api";

function Review({ onReviewComplete }) {
  const [documents, setDocuments] = useState([]);
  const [selectedDocId, setSelectedDocId] = useState(null);
  const [extraction, setExtraction] = useState(null);
  const [editedData, setEditedData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [reviewing, setReviewing] = useState(false);
  const [successMessage, setSuccessMessage] = useState(null);

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    try {
      setLoading(true);
      const docs = await listDocuments();
      setDocuments(docs.documents || []);
    } catch (err) {
      setError(`Error loading documents: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectDocument = async (docId) => {
    setSelectedDocId(docId);
    setError(null);

    try {
      setLoading(true);
      const data = await getExtraction(docId);
      setExtraction(data.extracted_json);
      setEditedData(JSON.parse(JSON.stringify(data.extracted_json)));
    } catch (err) {
      setError(`Error loading extraction: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleFieldChange = (field, value) => {
    setEditedData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleSubmitReview = async (approved) => {
    if (!selectedDocId) return;

    setReviewing(true);
    setError(null);

    try {
      // Get extraction ID (in real app, would come from API)
      const extractionId = selectedDocId;

      await submitReview(extractionId, {
        extraction_id: extractionId,
        reviewer_name: "Human Reviewer",
        approved,
        comments: `Data has been ${approved ? "approved" : "rejected"} for processing`,
      });

      setSuccessMessage(
        `Review submitted: ${approved ? "Approved" : "Rejected"}`
      );
      setTimeout(() => {
        setSuccessMessage(null);
        loadDocuments();
        onReviewComplete();
      }, 2000);
    } catch (err) {
      setError(`Review error: ${err.message}`);
    } finally {
      setReviewing(false);
    }
  };

  return (
    <div className="review-container">
      <h2>Review extractions</h2>

      {error && <div className="error-message">{error}</div>}
      {successMessage && (
        <div className="success-message">{successMessage}</div>
      )}

      <div className="review-layout">
        <div className="documents-list">
          <h3>Documents</h3>
          {loading && <p>Loading documents...</p>}
          {documents.length === 0 ? (
            <p className="empty-state">No documents uploaded yet</p>
          ) : (
            <ul>
              {documents.map((doc) => (
                <li
                  key={doc.id}
                  className={`doc-item ${
                    selectedDocId === doc.id ? "active" : ""
                  }`}
                  onClick={() => handleSelectDocument(doc.id)}
                >
                  <span className="doc-name">{doc.filename}</span>
                  <span className="doc-status">{doc.status}</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        {extraction && editedData && (
          <div className="extraction-view">
            <h3>Extracted Data</h3>
            <div className="extraction-fields">
              <div className="field-group">
                <label>Invoice Number</label>
                <input
                  type="text"
                  value={editedData.invoice_number || ""}
                  onChange={(e) =>
                    handleFieldChange("invoice_number", e.target.value)
                  }
                />
              </div>

              <div className="field-group">
                <label>Invoice Date</label>
                <input
                  type="date"
                  value={editedData.invoice_date || ""}
                  onChange={(e) =>
                    handleFieldChange("invoice_date", e.target.value)
                  }
                />
              </div>

              <div className="field-group">
                <label>Due Date</label>
                <input
                  type="date"
                  value={editedData.due_date || ""}
                  onChange={(e) =>
                    handleFieldChange("due_date", e.target.value)
                  }
                />
              </div>

              <div className="field-group">
                <label>Vendor Name</label>
                <input
                  type="text"
                  value={editedData.vendor_name || ""}
                  onChange={(e) =>
                    handleFieldChange("vendor_name", e.target.value)
                  }
                />
              </div>

              <div className="field-group">
                <label>Vendor Address</label>
                <input
                  type="text"
                  value={editedData.vendor_address || ""}
                  onChange={(e) =>
                    handleFieldChange("vendor_address", e.target.value)
                  }
                />
              </div>

              <div className="field-group">
                <label>Customer Name</label>
                <input
                  type="text"
                  value={editedData.customer_name || ""}
                  onChange={(e) =>
                    handleFieldChange("customer_name", e.target.value)
                  }
                />
              </div>

              <div className="field-group">
                <label>Customer Address</label>
                <input
                  type="text"
                  value={editedData.customer_address || ""}
                  onChange={(e) =>
                    handleFieldChange("customer_address", e.target.value)
                  }
                />
              </div>

              <div className="field-group">
                <label>Currency</label>
                <input
                  type="text"
                  value={editedData.currency || ""}
                  onChange={(e) =>
                    handleFieldChange("currency", e.target.value)
                  }
                />
              </div>

              <div className="field-group">
                <label>Subtotal</label>
                <input
                  type="number"
                  step="0.01"
                  value={editedData.subtotal || ""}
                  onChange={(e) =>
                    handleFieldChange("subtotal", parseFloat(e.target.value))
                  }
                />
              </div>

              <div className="field-group">
                <label>Tax</label>
                <input
                  type="number"
                  step="0.01"
                  value={editedData.tax || ""}
                  onChange={(e) =>
                    handleFieldChange("tax", parseFloat(e.target.value))
                  }
                />
              </div>

              <div className="field-group">
                <label>Discount</label>
                <input
                  type="number"
                  step="0.01"
                  value={editedData.discount || ""}
                  onChange={(e) =>
                    handleFieldChange("discount", parseFloat(e.target.value))
                  }
                />
              </div>

              <div className="field-group">
                <label>Total</label>
                <input
                  type="number"
                  step="0.01"
                  value={editedData.total || ""}
                  onChange={(e) =>
                    handleFieldChange("total", parseFloat(e.target.value))
                  }
                />
              </div>
            </div>

            <div className="review-actions">
              <button
                onClick={() => handleSubmitReview(true)}
                disabled={reviewing}
                className="btn btn-approve"
              >
                Approve
              </button>
              <button
                onClick={() => handleSubmitReview(false)}
                disabled={reviewing}
                className="btn btn-reject"
              >
                Reject
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default Review;
