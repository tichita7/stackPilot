import React, { useState, useEffect } from "react";
import { onAuthStateChanged } from "firebase/auth";
import { auth } from "../firebase";
import NavLogo from "../components/NavLogo";
import CustomUserMenu from "../components/CustomUserMenu";
import { useNavigate } from "react-router-dom";

const RepositoryCopilot = () => {
  const [user, setUser] = useState(null);
  const navigate = useNavigate();

  const [url, setUrl] = useState("");
  const [goal, setGoal] = useState("");
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
  const TECH_BLUE = "#6d7bf1";
  const SUCCESS_GREEN = "#4ade80";

  useEffect(() => {
    document.title = "StackPilot - Repository Copilot";
    const unsub = onAuthStateChanged(auth, setUser);
    return () => unsub();
  }, []);

  const handleAnalyze = async (e) => {
    e?.preventDefault();
    if (!url) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const idToken = auth.currentUser 
  ? await auth.currentUser.getIdToken() 
  : "";
      const response = await fetch(
        "https://stackpilot-oom6.onrender.com/api/repository-copilot",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            repo_url: url,
            goal: goal,
            id_token: idToken,
          }),
        },
      );

      if (!response.ok) throw new Error("Failed to map repository.");
      const data = await response.json();

      if (data.error) throw new Error(data.error);

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
    { id: "tech_stack", label: "Tech Stack" },
    { id: "insights", label: "Insights" },
    { id: "files", label: "Files" },
    { id: "quick_start", label: "Quick Start" },
    { id: "change_plan", label: "Change Plan" },
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
            { n: "Debug Assistant", p: "/ai/debug-assistant" },
            { n: "Code Explainer", p: "/ai/code-explain" },
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
                e.currentTarget.style.borderColor = TECH_BLUE;
                e.currentTarget.style.color = TECH_BLUE;
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
            Repository <span style={{ color: TECH_BLUE }}>CoPilot</span>
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
            Instantly map, analyze, and understand any GitHub codebase with
            high-precision AI-driven architectural mapping.
          </p>
        </div>

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
            <div style={{ display: "flex", gap: 16 }}>
              <div style={{ flex: 1, position: "relative" }}>
                <div
                  style={{
                    position: "absolute",
                    left: 16,
                    top: 18,
                    ...F,
                    fontSize: 12,
                    color: TECH_BLUE,
                  }}
                >
                  URL:
                </div>
                <input
                  type="text"
                  placeholder="https://github.com/facebook/react"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  style={{
                    width: "100%",
                    background: "#111",
                    border: `1px solid ${BORDER}`,
                    borderRadius: 8,
                    padding: "16px 16px 16px 54px",
                    color: "#fff",
                    ...F,
                    fontSize: 14,
                    outline: "none",
                  }}
                  required
                />
              </div>
              <div style={{ flex: 1, position: "relative" }}>
                <div
                  style={{
                    position: "absolute",
                    left: 16,
                    top: 18,
                    ...F,
                    fontSize: 12,
                    color: INK,
                  }}
                >
                  GOAL:
                </div>
                <input
                  type="text"
                  placeholder="Map the routing architecture..."
                  value={goal}
                  onChange={(e) => setGoal(e.target.value)}
                  style={{
                    width: "100%",
                    background: "#111",
                    border: `1px solid ${BORDER}`,
                    borderRadius: 8,
                    padding: "16px 16px 16px 60px",
                    color: "#fff",
                    ...F,
                    fontSize: 14,
                    outline: "none",
                  }}
                />
              </div>
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
                  background: TECH_BLUE,
                  color: "#000",
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
                    e.currentTarget.style.boxShadow = `0 8px 24px ${TECH_BLUE}60`;
                  }
                }}
                onMouseLeave={(e) => {
                  if (!loading) {
                    e.currentTarget.style.transform = "translateY(0)";
                    e.currentTarget.style.boxShadow = "none";
                  }
                }}
              >
                {loading ? "[ ANALYZING... ]" : "[ ANALYZE REPOSITORY → ]"}
              </button>
              <div style={{ display: "flex", gap: 12 }}>
                {[
                  "Analyze Next.js App Router",
                  "Find Auth Flow",
                  "Map DB Schema",
                ].map((chip) => (
                  <button
                    key={chip}
                    type="button"
                    onClick={() => setGoal(chip)}
                    style={{
                      background: "transparent",
                      border: `1px solid ${BORDER}`,
                      color: INK,
                      ...F,
                      fontSize: 10,
                      padding: "6px 12px",
                      borderRadius: 100,
                      cursor: "pointer",
                      textTransform: "uppercase",
                    }}
                    onMouseEnter={(e) => (e.target.style.borderColor = INK)}
                    onMouseLeave={(e) => (e.target.style.borderColor = BORDER)}
                  >
                    {chip}
                  </button>
                ))}
              </div>
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
                    color: activeTab === tab.id ? TECH_BLUE : INK,
                    borderBottom:
                      activeTab === tab.id
                        ? `2px solid ${TECH_BLUE}`
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
                    Project Architecture Summary
                  </h3>
                  <p
                    style={{ color: "#d1d1d1", lineHeight: 1.8, fontSize: 15 }}
                  >
                    {result.overview}
                  </p>
                </div>
              )}
              {activeTab === "tech_stack" && (
                <div>
                  <h3
                    style={{ fontSize: 20, fontWeight: 700, marginBottom: 24 }}
                  >
                    Stack Composition
                  </h3>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 12 }}>
                    {result.tech_stack?.map((tech, idx) => (
                      <div
                        key={idx}
                        style={{
                          background: "rgba(0, 210, 255, 0.1)",
                          border: `1px solid ${TECH_BLUE}`,
                          color: TECH_BLUE,
                          ...F,
                          padding: "8px 16px",
                          borderRadius: 6,
                          fontSize: 14,
                        }}
                      >
                        {tech}
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {activeTab === "insights" && (
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
                    gap: 24,
                  }}
                >
                  {Object.entries(result.developer_insights || {}).map(
                    ([key, value]) => (
                      <div
                        key={key}
                        style={{
                          background: "#111",
                          border: `1px solid ${BORDER}`,
                          padding: 24,
                          borderRadius: 12,
                        }}
                      >
                        <div
                          style={{
                            ...F,
                            color: SUCCESS_GREEN,
                            textTransform: "uppercase",
                            fontSize: 12,
                            marginBottom: 12,
                          }}
                        >
                          {key.replace("_", " ")}
                        </div>
                        <div
                          style={{
                            color: "#d1d1d1",
                            fontSize: 14,
                            lineHeight: 1.6,
                          }}
                        >
                          {value}
                        </div>
                      </div>
                    ),
                  )}
                </div>
              )}
              {activeTab === "files" && (
                <div>
                  <h3
                    style={{ fontSize: 20, fontWeight: 700, marginBottom: 20 }}
                  >
                    File System Telemetry
                  </h3>
                  <div
                    style={{
                      background: "#0e0e0e",
                      border: `1px solid ${BORDER}`,
                      padding: 24,
                      borderRadius: 12,
                      ...F,
                      color: "#d1d1d1",
                      fontSize: 14,
                      lineHeight: 2,
                    }}
                  >
                    {result.important_files?.map((file, idx) => (
                      <div
                        key={idx}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: 12,
                        }}
                      >
                        <span style={{ color: INK }}>📄</span> {file}
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {activeTab === "quick_start" && (
                <div>
                  <h3
                    style={{ fontSize: 20, fontWeight: 700, marginBottom: 20 }}
                  >
                    Local Deployment Protocol
                  </h3>
                  <div
                    style={{
                      background: "#0e0e0e",
                      border: `1px solid ${BORDER}`,
                      padding: 24,
                      borderRadius: 12,
                    }}
                  >
                    <div style={{ display: "flex", gap: 8, marginBottom: 24 }}>
                      <div
                        style={{
                          width: 12,
                          height: 12,
                          borderRadius: "50%",
                          background: "#ff5f57",
                        }}
                      />
                      <div
                        style={{
                          width: 12,
                          height: 12,
                          borderRadius: "50%",
                          background: "#febc2e",
                        }}
                      />
                      <div
                        style={{
                          width: 12,
                          height: 12,
                          borderRadius: "50%",
                          background: "#28c840",
                        }}
                      />
                    </div>
                    <div
                      style={{
                        ...F,
                        color: SUCCESS_GREEN,
                        fontSize: 14,
                        lineHeight: 1.8,
                      }}
                    >
                      {result.quick_start?.map((cmd, idx) => (
                        <div key={idx}>$ {cmd}</div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
              {activeTab === "change_plan" && (
                <div>
                  <h3
                    style={{ fontSize: 20, fontWeight: 700, marginBottom: 16 }}
                  >
                    Execution Strategy
                  </h3>
                  <div style={{ marginBottom: 24 }}>
                    <div
                      style={{
                        ...F,
                        color: TECH_BLUE,
                        fontSize: 12,
                        marginBottom: 8,
                        textTransform: "uppercase",
                      }}
                    >
                      Targets
                    </div>
                    <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                      {result.change_plan?.files_to_modify?.map((f) => (
                        <span
                          key={f}
                          style={{
                            background: "#222",
                            padding: "4px 8px",
                            borderRadius: 4,
                            ...F,
                            fontSize: 12,
                          }}
                        >
                          {f}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div
                    style={{
                      ...F,
                      color: INK,
                      fontSize: 12,
                      marginBottom: 8,
                      textTransform: "uppercase",
                    }}
                  >
                    Step-by-Step
                  </div>
                  <div
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: 12,
                    }}
                  >
                    {result.change_plan?.steps?.map((step, idx) => (
                      <div
                        key={idx}
                        style={{
                          background: "#111",
                          border: `1px solid ${BORDER}`,
                          padding: 16,
                          borderRadius: 8,
                          display: "flex",
                          gap: 16,
                        }}
                      >
                        <div style={{ color: TECH_BLUE, ...F }}>0{idx + 1}</div>
                        <div style={{ color: "#d1d1d1", fontSize: 14 }}>
                          {step}
                        </div>
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

export default RepositoryCopilot;
