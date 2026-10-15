
import { useState } from "react";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  CircleHelp,
  FileText,
  Loader2,
  Search,
  Server,
  ShieldAlert,
  Terminal,
} from "lucide-react";
import "./App.css";

type IncidentReport = {
  service_name: string;
  environment: string;
  severity: "low" | "medium" | "high" | "critical";
  summary: string;
  likely_causes: string[];
  recommendations: string[];
  evidence: string[];
  matched_patterns: string[];
};

function App() {
  const [logs, setLogs] = useState(
    "2026-10-15 10:22:01 ERROR payment-api Database connection failed: connection timeout"
  );
  const [service, setService] = useState("payment-api");
  const [environment, setEnvironment] = useState("local");
  const [report, setReport] = useState<IncidentReport | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function analyzeLogs() {
    setLoading(true);
    setError("");
    setReport(null);

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/api/v1/analyze",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            log_text: logs,
            service_name: service,
            environment,
          }),
        }
      );

      if (!response.ok) {
        throw new Error(`API request failed (${response.status})`);
      }

      setReport(await response.json());
    } catch {
      setError(
        "Could not connect to the API. Check that FastAPI is running on port 8000."
      );
    } finally {
      setLoading(false);
    }
  }

  const severity = report?.severity ?? "none";

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon"><Activity size={23} /></div>
          <div>
            <h2>OpsPilot</h2>
            <span>AI DEVOPS COPILOT</span>
          </div>
        </div>

        <div className="nav-label">WORKSPACE</div>
        <div className="nav-item active">
          <Activity size={18} /> Incident Analyzer
        </div>
        <div className="nav-item">
          <Server size={18} /> Services
          <span className="coming-soon">SOON</span>
        </div>
        <div className="nav-item">
          <FileText size={18} /> Incident History
          <span className="coming-soon">SOON</span>
        </div>

        <div className="sidebar-bottom">
          <div className="status-dot" />
          <span>Local API</span>
          <span className="online">READY</span>
        </div>
      </aside>

      <section className="main-content">
        <header className="topbar">
          <div className="breadcrumb">Workspace / <b>Incident Analyzer</b></div>
          <div className="environment-badge">
            <span className="status-dot" /> LOCAL ENVIRONMENT
          </div>
        </header>

        <div className="page-content">
          <div className="page-heading">
            <div>
              <div className="eyebrow">OPERATIONS CENTER</div>
              <h1>Incident Analyzer</h1>
              <p>Investigate application errors and identify possible root causes.</p>
            </div>
            <div className="version-tag">v0.1.0</div>
          </div>

          <div className="stats-grid">
            <article className="stat-card">
              <span>ANALYSIS ENGINE</span>
              <div className="stat-value"><Activity /> Rule-based</div>
              <small>Local processing</small>
            </article>
            <article className="stat-card">
              <span>SELECTED SERVICE</span>
              <div className="stat-value"><Server /> {service || "Not set"}</div>
              <small>Application under investigation</small>
            </article>
            <article className="stat-card">
              <span>LAST ANALYSIS</span>
              <div className="stat-value">
                {report ? <CheckCircle2 /> : <CircleHelp />}
                {report ? "Completed" : "Not run"}
              </div>
              <small>Current session</small>
            </article>
          </div>

          <div className="workspace-grid">
            <section className="panel log-panel">
              <div className="panel-heading">
                <div className="heading-icon"><Terminal size={18} /></div>
                <div>
                  <h3>Log Input</h3>
                  <p>Provide the logs you want to investigate.</p>
                </div>
              </div>

              <label htmlFor="service">Service name</label>
              <input
                id="service"
                value={service}
                onChange={(event) => setService(event.target.value)}
                placeholder="payment-api"
              />

              <label htmlFor="environment">Environment</label>
              <select
                id="environment"
                value={environment}
                onChange={(event) => setEnvironment(event.target.value)}
              >
                <option value="local">Local</option>
                <option value="development">Development</option>
                <option value="staging">Staging</option>
                <option value="production">Production</option>
              </select>

              <div className="editor-heading">
                <label htmlFor="logs">Application logs</label>
                <span>Plain text</span>
              </div>
              <textarea
                id="logs"
                value={logs}
                onChange={(event) => setLogs(event.target.value)}
                placeholder="Paste application logs here..."
                spellCheck={false}
              />

              <button
                className="analyze-button"
                onClick={analyzeLogs}
                disabled={loading || !logs.trim() || !service.trim()}
              >
                {loading ? <Loader2 className="spin" /> : <Search size={18} />}
                {loading ? "Analyzing logs..." : "Analyze incident"}
              </button>

              <p className="privacy-note">
                <ShieldAlert size={15} />
                Logs are sent to your local API.
              </p>
            </section>

            <section className="panel results-panel">
              <div className="panel-heading">
                <div className="heading-icon purple"><Activity size={18} /></div>
                <div>
                  <h3>Analysis Results</h3>
                  <p>Findings from your log analysis.</p>
                </div>
              </div>

              {error && <div className="error-message">{error}</div>}

              {!report && !error && (
                <div className="empty-state">
                  <div className="empty-icon"><Search size={27} /></div>
                  <h3>Ready to investigate</h3>
                  <p>Submit your logs to discover error patterns, severity, and recommended troubleshooting steps.</p>
                  <div className="empty-tip">
                    <AlertTriangle size={16} />
                    Try the preloaded database connection error.
                  </div>
                </div>
              )}

              {report && (
                <div className="report">
                  <div className="severity-row">
                    <div>
                      <span className="result-label">DETECTED SEVERITY</span>
                      <div className={`severity ${severity}`}>
                        <span /> {severity.toUpperCase()}
                      </div>
                    </div>
                    <span className="pattern-count">
                      {report.matched_patterns.length} pattern(s)
                    </span>
                  </div>

                  <h4>Incident summary</h4>
                  <p className="summary">{report.summary}</p>

                  <h4>Likely causes</h4>
                  <ul>
                    {report.likely_causes.map((item, index) => (
                      <li key={index}>{item}</li>
                    ))}
                  </ul>

                  <h4>Recommended actions</h4>
                  <ol>
                    {report.recommendations.map((item, index) => (
                      <li key={index}>{item}</li>
                    ))}
                  </ol>

                  <h4>Evidence</h4>
                  {report.evidence.length ? (
                    report.evidence.map((line, index) => (
                      <pre className="evidence" key={index}>{line}</pre>
                    ))
                  ) : (
                    <p className="muted">No matching log lines found.</p>
                  )}

                  <div className="pattern-tags">
                    {report.matched_patterns.map((pattern) => (
                      <span key={pattern}>{pattern}</span>
                    ))}
                  </div>
                </div>
              )}
            </section>
          </div>

          <footer>
            <span>OpsPilot <span className="footer-dot">·</span> AI DevOps Copilot</span>
            <span><span className="status-dot" /> Local-first analysis</span>
          </footer>
        </div>
      </section>
    </main>
  );
}

export default App;


