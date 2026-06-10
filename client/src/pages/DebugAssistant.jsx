import React, { useState, useEffect } from "react";
import { useUser } from "@clerk/clerk-react";
import NavLogo from "../components/NavLogo";

import CustomUserMenu from "../components/CustomUserMenu";
import { useNavigate } from "react-router-dom";

const DebugAssistant = () => {
  const { user } = useUser();
  const navigate = useNavigate();

  const [code, setCode] = useState("");
  const [errorLog, setErrorLog] = useState("");
  const [language, setLanguage] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [activeTab, setActiveTab] = useState("overview");

  const F = { fontFamily: "'DM Mono', monospace" };
  const BG = "#252523";
  const PANEL_BG = "#1c1c1a";
  const INK = "#efefdc";
  const INK2 = "#c4ccc9";
  const BORDER = "#2a2a28";
  const TECH_BLUE = "#00d2ff";
  const CRISIS_RED = "#c33620"; // Tool brand color for tracking bugs
  const SUCCESS_GREEN = "#4ade80";

  useEffect(() => {
    document.title = "StackPilot - Debug Assistant";
    if (!user) return;
    fetch(`http://localhost:8000/api/dashboard-analytics/${user.id}`)
      .then((res) => res.json())
      .then((data) => {
        if (data && data.time_series_7d) {
          const todayData = data.time_series_7d[data.time_series_7d.length - 1];
          const todayDebugRuns = todayData["debug-assistant"] || 0;
        }
      })
      .catch((err) => console.error("Failed to sync tool telemetry:", err));
  }, [user]);

  const handleAnalyze = async (e) => {
    e?.preventDefault();
    if (!errorLog) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch("http://localhost:8000/api/debug", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          code: code,
          error: errorLog,
          language: language || "Auto-detect",
          clerk_id: user?.id || "",
        }),
      });

      if (!response.ok)
        throw new Error("Telemetry validation diagnostic failure.");
      const data = await response.json();

      setResult(data);
      setActiveTab("overview");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const TABS = [
    { id: "overview", label: "Root Cause" },
    { id: "explanation", label: "Technical Breakdown" },
    { id: "fixed_code", label: "Fixed Solution" },
    { id: "prevention", label: "Prevention Steps" },
  ];

  return (
    <div
      style={{
        background: BG,
        minHeight: "100vh",
        height: "100vh",
        overflowY: "auto",
        overflowX: "hidden",
        color: "#ffffff",
        padding: "0 24px 40px",
        fontFamily: "'Syne', sans-serif",
      }}
    >
      {/* ── CUSTOM DARK NAVBAR ──────────────────────────────────────── */}
      <nav
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          height: 64,
          borderBottom: `1px solid ${BORDER}`,
          marginBottom: 48,
        }}
      >
        <NavLogo />

        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          {[
            { n: "Dashboard", p: "/ai" },
            { n: "Repo CoPilot", p: "/ai/repository-copilot" },
            { n: "Code Explain", p: "/ai/code-explain" },
            { n: "Review Resume", p: "/ai/review-resume" },
          ].map((t) => (
            <button
              key={t.n}
              onClick={() => navigate(t.p)}
              style={{
                ...F,
                fontSize: 12,
                color: INK,
                background: "transparent",
                border: `1px solid ${BORDER}`,
                padding: "6px 14px",
                borderRadius: 6,
                cursor: "pointer",
                transition: "all 0.2s",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = CRISIS_RED;
                e.currentTarget.style.color = CRISIS_RED;
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = BORDER;
                e.currentTarget.style.color = INK;
              }}
            >
              {t.n}
            </button>
          ))}
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 24 }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 12,
              borderLeft: `1px solid ${BORDER}`,
              paddingLeft: 20,
            }}
          >
            <CustomUserMenu user={user} />
          </div>
        </div>
      </nav>

      {/* ── MAIN CONTENT ─────────────────────────────────────────────── */}
      <div style={{ maxWidth: 1000, margin: "0 auto" }}>
        <div style={{ textAlign: "center", marginBottom: 48 }}>
          <h1
            style={{
              fontSize: 42,
              fontWeight: 800,
              letterSpacing: "-1px",
              margin: "0 0 12px 0",
              color: "#ffffff",
            }}
          >
            Debug <span style={{ color: CRISIS_RED }}>Assistant</span>
          </h1>
          <p
            style={{
              color: INK,
              fontSize: 16,
              margin: 0,
              maxWidth: 600,
              marginInline: "auto",
            }}
          >
            Feed your terminal crashes and broken application contexts. Trace
            runtime stack memory execution flags instantly.
          </p>
        </div>

        {/* Input Console */}
        <div
          style={{
            background: PANEL_BG,
            borderRadius: 16,
            border: `1px solid ${BORDER}`,
            padding: "32px",
            marginBottom: 48,
            boxShadow: "0 24px 48px rgba(0,0,0,0.2)",
          }}
        >
          <form
            onSubmit={handleAnalyze}
            style={{ display: "flex", flexDirection: "column", gap: 16 }}
          >
            {/* Top Config Row */}
            <div style={{ display: "flex", gap: 16 }}>
              <div style={{ flex: 1 }}>
                <input
                  type="text"
                  placeholder="Error log string prompt summary (e.g. TypeError: cannot read...)"
                  value={errorLog}
                  onChange={(e) => setErrorLog(e.target.value)}
                  style={{
                    width: "100%",
                    background: "#111",
                    border: `1px solid ${BORDER}`,
                    borderRadius: 6,
                    padding: "12px 16px",
                    color: "#fff",
                    ...F,
                    fontSize: 13,
                    outline: "none",
                  }}
                  required
                />
              </div>

              <div>
                <select
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  style={{
                    width: 200,
                    background: "#111",
                    border: `1px solid ${BORDER}`,
                    borderRadius: 6,
                    padding: "12px 16px",
                    color: "#fff",
                    ...F,
                    fontSize: 12,
                    outline: "none",
                    cursor: "pointer",
                  }}
                >
                  <option value="">Auto-detect Language</option>
                  <option value="JavaScript">JavaScript</option>
                  <option value="TypeScript">TypeScript</option>
                  <option value="Python">Python</option>
                  <option value="Java">Java</option>
                  <option value="C++">C++</option>
                  <option value="Rust">Rust</option>
                  <option value="Go">Go</option>
                  <option value="SQL">SQL</option>
                </select>
              </div>
            </div>

            {/* Code Context Area */}
            <div style={{ position: "relative" }}>
              <textarea
                placeholder="// Paste the underlying script code context here..."
                value={code}
                onChange={(e) => setCode(e.target.value)}
                style={{
                  width: "100%",
                  height: 240,
                  background: "#0e0e0e",
                  border: `1px solid ${BORDER}`,
                  borderRadius: 8,
                  padding: "20px",
                  color: "#4ade80",
                  ...F,
                  fontSize: 13,
                  outline: "none",
                  resize: "vertical",
                  lineHeight: 1.6,
                }}
              />
            </div>

            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 16,
                marginTop: 8,
              }}
            >
              <button
                type="submit"
                disabled={loading}
                style={{
                  background: CRISIS_RED,
                  color: "#fff",
                  fontWeight: 800,
                  fontSize: 13,
                  ...F,
                  padding: "14px 28px",
                  borderRadius: 8,
                  border: "none",
                  cursor: loading ? "wait" : "pointer",
                  opacity: loading ? 0.7 : 1,
                  transition: "all 0.2s cubic-bezier(0.4, 0, 0.2, 1)",
                  transform: "translateY(0)",
                  boxShadow: "none",
                }}
                onMouseEnter={(e) => {
                  if (!loading) {
                    e.currentTarget.style.transform = "translateY(-2px)";
                    e.currentTarget.style.boxShadow = `0 8px 24px ${CRISIS_RED}60`;
                  }
                }}
                onMouseLeave={(e) => {
                  if (!loading) {
                    e.currentTarget.style.transform = "translateY(0)";
                    e.currentTarget.style.boxShadow = "none";
                  }
                }}
              >
                {loading
                  ? "[ RUNNING DIAGNOSTICS... ]"
                  : "[ REPAIR RUNTIME ERROR → ]"}
              </button>
            </div>
          </form>
          {error && (
            <div
              style={{ ...F, fontSize: 12, color: CRISIS_RED, marginTop: 16 }}
            >
              Telemetry Fault: {error}
            </div>
          )}
        </div>

        {/* Output Results Window */}
        {result && (
          <div
            style={{
              background: PANEL_BG,
              borderRadius: 16,
              border: `1px solid ${BORDER}`,
              overflow: "hidden",
              marginBottom: 60,
            }}
          >
            <div
              style={{
                display: "flex",
                borderBottom: `1px solid ${BORDER}`,
                background: "#181817",
                overflowX: "auto",
              }}
            >
              {TABS.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  style={{
                    background: "transparent",
                    border: "none",
                    padding: "16px 24px",
                    cursor: "pointer",
                    ...F,
                    fontSize: 12,
                    fontWeight: 700,
                    textTransform: "uppercase",
                    letterSpacing: "0.05em",
                    color: activeTab === tab.id ? CRISIS_RED : INK,
                    borderBottom:
                      activeTab === tab.id
                        ? `2px solid ${CRISIS_RED}`
                        : "2px solid transparent",
                    transition: "all 0.2s",
                  }}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            <div style={{ padding: 32 }}>
              {/* 1. Root Cause Analysis */}
              {activeTab === "overview" && (
                <div>
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 16,
                      marginBottom: 20,
                    }}
                  >
                    <h3 style={{ fontSize: 20, fontWeight: 700, margin: 0 }}>
                      Root Cause Analysis
                    </h3>
                    <div
                      style={{
                        ...F,
                        fontSize: 11,
                        background: "rgba(255,95,87,0.1)",
                        border: `1px solid ${CRISIS_RED}`,
                        color: CRISIS_RED,
                        padding: "2px 10px",
                        borderRadius: 4,
                      }}
                    >
                      CONFIDENCE: {result.confidence || 50}%
                    </div>
                  </div>
                  <p
                    style={{ color: "#d1d1d1", lineHeight: 1.8, fontSize: 15 }}
                  >
                    {result.rootCause}
                  </p>
                </div>
              )}

              {/* 2. Technical Breakdown Points */}
              {activeTab === "explanation" && (
                <div>
                  <h3
                    style={{ fontSize: 20, fontWeight: 700, marginBottom: 20 }}
                  >
                    Diagnostic Telemetry Notes
                  </h3>
                  <div
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: 14,
                    }}
                  >
                    {result.technicalExplanation?.map((item, idx) => (
                      <div
                        key={idx}
                        style={{
                          background: "#111",
                          border: `1px solid ${BORDER}`,
                          padding: "16px 20px",
                          borderRadius: 8,
                          color: "#d1d1d1",
                          fontSize: 14,
                          lineHeight: 1.6,
                        }}
                      >
                        ⚡ {item}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 3. Patch Fixed Code Box */}
              {activeTab === "fixed_code" && (
                <div>
                  <h3
                    style={{ fontSize: 20, fontWeight: 700, marginBottom: 16 }}
                  >
                    Resolved Code Block
                  </h3>
                  {result.fixedCode ? (
                    <div
                      style={{
                        background: "#0e0e0e",
                        border: `1px solid ${BORDER}`,
                        padding: 24,
                        borderRadius: 12,
                        position: "relative",
                      }}
                    >
                      <pre
                        style={{
                          ...F,
                          color: SUCCESS_GREEN,
                          fontSize: 13,
                          margin: 0,
                          overflowX: "auto",
                          lineHeight: 1.6,
                        }}
                      >
                        {result.fixedCode}
                      </pre>
                    </div>
                  ) : (
                    <p
                      style={{ color: INK, fontSize: 14, fontStyle: "italic" }}
                    >
                      No script replacements required to apply this remediation
                      path.
                    </p>
                  )}
                </div>
              )}

              {/* 4. Prevention Steps */}
              {activeTab === "prevention" && (
                <div>
                  <h3
                    style={{ fontSize: 20, fontWeight: 700, marginBottom: 20 }}
                  >
                    Refactoring Guidelines
                  </h3>
                  <div
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: 12,
                    }}
                  >
                    {result.prevention?.map((tip, idx) => (
                      <div
                        key={idx}
                        style={{
                          background: "rgba(255, 95, 87, 0.03)",
                          borderLeft: `3px solid ${CRISIS_RED}`,
                          padding: "16px 20px",
                          color: "#d1d1d1",
                          fontSize: 15,
                          lineHeight: 1.6,
                        }}
                      >
                        ✔ {tip}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DebugAssistant;
