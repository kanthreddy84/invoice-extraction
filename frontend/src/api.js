// API integration with FastAPI backend

const API_URL = "https://invoice-extraction-api-tn0f.onrender.com";

export const uploadDocument = async (file) => {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_URL}/api/documents/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) throw new Error("Upload failed");
  return response.json();
};

export const processDocumentAsync = async (documentId) => {
  const response = await fetch(
    `${API_URL}/api/documents/${documentId}/process-async`,
    { method: "POST" }
  );

  if (!response.ok) throw new Error("Processing failed");
  return response.json();
};

export const getTaskStatus = async (taskId) => {
  const response = await fetch(`${API_URL}/api/tasks/${taskId}/status`);
  if (!response.ok) throw new Error("Status check failed");
  return response.json();
};

export const getExtraction = async (documentId) => {
  const response = await fetch(
    `${API_URL}/api/documents/${documentId}/extraction`
  );
  if (!response.ok) throw new Error("Extraction not found");
  return response.json();
};

export const submitReview = async (extractionId, reviewData) => {
  const response = await fetch(
    `${API_URL}/api/extractions/${extractionId}/review`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(reviewData),
    }
  );

  if (!response.ok) throw new Error("Review submission failed");
  return response.json();
};

export const getMetrics = async () => {
  const response = await fetch(`${API_URL}/api/metrics`);
  if (!response.ok) throw new Error("Metrics fetch failed");
  return response.json();
};

export const listDocuments = async () => {
  const response = await fetch(`${API_URL}/api/documents`);
  if (!response.ok) throw new Error("List documents failed");
  return response.json();
};

export const cleanupDatabase = async () => {
  const response = await fetch(`${API_URL}/admin/cleanup`, {
    method: "POST",
  });
  if (!response.ok) throw new Error("Cleanup failed");
  return response.json();
};

export const saveExtraction = async (taskId, documentId) => {
  const response = await fetch(
    `${API_URL}/api/tasks/${taskId}/save-extraction/${documentId}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    }
  );
  if (!response.ok) throw new Error("Save extraction failed");
  return response.json();
};
