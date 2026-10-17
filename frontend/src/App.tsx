
import { useEffect, useState } from "react";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  CircleHelp,
  Clock,
  FileText,
  Loader2,
  Search,
  Server,
  ShieldAlert,
  Terminal,
  Trash2,
  ArrowLeft,
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

type IncidentHistoryItem = {
  id: string;
  createdAt: string;
  logs: string;
  report: IncidentReport;
};

type Page = "analyzer" | "services" | "history";

const HISTORY_KEY = "opspilot-incident-history";

function loadHistory(): IncidentHistoryItem[] {
  try {
    const saved = localStorage.getItem(HISTORY_KEY);
    return saved ? JSON.parse(saved) : [];
  } catch {
    return [];
  }
}

function App() {
  const [page, setPage] = useState<Page>("analyzer");

  const [logs, setLogs] = useState(
    "2026-10-15 10:22:01 ERROR payment-api Database connection failed: connection timeout"
  );
  const [service, setService] = useState("payment-api");
  const [environment, setEnvironment] = useState("local");
  const [report, setReport] = useState<IncidentReport | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const [history, setHistory] =
    useState<IncidentHistoryItem[]>(loadHistory);

  useEffect(() => {
    try {
      localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
    } catch (storageError) {
      console.error("Could not save incident history:", storageError);
    }
  }, [history]);

  async function analyzeLogs() {
    if (!logs.trim() || !service.trim() || loading) return;

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
            service_name: service.trim(),
            environment,
          }),
        }
      );

      if (!response.ok) {
        const details = await response.text();
        throw new Error(
          `API request failed (${response.status}): ${details}`
        );
      }

      const result: IncidentReport = await response.json();

      setReport(result);

      const item: IncidentHistoryItem = {
        id: crypto.randomUUID(),
        createdAt: new Date().toISOString(),
        logs,
        report: result,
      };

      setHistory((previous) => [item, ...previous]);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not connect to the local API."
      );
    } finally {
      setLoading(false);
    }
  }

  function openIncident(item: IncidentHistoryItem) {
    setLogs(item.logs);
    setService(item.report.service_name);
    setEnvironment(item.report.environment);
    setReport(item.report);
    setError("");
    setPage("analyzer");
  }

  function deleteIncident(id: string) {
    setHistory((previous) => previous.filter((item) => item.id !== id));
  }

  function clearHistory() {
    if (window.confirm("Delete all saved incident history?")) {
      setHistory([]);
    }
  }

  const services = Array.from(
    new Map(
      history.map((item) => [
        `${item.report.service_name}::${item.report.environment}`,
        {
          name: item.report.service_name,
          environment: item.report.environment,
          lastSeen: item.createdAt,
          count: history.filter(
            (other) =>
              other.report.service_name === item.report.service_name &&
              other.report.environment === item.report.environment
          ).length,
        },
      ])
    ).values()
  );

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

        <button
          type="button"
          className={`nav-item ${page === "analyzer" ? "active" : ""}`}
          onClick={() => setPage("analyzer")}
        >
          <Activity size={18} /> Incident Analyzer
        </button>

        <button
          type="button"
          className={`nav-item ${page === "services" ? "active" : ""}`}
          onClick={() => setPage("services")}
        >
          <Server size={18} /> Services
          <span className="nav-count">{services.length}</span>
        </button>

        <button
          type="button"
          className={`nav-item ${page === "history" ? "active" : ""}`}
          onClick={() => setPage("history")}
        >
          <FileText size={18} /> Incident History
          <span className="nav-count">{history.length}</span>
        </button>

        <div className="sidebar-bottom">
          <div className="status-dot" />
          <span>Local API</span>
          <span className="online">READY</span>
        </div>
      </aside>

      <section className="main-content">
        <header className="topbar">
          <div className="breadcrumb">
            Workspace / <b>
              {page === "analyzer"
                ? "Incident Analyzer"
                : page === "services"
                  ? "Services"
                  : "Incident History"}
            </b>
          </div>
          <div className="environment-badge">
            <span className="status-dot" /> LOCAL ENVIRONMENT
          </div>
        </header>

        <div className="page-content">
          {page === "analyzer" && (
            <>
              <div className="page-heading">
                <div>
                  <div className="eyebrow">OPERATIONS CENTER</div>
                  <h1>Incident Analyzer</h1>
                  <p>
                    Investigate application errors and identify possible root
                    causes.
                  </p>
                </div>
                <div className="version-tag">v0.2.0</div>
              </div>

              <div className="stats-grid">
                <article className="stat-card">
                  <span>ANALYSIS ENGINE</span>
                  <div className="stat-value"><Activity /> Rule-based</div>
                  <small>Local API processing</small>
                </article>
                <article className="stat-card">
                  <span>SELECTED SERVICE</span>
                  <div className="stat-value">
                    <Server /> {service || "Not set"}
                  </div>
                  <small>Application under investigation</small>
                </article>
                <article className="stat-card">
                  <span>LAST ANALYSIS</span>
                  <div className="stat-value">
                    {report ? <CheckCircle2 /> : <CircleHelp />}
                    {report ? "Completed" : "Not run"}
                  </div>
                  <small>{history.length} saved analysis(es)</small>
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
                    maxLength={100}
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
                    <span>{logs.length.toLocaleString()} characters</span>
                  </div>

                  <textarea
                    id="logs"
                    value={logs}
                    onChange={(event) => setLogs(event.target.value)}
                    placeholder="Paste application logs here..."
                    spellCheck={false}
                    maxLength={50000}
                  />

                  <button
                    type="button"
                    className="analyze-button"
                    onClick={analyzeLogs}
                    disabled={loading || !logs.trim() || !service.trim()}
                  >
                    {loading
                      ? <Loader2 className="spin" />
                      : <Search size={18} />}
                    {loading ? "Analyzing logs..." : "Analyze incident"}
                  </button>

                  <p className="privacy-note">
                    <ShieldAlert size={15} />
                    Logs are sent to your local API.
                  </p>
                </section>

                <section className="panel results-panel">
                  <div className="panel-heading">
                    <div className="heading-icon purple">
                      <Activity size={18} />
                    </div>
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
                      <p>
                        Submit your logs to discover error patterns, severity,
                        and recommended troubleshooting steps.
                      </p>
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
                          <span className="result-label">
                            DETECTED SEVERITY
                          </span>
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
            </>
          )}

          {page === "services" && (
            <>
              <div className="page-heading">
                <div>
                  <div className="eyebrow">WORKSPACE</div>
                  <h1>Services</h1>
                  <p>
                    Services discovered from your saved incident analyses.
                  </p>
                </div>
                <div className="version-tag">{services.length} service(s)</div>
              </div>

              <section className="panel data-panel">
                {services.length === 0 ? (
                  <div className="empty-state">
                    <Server size={32} />
                    <h3>No services yet</h3>
                    <p>
                      Analyze logs for a service to see it listed here.
                    </p>
                    <button
                      type="button"
                      className="analyze-button"
                      onClick={() => setPage("analyzer")}
                    >
                      <Search size={18} /> Go to Incident Analyzer
                    </button>
                  </div>
                ) : (
                  <div className="table-wrap">
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>Service</th>
                          <th>Environment</th>
                          <th>Analyses</th>
                          <th>Last analyzed</th>
                          <th>Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {services.map((item) => (
                          <tr key={`${item.name}::${item.environment}`}>
                            <td><Server size={16} /> {item.name}</td>
                            <td>{item.environment}</td>
                            <td>{item.count}</td>
                            <td>{new Date(item.lastSeen).toLocaleString()}</td>
                            <td>
                              <button
                                type="button"
                                className="small-button"
                                onClick={() => {
                                  setService(item.name);
                                  setEnvironment(item.environment);
                                  setReport(null);
                                  setError("");
                                  setPage("analyzer");
                                }}
                              >
                                Analyze
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
                <p className="privacy-note">
                  <CircleHelp size={15} />
                  Service entries are based on local analysis history, not live
                  infrastructure health checks.
                </p>
              </section>
            </>
          )}

          {page === "history" && (
            <>
              <div className="page-heading">
                <div>
                  <div className="eyebrow">WORKSPACE</div>
                  <h1>Incident History</h1>
                  <p>Review and reopen previous log analyses.</p>
                </div>
                {history.length > 0 && (
                  <button
                    type="button"
                    className="small-button danger-button"
                    onClick={clearHistory}
                  >
                    <Trash2 size={16} /> Clear history
                  </button>
                )}
              </div>

              <section className="panel data-panel">
                {history.length === 0 ? (
                  <div className="empty-state">
                    <Clock size={32} />
                    <h3>No incidents saved</h3>
                    <p>
                      Successful analyses will appear here automatically.
                    </p>
                    <button
                      type="button"
                      className="analyze-button"
                      onClick={() => setPage("analyzer")}
                    >
                      <Search size={18} /> Analyze your first incident
                    </button>
                  </div>
                ) : (
                  <div className="history-list">
                    {history.map((item) => (
                      <article className="history-item" key={item.id}>
                        <div className="history-item-main">
                          <div className={`severity ${item.report.severity}`}>
                            <span /> {item.report.severity.toUpperCase()}
                          </div>
                          <h3>{item.report.service_name}</h3>
                          <p>{item.report.summary}</p>
                          <div className="history-meta">
                            <span>
                              <Clock size={14} />
                              {new Date(item.createdAt).toLocaleString()}
                            </span>
                            <span>{item.report.environment}</span>
                            <span>
                              {item.report.matched_patterns.length} pattern(s)
                            </span>
                          </div>
                        </div>
                        <div className="history-actions">
                          <button
                            type="button"
                            className="small-button"
                            onClick={() => openIncident(item)}
                          >
                            <ArrowLeft size={15} /> View report
                          </button>
                          <button
                            type="button"
                            className="icon-button"
                            aria-label="Delete incident"
                            title="Delete incident"
                            onClick={() => deleteIncident(item.id)}
                          >
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </article>
                    ))}
                  </div>
                )}
              </section>
            </>
          )}

          <footer>
            <span>
              OpsPilot <span className="footer-dot">·</span> AI DevOps Copilot
            </span>
            <span><span className="status-dot" /> Local-first analysis</span>
          </footer>
        </div>
      </section>
    </main>
  );
}

export default App;
