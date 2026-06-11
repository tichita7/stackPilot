import React, { useState, useEffect } from "react";
import { onAuthStateChanged } from "firebase/auth";
import { auth } from "../firebase";

import NavLogo from "../components/NavLogo";
import CustomUserMenu from "../components/CustomUserMenu";
import { useNavigate } from "react-router-dom";

const ReviewResume = () => {
  const [user, setUser] = useState(null);
  const navigate = useNavigate();

  const [file, setFile] = useState(null);
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
  const SUCCESS_GREEN = "#4ade80";
  const GOLD_ACCENT = "#eab308";

  useEffect(() => {
    document.title = "StackPilot - Review Resume";
    const unsub = onAuthStateChanged(auth, setUser);
    return () => unsub();
  }, []);

  const handleUpload = async (e) => {
    e?.preventDefault();
    if (!file) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const idToken = auth.currentUser
        ? await auth.currentUser.getIdToken()
        : "";
      const formData = new FormData(); // ✅ formData after idToken
      formData.append("file", file);
      formData.append("id_token", idToken);

      const response = await fetch(
        "https://stackpilot-oom6.onrender.com/api/review-resume",
        {
          method: "POST",
          body: formData,
        },
      );

      if (!response.ok) throw new Error("Resume parsing service unavailable.");
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
    { id: "strengths", label: "Strengths" },
    { id: "improvements", label: "Improvements" },
    { id: "keywords", label: "ATS Keywords" },
  ];

  return (
    <div
      style={{
        background: BG,
        minHeight: "100vh",
        height: "100vh",
        overflowY: "auto",
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
            { n: "Repo CoPilot", p: "/ai/repository-copilot" },
            { n: "Debug Assistant", p: "/ai/debug-assistant" },
            { n: "Code Explainer", p: "/ai/code-explain" },
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
                e.currentTarget.style.borderColor = GOLD_ACCENT;
                e.currentTarget.style.color = GOLD_ACCENT;
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

      <div style={{ maxWidth: 800, margin: "0 auto" }}>
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
            Resume <span style={{ color: GOLD_ACCENT }}>Reviewer</span>
          </h1>
          <p style={{ color: INK, fontSize: 16, margin: 0 }}>
            ATS optimization and career-ready critique.
          </p>
        </div>

        <div
          style={{
            background: PANEL_BG,
            borderRadius: 16,
            border: `1px solid ${BORDER}`,
            padding: "40px",
            marginBottom: 48,
            textAlign: "center",
          }}
        >
          <form onSubmit={handleUpload}>
            <div style={{ marginBottom: 24 }}>
              <label
                style={{
                  cursor: "pointer",
                  display: "inline-block",
                  background: "#111",
                  border: `2px dashed ${BORDER}`,
                  padding: "32px 64px",
                  borderRadius: 12,
                  color: INK,
                  ...F,
                }}
              >
                {file ? file.name : "Click to upload PDF Resume"}
                <input
                  type="file"
                  accept=".pdf"
                  onChange={(e) => setFile(e.target.files[0])}
                  style={{ display: "none" }}
                />
              </label>
            </div>
            <button
              type="submit"
              disabled={loading || !file}
              style={{
                background: GOLD_ACCENT,
                color: "#000",
                fontWeight: 800,
                fontSize: 13,
                ...F,
                padding: "14px 28px",
                borderRadius: 8,
                border: "none",
                cursor: loading ? "wait" : "pointer",
                opacity: loading || !file ? 0.5 : 1,
                transition: "all 0.2s",
              }}
            >
              {loading ? "SCANNING..." : "RUN ATS ANALYSIS →"}
            </button>
          </form>
          {error && (
            <div
              style={{ ...F, fontSize: 12, color: "#ff5f57", marginTop: 16 }}
            >
              {error}
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
            }}
          >
            <div
              style={{
                display: "flex",
                borderBottom: `1px solid ${BORDER}`,
                background: "#181817",
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
                    color: activeTab === tab.id ? GOLD_ACCENT : INK,
                    borderBottom:
                      activeTab === tab.id
                        ? `2px solid ${GOLD_ACCENT}`
                        : "none",
                  }}
                >
                  {tab.label}
                </button>
              ))}
            </div>
            <div style={{ padding: 32 }}>
              {activeTab === "overview" && (
                <h1
                  style={{
                    fontSize: 48,
                    fontWeight: 800,
                    color: GOLD_ACCENT,
                    ...F,
                  }}
                >
                  {result.score}/100
                </h1>
              )}
              {activeTab === "strengths" &&
                result.strengths?.map((s, i) => (
                  <div key={i} style={{ padding: "12px 0", color: "#d1d1d1" }}>
                    ✔ {s}
                  </div>
                ))}
              {activeTab === "improvements" &&
                result.improvements?.map((s, i) => (
                  <div key={i} style={{ padding: "12px 0", color: "#d1d1d1" }}>
                    ✖ {s}
                  </div>
                ))}
              {activeTab === "keywords" && (
                <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
                  {result.keywords?.map((k, i) => (
                    <span
                      key={i}
                      style={{
                        background: "#222",
                        padding: "6px 12px",
                        borderRadius: 6,
                        ...F,
                        fontSize: 12,
                      }}
                    >
                      {k}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ReviewResume;
