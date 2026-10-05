import { useState } from "react";
import {
  resolveComplaint,
  type ResolveResponse,
} from "./api";
import "./App.css";

function App() {
  const [complaint, setComplaint] = useState("");
  const [result, setResult] = useState<ResolveResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleResolve() {
    if (!complaint.trim()) {
      setError("Please enter a customer complaint.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await resolveComplaint(complaint);
      setResult(response);
    } catch (err) {
      console.error(err);
      setError(
        "Unable to resolve the complaint. Make sure the FastAPI server is running.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app">
      <header className="header">
        <div>
          <h1>Telecom Support Resolution Assistant</h1>
          <p>
            AI-assisted troubleshooting for customer support agents
          </p>
        </div>

        <div className="status">
          <span className="status-dot" />
          System Online
        </div>
      </header>

      <main className="container">
        <section className="card complaint-card">
          <h2>Customer Complaint</h2>

          <p className="section-description">
            Paste the customer's issue to generate a grounded resolution.
          </p>

          <textarea
            value={complaint}
            onChange={(event) => setComplaint(event.target.value)}
            placeholder="Example: My broadband drops every evening around 8 and I've already restarted the router twice..."
            rows={6}
          />

          <div className="action-row">
            <span className="character-count">
              {complaint.length} characters
            </span>

            <button
              onClick={handleResolve}
              disabled={loading}
            >
              {loading ? "Analyzing..." : "Resolve Complaint"}
            </button>
          </div>

          {error && <div className="error">{error}</div>}
        </section>

        {result && (
          <>
            <section className="card">
              <div className="section-heading">
                <h2>Complaint Intelligence</h2>

                <span className="model-badge">
                  {result.intelligence.model_version}
                </span>
              </div>

              <div className="intelligence-grid">
                <InfoItem
                  label="Intent"
                  value={result.intelligence.intent}
                />

                <InfoItem
                  label="Sub-intent"
                  value={result.intelligence.sub_intent}
                />

                <InfoItem
                  label="Product"
                  value={result.intelligence.product}
                />

                <InfoItem
                  label="Severity"
                  value={result.intelligence.severity}
                  className={result.intelligence.severity.toLowerCase()}
                />

                <InfoItem
                  label="Sentiment"
                  value={result.intelligence.sentiment}
                />

                <InfoItem
                  label="Confidence"
                  value={`${Math.round(
                    result.intelligence.confidence * 100,
                  )}%`}
                />
              </div>
            </section>

            <section className="card resolution-card">
              <div className="section-heading">
                <h2>AI Resolution</h2>

                <div className="confidence">
                  {Math.round(result.resolution.confidence * 100)}%
                  confidence
                </div>
              </div>

              <div className="resolution-section">
                <h3>Summary</h3>
                <p>{result.resolution.summary}</p>
              </div>

              <div className="resolution-section">
                <h3>Diagnosis</h3>
                <p>{result.resolution.diagnosis}</p>
              </div>

              <div className="resolution-section">
                <h3>Recommended Steps</h3>

                <ol className="steps">
                  {result.resolution.recommended_steps.map(
                    (step, index) => (
                      <li key={index}>
                        <span className="step-number">
                          {index + 1}
                        </span>

                        <span>{step}</span>
                      </li>
                    ),
                  )}
                </ol>
              </div>
            </section>

            <section className="bottom-grid">
              <div className="card">
                <h2>Grounding & Safety</h2>

                <div
                  className={
                    result.grounding.is_grounded
                      ? "grounded success"
                      : "grounded warning"
                  }
                >
                  <span>
                    {result.grounding.is_grounded ? "✓" : "!"}
                  </span>

                  <div>
                    <strong>
                      {result.grounding.is_grounded
                        ? "Resolution verified"
                        : "Verification required"}
                    </strong>

                    <p>
                      {result.grounding.is_grounded
                        ? "Recommended steps were checked against authoritative knowledge-base evidence."
                        : "Some generated steps could not be fully verified against the authoritative knowledge base."}
                    </p>
                  </div>
                </div>

                <div className="evidence-count">
                  Authoritative evidence:{" "}
                  <strong>
                    {result.grounding.authoritative_evidence_count}
                  </strong>
                </div>

                {result.grounding.unsupported_steps.length > 0 && (
                  <div className="unsupported">
                    <strong>Unsupported steps:</strong>

                    <ul>
                      {result.grounding.unsupported_steps.map(
                        (step, index) => (
                          <li key={index}>{step}</li>
                        ),
                      )}
                    </ul>
                  </div>
                )}
              </div>

              <div className="card">
                <h2>Knowledge Sources</h2>

                {result.resolution.citations.length > 0 ? (
                  <div className="citations">
                    {result.resolution.citations.map(
                      (citation, index) => (
                        <div
                          className="citation"
                          key={index}
                        >
                          <strong>
                            {citation.source_id}
                          </strong>

                          {citation.section && (
                            <span>{citation.section}</span>
                          )}
                        </div>
                      ),
                    )}
                  </div>
                ) : (
                  <p className="muted">
                    No citations returned.
                  </p>
                )}
              </div>
            </section>
          </>
        )}
      </main>
    </div>
  );
}

interface InfoItemProps {
  label: string;
  value: string;
  className?: string;
}

function InfoItem({
  label,
  value,
  className = "",
}: InfoItemProps) {
  return (
    <div className="info-item">
      <span>{label}</span>
      <strong className={className}>{value}</strong>
    </div>
  );
}

export default App;