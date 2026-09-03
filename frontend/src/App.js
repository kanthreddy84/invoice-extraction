import React, { useState } from "react";
import "./App.css";
import Logo from "./components/Logo";
import Upload from "./components/Upload";
import Review from "./components/Review";
import Dashboard from "./components/Dashboard";

function App() {
  const [activeTab, setActiveTab] = useState("upload");
  const [documentId, setDocumentId] = useState(null);
  const [taskId, setTaskId] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const handleUploadSuccess = (doc) => {
    setDocumentId(doc.document_id);
    setTaskId(null);
    setRefreshKey(refreshKey + 1);
  };

  const handleProcessStart = (task) => {
    setTaskId(task.task_id);
    setRefreshKey(refreshKey + 1);
  };

  const handleReviewComplete = () => {
    setRefreshKey(refreshKey + 1);
  };

  return (
    <div className="app">
      <header className="header">
        <div className="container">
          <div className="header-brand">DataFactZ</div>
          <div className="header-content">
            <Logo />
            <div>
              <h1>Invoice extraction</h1>
              <p>AI-powered document processing with human review</p>
            </div>
          </div>
        </div>
      </header>

      <nav className="tabs">
        <div className="container">
          <button
            className={`tab ${activeTab === "upload" ? "active" : ""}`}
            onClick={() => setActiveTab("upload")}
          >
            Upload
          </button>
          <button
            className={`tab ${activeTab === "review" ? "active" : ""}`}
            onClick={() => setActiveTab("review")}
          >
            Review
          </button>
          <button
            className={`tab ${activeTab === "dashboard" ? "active" : ""}`}
            onClick={() => setActiveTab("dashboard")}
          >
            Dashboard
          </button>
        </div>
      </nav>

      <main className="container content">
        {activeTab === "upload" && (
          <Upload
            onUploadSuccess={handleUploadSuccess}
            onProcessStart={handleProcessStart}
            documentId={documentId}
            taskId={taskId}
            key={refreshKey}
          />
        )}
        {activeTab === "review" && (
          <Review
            documentId={documentId}
            onReviewComplete={handleReviewComplete}
            key={refreshKey}
          />
        )}
        {activeTab === "dashboard" && (
          <Dashboard key={refreshKey} />
        )}
      </main>

      <footer className="footer">
        <p>DataFactZ Invoice Extraction | Built with FastAPI and Ollama</p>
      </footer>
    </div>
  );
}

export default App;
