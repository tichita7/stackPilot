import React, { useState, useEffect } from "react";
import { onAuthStateChanged } from "firebase/auth";
import { auth } from "../firebase";
import NavLogo from "../components/NavLogo";
import CustomUserMenu from "../components/CustomUserMenu";
import { useNavigate } from "react-router-dom";

const CodeExplain = () => {
  const [user, setUser] = useState(null);
  const navigate = useNavigate();

  const [code, setCode] = useState("");
  const [language, setLanguage] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [activeTab, setActiveTab] = useState("overview");

  useEffect(() => {
    document.title = "StackPilot - Code Explain";
    const unsub = onAuthStateChanged(auth, setUser);
    return () => unsub();
  }, []);

  const F = { fontFamily: "'DM Mono', monospace" };
  const BG = "#252523";
  const PANEL_BG = "#1c1c1a";
  const INK = "#efefdc";
  const INK2 = "#c4ccc9";
  const BORDER = "#2a2a28";
  const TECH_BLUE = "#00d2ff";
  const SUCCESS_GREEN = "#4ade80";
  const PURPLE_ACCENT = "#d86ce6";

  const handleAnalyze = async (e) => {
    e?.preventDefault();
    if (!code) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const idToken = auth.currentUser
        ? await auth.currentUser.getIdToken()
        : "";
      const response = await fetch(
        "https://stackpilot-oom6.onrender.com/api/code-explain",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            code: code,
            language: language || "Auto-detect",
            id_token: idToken,
          }),
        },
      );

      if (!response.ok) throw new Error("Backend connection failed.");
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
    { id: "overview", label: "Overview" },
    { id: "breakdown", label: "Step-by-Step" },
    { id: "complexity", label: "Complexity" },
    { id: "improvements", label: "Improvements" },
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
            { n: "Debug Assistant", p: "/ai/debug-assistant" },
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
                e.currentTarget.style.borderColor = PURPLE_ACCENT;
                e.currentTarget.style.color = PURPLE_ACCENT;
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
            style={{ display: "flex", flexDirection: "column", gap: 4 }}
          ></div>
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
            Code <span style={{ color: PURPLE_ACCENT }}>Explain</span>
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
            Paste any complex function or script. The AI will break it down
            line-by-line and analyze its time and space complexity.
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
            {/* Language Dropdown */}
            <div style={{ display: "flex", justifyContent: "flex-end" }}>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                style={{
                  width: 250,
                  background: "#111",
                  border: `1px solid ${BORDER}`,
                  borderRadius: 6,
                  padding: "10px 16px",
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
                <option value="React/JSX">React (JSX/TSX)</option>
                <option value="Python">Python</option>
                <option value="Java">Java</option>
                <option value="C++">C++</option>
                <option value="C#">C#</option>
                <option value="Go">Go</option>
                <option value="Rust">Rust</option>
                <option value="PHP">PHP</option>
                <option value="Ruby">Ruby</option>
                <option value="SQL">SQL</option>
                <option value="Swift">Swift</option>
              </select>
            </div>

            {/* Code Textarea */}
            <div style={{ position: "relative" }}>
              <textarea
                placeholder="// Paste your raw code here..."
                value={code}
                onChange={(e) => setCode(e.target.value)}
                style={{
                  width: "100%",
                  height: 280,
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
                required
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
                  background: PURPLE_ACCENT,
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
                    e.currentTarget.style.boxShadow = `0 8px 24px ${PURPLE_ACCENT}60`;
                  }
                }}
                onMouseLeave={(e) => {
                  if (!loading) {
                    e.currentTarget.style.transform = "translateY(0)";
                    e.currentTarget.style.boxShadow = "none";
                  }
                }}
              >
                {loading ? "[ COMPILING... ]" : "[ EXPLAIN CODE → ]"}
              </button>
            </div>
          </form>
          {error && (
            <div
              style={{ ...F, fontSize: 12, color: "#ff5f57", marginTop: 16 }}
            >
              Error: {error}
            </div>
          )}
        </div>

        {/* Output Results */}
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
                    color: activeTab === tab.id ? PURPLE_ACCENT : INK,
                    borderBottom:
                      activeTab === tab.id
                        ? `2px solid ${PURPLE_ACCENT}`
                        : "2px solid transparent",
                    transition: "all 0.2s",
                  }}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            <div style={{ padding: 32 }}>
              {activeTab === "overview" && (
                <div>
                  <h3
                    style={{ fontSize: 20, fontWeight: 700, marginBottom: 16 }}
                  >
                    Executive Summary
                  </h3>
                  <p
                    style={{ color: "#d1d1d1", lineHeight: 1.8, fontSize: 15 }}
                  >
                    {result.summary}
                  </p>
                </div>
              )}

              {activeTab === "breakdown" && (
                <div>
                  <h3
                    style={{ fontSize: 20, fontWeight: 700, marginBottom: 20 }}
                  >
                    Step-by-Step Execution
                  </h3>
                  <div
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: 16,
                    }}
                  >
                    {result.breakdown?.map((step, idx) => (
                      <div
                        key={idx}
                        style={{
                          background: "#111",
                          border: `1px solid ${BORDER}`,
                          padding: 20,
                          borderRadius: 8,
                          display: "flex",
                          gap: 20,
                        }}
                      >
                        <div
                          style={{
                            color: PURPLE_ACCENT,
                            ...F,
                            fontSize: 16,
                            fontWeight: 800,
                          }}
                        >
                          0{idx + 1}
                        </div>
                        <div
                          style={{
                            color: "#d1d1d1",
                            fontSize: 15,
                            lineHeight: 1.6,
                          }}
                        >
                          {step}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {activeTab === "complexity" && (
                <div>
                  <h3
                    style={{ fontSize: 20, fontWeight: 700, marginBottom: 24 }}
                  >
                    Big-O Analysis
                  </h3>
                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: "1fr 1fr",
                      gap: 24,
                    }}
                  >
                    <div
                      style={{
                        background: "#111",
                        border: `1px solid ${BORDER}`,
                        padding: 32,
                        borderRadius: 12,
                        textAlign: "center",
                      }}
                    >
                      <div
                        style={{
                          ...F,
                          color: INK2,
                          textTransform: "uppercase",
                          fontSize: 12,
                          marginBottom: 16,
                          letterSpacing: "0.1em",
                        }}
                      >
                        Time Complexity
                      </div>
                      <div
                        style={{
                          fontSize: 48,
                          fontWeight: 800,
                          color: "#ff5f57",
                          ...F,
                        }}
                      >
                        {result.complexity?.time || "O(?)"}
                      </div>
                    </div>
                    <div
                      style={{
                        background: "#111",
                        border: `1px solid ${BORDER}`,
                        padding: 32,
                        borderRadius: 12,
                        textAlign: "center",
                      }}
                    >
                      <div
                        style={{
                          ...F,
                          color: INK2,
                          textTransform: "uppercase",
                          fontSize: 12,
                          marginBottom: 16,
                          letterSpacing: "0.1em",
                        }}
                      >
                        Space Complexity
                      </div>
                      <div
                        style={{
                          fontSize: 48,
                          fontWeight: 800,
                          color: TECH_BLUE,
                          ...F,
                        }}
                      >
                        {result.complexity?.space || "O(?)"}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === "improvements" && (
                <div>
                  <h3
                    style={{ fontSize: 20, fontWeight: 700, marginBottom: 20 }}
                  >
                    Refactoring Suggestions
                  </h3>
                  <div
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: 12,
                    }}
                  >
                    {result.improvements?.map((tip, idx) => (
                      <div
                        key={idx}
                        style={{
                          background: "rgba(178, 118, 239, 0.05)",
                          borderLeft: `3px solid ${PURPLE_ACCENT}`,
                          padding: "16px 20px",
                          color: "#d1d1d1",
                          fontSize: 15,
                          lineHeight: 1.6,
                        }}
                      >
                        {tip}
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

export default CodeExplain;
