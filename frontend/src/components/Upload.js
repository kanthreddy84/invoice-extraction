import React, { useState, useEffect } from "react";
import { uploadDocument, processDocumentAsync, getTaskStatus, saveExtraction } from "../api";

function Upload({ onUploadSuccess, onProcessStart, documentId, taskId }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [taskStatus, setTaskStatus] = useState(null);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  useEffect(() => {
    if (!taskId) return;

    setProcessing(true);
    const pollInterval = setInterval(async () => {
      try {
        const status = await getTaskStatus(taskId);
        setTaskStatus(status);

        if (status.status === "SUCCESS") {
          // Auto-save extraction to database
          try {
            await saveExtraction(taskId, documentId);
            setSuccessMessage("Extraction completed and saved");
          } catch (err) {
            console.error("Save error:", err);
            setSuccessMessage("Extraction completed (ready to review)");
          }
          setProcessing(false);
          clearInterval(pollInterval);
        } else if (status.status === "FAILURE") {
          setError(`Task failed: ${status.error}`);
          setProcessing(false);
          clearInterval(pollInterval);
        }
      } catch (err) {
        console.error("Poll error:", err);
      }
    }, 2000);

    return () => clearInterval(pollInterval);
  }, [taskId]);

  const handleFileSelect = (e) => {
    setSelectedFile(e.target.files[0]);
    setError(null);
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError("Please select a file");
      return;
    }

    setUploading(true);
    setError(null);

    try {
      const result = await uploadDocument(selectedFile);
      setSuccessMessage(`Document uploaded: ${result.filename}`);
      setSelectedFile(null);
      onUploadSuccess(result);
    } catch (err) {
      setError(`Upload error: ${err.message}`);
    } finally {
      setUploading(false);
    }
  };

  const handleProcess = async () => {
    if (!documentId) {
      setError("No document selected");
      return;
    }

    try {
      const result = await processDocumentAsync(documentId);
      onProcessStart(result);
      setSuccessMessage("Processing started...");
    } catch (err) {
      setError(`Processing error: ${err.message}`);
    }
  };

  return (
    <div className="upload-container">
      <h2>Upload and process invoice</h2>

      {error && <div className="error-message">{error}</div>}
      {successMessage && (
        <div className="success-message">{successMessage}</div>
      )}

      <div className="upload-section">
        <div className="file-input-wrapper">
          <input
            type="file"
            accept=".pdf"
            onChange={handleFileSelect}
            disabled={uploading}
            id="file-input"
          />
          <label htmlFor="file-input" className="file-label">
            {selectedFile ? selectedFile.name : "Click to select PDF"}
          </label>
        </div>

        <button
          onClick={handleUpload}
          disabled={uploading || !selectedFile}
          className="btn btn-primary"
        >
          {uploading ? "Uploading" : "Upload document"}
        </button>
      </div>

      {documentId && (
        <div className="processing-section">
          <p>Document ID: <strong>{documentId}</strong></p>
          <button
            onClick={handleProcess}
            disabled={processing}
            className="btn btn-success"
          >
            {processing ? "Processing" : "Start extraction"}
          </button>
        </div>
      )}

      {taskId && (
        <div className="status-section">
          <h3>Processing status</h3>
          <div className="status-box">
            <p>Task ID: <code>{taskId}</code></p>
            <p>Status: <strong>{taskStatus?.status || "PENDING"}</strong></p>
            {taskStatus?.status === "STARTED" && (
              <div className="spinner">Processing</div>
            )}
            {taskStatus?.status === "SUCCESS" && (
              <div className="success-box">
                <p>Extraction completed successfully</p>
                <p>Confidence: {(taskStatus?.result?.confidence * 100).toFixed(1)}%</p>
              </div>
            )}
            {taskStatus?.status === "FAILURE" && (
              <div className="error-box">
                <p>Error: {taskStatus?.error}</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default Upload;
