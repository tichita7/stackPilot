import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useUser } from "@clerk/clerk-react";
import NavLogo from "../components/NavLogo";

import CustomUserMenu from "../components/CustomUserMenu";

const Dashboard = () => {
  const navigate = useNavigate();
  const { user } = useUser();
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    document.title = "StackPilot - Dashboard";
    if (!user) return;

    fetch(`http://localhost:8000/api/dashboard-analytics/${user.id}`)
      .then((res) => {
        if (!res.ok)
          throw new Error(`Backend telemetry engine failure: ${res.status}`);
        return res.json();
      })
      .then((data) => {
        if (data && data.metrics) {
          setAnalytics(data);
        } else {
          throw new Error("Telemetry validation structural mismatch.");
        }
        setLoading(false);
      })
      .catch((err) => {
        console.error("Telemetry pipeline execution error:", err);
        setLoading(false);
      });
  }, [user]);

  const F = { fontFamily: "'DM Mono', monospace" };
  const BG = "#252523";
  const PANEL_BG = "#1c1c1a";
  const INK = "#efefdc";
  const INK2 = "#c4ccc9";
  const BORDER = "#2a2a28";
  const ACCENT = "#0b880d";
  const TECH_BLUE = "#395aa6";

  if (loading || !analytics) {
    return (
      <div
        style={{
          background: BG,
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: ACCENT,
          ...F,
        }}
      >
        LOADING TELEMETRY CORE CONTROL ENGINE...
      </div>
    );
  }

  return (
    <div
      style={{
        fontFamily: "'Syne', sans-serif",
        background: BG,
        minHeight: "100vh",
        height: "100vh",
        overflowY: "auto",
        overflowX: "hidden",
        color: "#ffffff",
        padding: "0 24px 40px",
      }}
    >
      <nav
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          height: 64,
          borderBottom: `1px solid ${BORDER}`,
          marginBottom: 32,
        }}
      >
        <NavLogo />

        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          {[
            { n: "Repository CoPilot", p: "/ai/repository-copilot" },
            { n: "Debug Assistant", p: "/ai/debug-assistant" },
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
          {/* <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              ...F,
              fontSize: 12,
              color: "#4ade80",
            }}
          >
            <span
              style={{
                width: 6,
                height: 6,
                background: "#4ade80",
                borderRadius: "50%",
              }}
            />
            {analytics.metrics.streak_count}
          </div> */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 12,
              borderLeft: `1px solid ${BORDER}`,
              paddingLeft: 20,
            }}
          >
            <div style={{ textAlign: "right" }}>
              <div style={{ fontSize: 13, fontWeight: 700 }}>
                {user?.fullName || "Alex Rivera"}
              </div>
              <div
                style={{
                  ...F,
                  fontSize: 9,
                  color: "#00ff66",
                  background: "rgba(0,255,102,0.1)",
                  padding: "1px 6px",
                  borderRadius: 4,
                  display: "inline-block",
                  marginTop: 2,
                }}
              >
                DEVELOPER PRO
              </div>
            </div>
            <CustomUserMenu user={user} />
          </div>
        </div>
      </nav>

      <div style={{ maxWidth: 1400, margin: "0 auto" }}>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            marginBottom: 28,
          }}
        >
          <div>
            <h1
              style={{
                fontSize: 32,
                fontWeight: 800,
                letterSpacing: "-1px",
                margin: -2,
                color: TECH_BLUE,
              }}
            >
              Workspace Velocity
            </h1>
            <p style={{ color: INK, fontSize: 14, margin: "4px 0 0 0" }}>
              Real-time telemetry and resource utilization tracking for
              workspace cluster.
            </p>
          </div>
          <div
            style={{
              ...F,
              fontSize: 11,
              color: "#4ade80",
              background: "rgba(74,222,128,0.06)",
              border: "1px solid rgba(74,222,128,0.2)",
              padding: "6px 14px",
              borderRadius: 100,
            }}
          >
            ● SYSTEM NOMINAL
          </div>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 360px",
            gap: 24,
            alignItems: "start",
          }}
        >
          <div
            style={{
              background: PANEL_BG,
              borderRadius: 12,
              border: `1px solid ${BORDER}`,
              padding: 24,
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                marginBottom: 32,
              }}
            >
              <div>
                <h3 style={{ fontSize: 18, fontWeight: 700, margin: 0 }}>
                  Weekly Workspace Velocity
                </h3>
                <span style={{ ...F, fontSize: 11, color: INK2 }}>
                  Resource consumption across tool stack (7-day window)
                </span>
              </div>
              <div
                style={{
                  ...F,
                  fontSize: 10,
                  color: INK,
                  background: "#222",
                  padding: "4px 8px",
                  borderRadius: 4,
                  border: `1px solid ${BORDER}`,
                }}
              >
                AUTO-REFRESH: 60S
              </div>
            </div>

            <div
              style={{
                height: 220,
                display: "flex",
                alignItems: "flex-end",
                justifyContent: "space-between",
                padding: "0 20px",
                borderBottom: `1px solid ${BORDER}`,
                marginBottom: 16,
              }}
            >
              {analytics.time_series_7d.map((dayData, idx) => {
                // Backend now sends { day, total } — single total count per day
                const totalRuns = dayData.total || 0;
                const maxRuns = Math.max(
                  ...analytics.time_series_7d.map((d) => d.total || 0),
                  1,
                );
                // Scale bar height: min 8px baseline, max 180px
                const calculatedHeight =
                  totalRuns > 0 ? Math.max((totalRuns / maxRuns) * 180, 18) : 8;

                return (
                  <div
                    key={idx}
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      alignItems: "center",
                      width: "10%",
                      gap: 8,
                    }}
                  >
                    <div
                      style={{
                        width: "100%",
                        height: calculatedHeight,
                        background: totalRuns > 0 ? TECH_BLUE : "#222220",
                        borderRadius: "4px 4px 0 0",
                        position: "relative",
                        transition: "all 0.3s ease",
                      }}
                    >
                      {totalRuns > 0 && (
                        <div
                          style={{
                            position: "absolute",
                            top: -22,
                            left: "50%",
                            transform: "translateX(-50%)",
                            ...F,
                            fontSize: 10,
                            color: TECH_BLUE,
                          }}
                        >
                          {totalRuns}
                        </div>
                      )}
                    </div>
                    <span
                      style={{ ...F, fontSize: 11, color: INK2, marginTop: 8 }}
                    >
                      {dayData.day}
                    </span>
                  </div>
                );
              })}
            </div>

            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                marginTop: 24,
                paddingTop: 16,
                borderTop: `1px solid #222`,
              }}
            >
              <div style={{ display: "flex", gap: 32 }}>
                <div>
                  <div
                    style={{
                      ...F,
                      fontSize: 10,
                      color: INK2,
                      textTransform: "uppercase",
                    }}
                  >
                    Avg Execution Latency
                  </div>
                  <div
                    style={{
                      fontSize: 16,
                      fontWeight: 700,
                      color: "#4ade80",
                      marginTop: 2,
                    }}
                  >
                    840ms
                  </div>
                </div>
                <div>
                  <div
                    style={{
                      ...F,
                      fontSize: 10,
                      color: INK2,
                      textTransform: "uppercase",
                    }}
                  >
                    Optimization Yield
                  </div>
                  <div
                    style={{
                      fontSize: 16,
                      fontWeight: 700,
                      color: TECH_BLUE,
                      marginTop: 2,
                    }}
                  >
                    94.6%
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
            <div
              style={{
                background: PANEL_BG,
                borderRadius: 12,
                border: `1px solid ${BORDER}`,
                padding: 20,
              }}
            >
              <div
                style={{
                  ...F,
                  fontSize: 10,
                  color: INK2,
                  textTransform: "uppercase",
                  letterSpacing: "0.05em",
                }}
              >
                Favorite Assistant
              </div>
              <div
                style={{
                  fontSize: 20,
                  fontWeight: 800,
                  color: "#ffffff",
                  marginTop: 8,
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                }}
              >
                <div
                  style={{
                    width: 8,
                    height: 8,
                    background: TECH_BLUE,
                    borderRadius: "50%",
                  }}
                />
                {analytics.metrics.favorite_assistant.split(" (")[0]}
              </div>
              <div style={{ ...F, fontSize: 12, color: INK, marginTop: 4 }}>
                Responsible for dominant query volume.
              </div>
            </div>

            <div
              style={{
                background: PANEL_BG,
                borderRadius: 12,
                border: `1px solid ${BORDER}`,
                padding: 20,
              }}
            >
              <div
                style={{
                  ...F,
                  fontSize: 10,
                  color: INK2,
                  textTransform: "uppercase",
                }}
              >
                Workspace Momentum
              </div>
              <div
                style={{
                  fontSize: 28,
                  fontWeight: 800,
                  color: "#00ff66",
                  marginTop: 4,
                  letterSpacing: "-1px",
                }}
              >
                {analytics.metrics.workspace_momentum.split(" ")[0]}
              </div>
              <div style={{ fontSize: 12, color: INK, marginTop: 2 }}>
                Efficiency increase across nodes vs previous cycle.
              </div>
            </div>

            <div
              style={{
                background: PANEL_BG,
                borderRadius: 12,
                border: `1px solid ${BORDER}`,
                padding: 20,
              }}
            >
              <div
                style={{
                  ...F,
                  fontSize: 10,
                  color: INK2,
                  textTransform: "uppercase",
                  marginBottom: 14,
                  letterSpacing: "0.05em",
                }}
              >
                Recent Telemetry
              </div>
              <div
                style={{ display: "flex", flexDirection: "column", gap: 12 }}
              >
                {analytics.telemetry_stream.map((log, idx) => (
                  <div
                    key={idx}
                    style={{
                      background: "#131312",
                      border: `1px solid #222`,
                      borderRadius: 8,
                      padding: "10px 12px",
                    }}
                  >
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                        marginBottom: 6,
                      }}
                    >
                      <span
                        style={{
                          ...F,
                          fontSize: 11,
                          fontWeight: 700,
                          color: TECH_BLUE,
                          textTransform: "uppercase",
                        }}
                      >
                        {log.tool.replace("-", " ")}
                      </span>
                      <span style={{ ...F, fontSize: 9, color: INK2 }}>
                        {new Date(log.created_at).toLocaleTimeString("en-IN", {
                          hour: "2-digit",
                          minute: "2-digit",
                          second: "2-digit",
                          timeZone: "Asia/Kolkata",
                        })}
                      </span>
                    </div>
                    <div
                      style={{
                        fontSize: 12,
                        color: "#dddddd",
                        whiteSpace: "nowrap",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                      }}
                    >
                      {log.input_summary ||
                        "Operational payload execution sequence dispatched."}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
