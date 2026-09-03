import React, { useState, useEffect } from "react";
import { getMetrics, cleanupDatabase } from "../api";

function Dashboard() {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [cleaning, setCleaning] = useState(false);

  useEffect(() => {
    loadMetrics();
    const interval = setInterval(loadMetrics, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadMetrics = async () => {
    try {
      const data = await getMetrics();
      setMetrics(data);
      setError(null);
    } catch (err) {
      setError(`Error loading metrics: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleCleanup = async () => {
    if (
      window.confirm(
        "Are you sure? This will delete all documents and extractions."
      )
    ) {
      setCleaning(true);
      try {
        await cleanupDatabase();
        alert("Database cleaned successfully!");
        loadMetrics();
      } catch (err) {
        alert(`Cleanup error: ${err.message}`);
      } finally {
        setCleaning(false);
      }
    }
  };

  if (loading) return <div className="dashboard">Loading metrics...</div>;

  return (
    <div className="dashboard">
      <h2>Analytics and metrics</h2>

      {error && <div className="error-message">{error}</div>}

      {metrics && (
        <div className="metrics-grid">
          <div className="metric-card">
            <h3>Total Documents</h3>
            <p className="metric-value">{metrics.total_documents}</p>
            <p className="metric-label">uploaded</p>
          </div>

          <div className="metric-card">
            <h3>Extractions</h3>
            <p className="metric-value">{metrics.total_extractions}</p>
            <p className="metric-label">processed</p>
          </div>

          <div className="metric-card">
            <h3>Reviews</h3>
            <p className="metric-value">{metrics.total_reviews}</p>
            <p className="metric-label">submitted</p>
          </div>

          <div className="metric-card">
            <h3>Approval Rate</h3>
            <p className="metric-value">
              {(metrics.approval_rate * 100).toFixed(1)}%
            </p>
            <p className="metric-label">
              {metrics.approved_reviews} / {metrics.total_reviews} approved
            </p>
          </div>
        </div>
      )}

      <div className="dashboard-section">
        <h3>System status</h3>
        <div className="status-info">
          <p>
            <strong>Status:</strong>
            <span className="status-badge online">Online</span>
          </p>
          <p>
            <strong>API:</strong> http://127.0.0.1:8000
          </p>
          <p>
            <strong>LLM:</strong> Ollama (free, local)
          </p>
        </div>
      </div>

      <div className="dashboard-section">
        <h3>Administration</h3>
        <button
          onClick={handleCleanup}
          disabled={cleaning}
          className="btn btn-danger"
        >
          {cleaning ? "Cleaning" : "Reset database"}
        </button>
        <p className="admin-note">
          Deletes all documents, extractions, and reviews
        </p>
      </div>

      {metrics && metrics.total_documents > 0 && (
        <div className="dashboard-section">
          <h3>Statistics</h3>
          <ul>
            <li>
              Documents processed:{" "}
              <strong>{metrics.total_extractions}/{metrics.total_documents}</strong>
            </li>
            <li>
              Documents reviewed:{" "}
              <strong>{metrics.total_reviews}/{metrics.total_documents}</strong>
            </li>
            <li>
              Extraction success rate:{" "}
              <strong>
                {metrics.total_documents > 0
                  ? (
                      (metrics.total_extractions / metrics.total_documents) *
                      100
                    ).toFixed(1)
                  : 0}
                %
              </strong>
            </li>
          </ul>
        </div>
      )}
    </div>
  );
}

export default Dashboard;
