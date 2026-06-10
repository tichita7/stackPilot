import React, { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AiToolsData } from "../assets/assets";
import { useUser } from "@clerk/clerk-react";
import NavLogo from "../components/NavLogo";

import CustomUserMenu from "../components/CustomUserMenu";

const FAQItem = ({ q, a, BG, INK, INK2, BORDER, ACCENT, F }) => {
  const [open, setOpen] = useState(false);
  return (
    <div
      style={{
        background: BG,
        borderBottom: `0.5px solid ${BORDER}`,
        cursor: "pointer",
      }}
      onClick={() => setOpen((o) => !o)}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "20px 24px",
        }}
      >
        <span
          style={{
            fontFamily: "'Syne', sans-serif",
            fontSize: 14,
            fontWeight: 700,
            color: open ? ACCENT : INK,
            transition: "color 0.2s",
          }}
        >
          {q}
        </span>
        <svg
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke={open ? ACCENT : INK2}
          strokeWidth="2.5"
          style={{
            transform: open ? "rotate(180deg)" : "rotate(0deg)",
            transition: "transform 0.2s",
            flexShrink: 0,
          }}
        >
          <path d="M6 9l6 6 6-6" />
        </svg>
      </div>
      {open && (
        <div
          style={{
            ...F,
            fontSize: 13,
            color: INK2,
            lineHeight: 1.7,
            padding: "0 24px 20px",
          }}
        >
          {a}
        </div>
      )}
    </div>
  );
};

const Home = () => {
  const navigate = useNavigate();
  const { user } = useUser();
  const toolsRef = useRef(null);
  const terminalRef = useRef(null);
  const heroRef = useRef(null);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const [hoveredTool, setHoveredTool] = useState(null);
  const [typedText, setTypedText] = useState("");
  const [terminalActive, setTerminalActive] = useState(false);
  const [visibleStats, setVisibleStats] = useState(false);
  const statsRef = useRef(null);

  const handleGetStarted = () => {
    if (user) navigate("/ai");
    else navigate("/sign-up");
  };

  // Mouse parallax
  useEffect(() => {
    document.title = "StackPilot - Home";

    const handleMouse = (e) => {
      setMousePos({
        x: e.clientX / window.innerWidth - 0.5,
        y: e.clientY / window.innerHeight - 0.5,
      });
    };
    window.addEventListener("mousemove", handleMouse);
    return () => window.removeEventListener("mousemove", handleMouse);
  }, []);

  // Typing effect for hero subtitle
  const fullText =
    "Debug errors, explain code, analyze repositories, and check your resume score — all from one AI workspace.";
  useEffect(() => {
    let i = 0;
    const iv = setInterval(() => {
      setTypedText(fullText.slice(0, i));
      i++;
      if (i > fullText.length) clearInterval(iv);
    }, 18);
    return () => clearInterval(iv);
  }, []);

  // Terminal stagger animation
  useEffect(() => {
    setTimeout(() => setTerminalActive(true), 400);
  }, []);

  // Stats counter animation on scroll
  useEffect(() => {
    const obs = new IntersectionObserver(
      ([e]) => {
        if (e.isIntersecting) setVisibleStats(true);
      },
      { threshold: 0.3 },
    );
    if (statsRef.current) obs.observe(statsRef.current);
    return () => obs.disconnect();
  }, []);

  const F = { fontFamily: "'DM Mono', monospace" };
  const BG = "#252523";
  const INK = "#efefdc";
  const INK2 = "#c4ccc9";
  const BORDER = "#bbb199";
  const ACCENT = "#634ca8";

  const TOOLS_DISPLAY = [
    {
      num: "01",
      tool: "repository-copilot",
      desc: "understand any codebase",
      color: "#6d7bf1",
      path: "/ai/repository-copilot",
    },
    {
      num: "02",
      tool: "debug-assistant",
      desc: "root cause analysis",
      color: "#ff5f57",
      path: "/ai/debug-assistant",
    },
    {
      num: "03",
      tool: "code-explain",
      desc: "line-by-line breakdown",
      color: "#d86ce6",
      path: "/ai/code-explain",
    },
    {
      num: "04",
      tool: "review-resume",
      desc: "ATS score & feedback",
      color: "#eab308",
      path: "/ai/review-resume",
    },
  ];

  return (
    <div
      style={{
        fontFamily: "'Syne', sans-serif",
        background: BG,
        minHeight: "100vh",
        color: INK,
        position: "static",
      }}
    >
      <link
        href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@300;400;500&display=swap"
        rel="stylesheet"
      />

      <style>{`
        * { box-sizing: border-box; }
        .nav-btn { transition: color 0.2s, background 0.2s; }
        .nav-btn:hover { color: ${ACCENT} !important; }
        .btn-accent { transition: all 0.2s; }
        .btn-accent:hover { background: #5a28e4 !important; transform: translateY(-1px); box-shadow: 0 4px 16px rgba(55, 42, 232, 0.35) !important; }
        .btn-accent:active { transform: translateY(0) scale(0.97); }
        .btn-outline { transition: all 0.2s; }
        .btn-outline:hover { background: ${ACCENT} !important; color: white !important; border-color: ${ACCENT} !important; transform: translateY(-1px); }
        .btn-outline:active { transform: translateY(0) scale(0.97); }
        .btn-ghost { transition: all 0.2s; }
        .btn-ghost:hover { background: ${ACCENT} !important; color: white !important; border-color: ${ACCENT} !important; }
        .t-line { transition: background 0.15s, padding-left 0.2s; cursor: pointer; }
        .t-line:hover { background: rgba(255,255,255,0.04) !important; padding-left: 22px !important; }
        .t-line:hover .t-tool-name { letter-spacing: 0.03em; }
        .t-tool-name { transition: letter-spacing 0.2s; }
        .stat-card { transition: transform 0.2s, box-shadow 0.2s; }
        .stat-card:hover { transform: translateY(-3px); box-shadow: 0 8px 20px rgba(26,26,24,0.1) !important; }
        @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }
        @keyframes pulse-dot { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.4;transform:scale(0.7)} }
        @keyframes scanline { 0%{top:-60px} 100%{top:110%} }
        @keyframes fadeSlideIn { from{opacity:0;transform:translateX(-10px)} to{opacity:1;transform:translateX(0)} }
        @keyframes countUp { from{opacity:0;transform:translateY(10px)} to{opacity:1;transform:translateY(0)} }
        @keyframes borderGlow { 0%,100%{border-color:#2a2a2a} 50%{border-color:#3a3a3a} }
        .cursor { animation: blink 1s infinite; }
        .live-dot { animation: pulse-dot 2s infinite; }
        .scanline { animation: scanline 5s linear infinite; }
        .t-line-anim { animation: fadeSlideIn 0.4s ease both; }
        .stat-num-anim { animation: countUp 0.5s ease both; }
        .hero-terminal { animation: borderGlow 4s ease infinite; }
        .hero-parallax { transition: transform 0.1s ease-out; }
      `}</style>

      {/* NAV */}
      <nav
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0 40px",
          height: 52,
          borderBottom: `0.5px solid ${BORDER}`,
          background: `${BG}f0`,
          position: "sticky",
          top: 0,
          zIndex: 100,
          backdropFilter: "blur(12px)",
        }}
      >
        <NavLogo />

        <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
          {[
            {
              label: "Tools",
              action: () =>
                toolsRef.current?.scrollIntoView({ behavior: "smooth" }),
            },
            {
              label: "Why StackPilot",
              action: () =>
                document
                  .getElementById("why")
                  ?.scrollIntoView({ behavior: "smooth" }),
            },
            {
              label: "FAQs",
              action: () =>
                document
                  .getElementById("faqs")
                  ?.scrollIntoView({ behavior: "smooth" }),
            },
          ].map(({ label, action }) => (
            <button
              key={label}
              className="nav-btn"
              onClick={action}
              style={{
                ...F,
                fontSize: 12,
                color: INK2,
                background: "none",
                border: "none",
                cursor: "pointer",
                padding: "4px 12px",
                borderRadius: 6,
              }}
            >
              {label}
            </button>
          ))}
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          {user ? (
            <>
              <button
                className="btn-accent mb-1"
                onClick={() => navigate("/ai")}
                style={{
                  fontFamily: "Syne",
                  fontSize: 12,
                  fontWeight: 700,
                  padding: "7px 16px",
                  borderRadius: 100,
                  background: ACCENT,
                  color: "white",
                  border: "none",
                  cursor: "pointer",
                }}
              >
                Open Dashboard →
              </button>
              <CustomUserMenu user={user} />
            </>
          ) : (
            <>
              <button
                className="btn-ghost"
                onClick={() => navigate("/sign-in")}
                style={{
                  fontFamily: "Syne",
                  fontSize: 12,
                  fontWeight: 600,
                  padding: "7px 16px",
                  borderRadius: 100,
                  background: "transparent",
                  color: INK,
                  border: `1px solid ${BORDER}`,
                  cursor: "pointer",
                }}
              >
                Sign in
              </button>
              <button
                className="btn-accent"
                onClick={handleGetStarted}
                style={{
                  fontFamily: "Syne",
                  fontSize: 12,
                  fontWeight: 700,
                  padding: "7px 16px",
                  borderRadius: 100,
                  background: INK,
                  color: BG,
                  border: "none",
                  cursor: "pointer",
                }}
              >
                Get started →
              </button>
            </>
          )}
        </div>
      </nav>

      {/* HERO */}
      <section
        ref={heroRef}
        style={{
          padding: "64px 40px 48px",
          display: "grid",
          gridTemplateColumns: "1fr 420px",
          gap: 52,
          alignItems: "center",
          maxWidth: 1200,
          margin: "0 auto",
        }}
      >
        {/* Left copy */}
        <div
          style={{
            transform: `translate(${mousePos.x * -8}px, ${mousePos.y * -4}px)`,
            transition: "transform 0.15s ease-out",
          }}
        >
          <div
            style={{
              ...F,
              fontSize: 11,
              color: INK2,
              letterSpacing: "0.1em",
              textTransform: "uppercase",
              marginBottom: 20,
              display: "flex",
              alignItems: "center",
              gap: 8,
            }}
          >
            <span
              style={{
                width: 24,
                height: 1,
                background: ACCENT,
                display: "inline-block",
              }}
            />
            <span style={{ color: ACCENT }}>AI Developer Copilot</span>
          </div>
          <h1
            style={{
              fontSize: "clamp(48px, 6vw, 80px)",
              fontWeight: 800,
              lineHeight: 0.95,
              letterSpacing: "-3px",
              marginBottom: 28,
            }}
          >
            Your AI
            <br />
            copilot codes
            <br />
            <span style={{ color: ACCENT, position: "relative" }}>
              inside
              <span
                style={{
                  position: "absolute",
                  bottom: -2,
                  left: 0,
                  right: 0,
                  height: 3,
                  background: ACCENT,
                  borderRadius: 2,
                  opacity: 0.3,
                }}
              />
            </span>
            <br />
            your stack.
          </h1>
          <p
            style={{
              ...F,
              fontSize: 13,
              color: INK2,
              lineHeight: 1.8,
              maxWidth: 440,
              marginBottom: 16,
              minHeight: 20,
            }}
          >
            {typedText}
            <span className="cursor" style={{ color: ACCENT }}>
              |
            </span>
          </p>
          <div
            style={{
              display: "flex",
              gap: 12,
              marginBottom: 20,
              flexWrap: "wrap",
            }}
          >
            <button
              className="btn-accent"
              onClick={handleGetStarted}
              style={{
                fontFamily: "Syne",
                fontSize: 14,
                fontWeight: 700,
                padding: "13px 28px",
                borderRadius: 100,
                background: ACCENT,
                color: "white",
                border: "none",
                cursor: "pointer",
              }}
            >
              {user ? "Open Dashboard →" : "Start free →"}
            </button>
            {!user && (
              <button
                className="btn-outline"
                onClick={() => navigate("/sign-in")}
                style={{
                  fontFamily: "Syne",
                  fontSize: 14,
                  fontWeight: 700,
                  padding: "13px 28px",
                  borderRadius: 100,
                  background: "transparent",
                  color: INK,
                  border: `1.5px solid ${INK}`,
                  cursor: "pointer",
                }}
              >
                Sign in
              </button>
            )}
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            <p style={{ ...F, fontSize: 11, color: INK2, margin: 0 }}>
              No credit card required.
            </p>
            <div style={{ display: "flex", gap: 6 }}>
              {["Groq", "Clerk", "FastAPI"].map((t) => (
                <span
                  key={t}
                  style={{
                    ...F,
                    fontSize: 10,
                    padding: "2px 8px",
                    borderRadius: 100,
                    border: `0.5px solid ${BORDER}`,
                    color: "black",
                    background: INK2,
                  }}
                >
                  {t}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Terminal */}
        <div
          className="hero-terminal"
          ref={terminalRef}
          style={{
            transform: `translate(${mousePos.x * 10}px, ${mousePos.y * 6}px)`,
            transition: "transform 0.15s ease-out",
            background: "#0e0e0e",
            borderRadius: 16,
            overflow: "hidden",
            border: "1px solid #2a2a2a",
            boxShadow:
              "0 32px 64px rgba(0,0,0,0.4), 0 0 0 0.5px rgba(255,255,255,0.05)",
            position: "relative",
          }}
        >
          {/* Scanline */}
          <div
            className="scanline"
            style={{
              position: "absolute",
              left: 0,
              right: 0,
              height: 60,
              background:
                "linear-gradient(transparent, rgba(255,255,255,0.018), transparent)",
              pointerEvents: "none",
              zIndex: 2,
            }}
          />

          {/* Header */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "13px 18px",
              borderBottom: "1px solid #1a1a1a",
              background: "#141414",
            }}
          >
            <div style={{ display: "flex", gap: 7 }}>
              {[
                ["#ff5f57", "0 0 8px #ff5f5780"],
                ["#febc2e", "0 0 8px #febc2e80"],
                ["#28c840", "0 0 8px #28c84080"],
              ].map(([c, s]) => (
                <div
                  key={c}
                  style={{
                    width: 11,
                    height: 11,
                    borderRadius: "50%",
                    background: c,
                    boxShadow: s,
                  }}
                />
              ))}
            </div>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 6,
                background: "#1e1e1e",
                padding: "3px 12px",
                borderRadius: 100,
              }}
            >
              <div
                className="live-dot"
                style={{
                  width: 5,
                  height: 5,
                  borderRadius: "50%",
                  background: "#4ade80",
                }}
              />
              <span style={{ ...F, fontSize: 10, color: "#666" }}>
                stackpilot://copilot
              </span>
            </div>
            <span style={{ ...F, fontSize: 10, color: "#4ade80" }}>LIVE</span>
          </div>

          {/* Prompt */}
          <div
            style={{
              padding: "12px 18px 10px",
              borderBottom: "0.5px solid #1a1a1a",
              background: "#111",
            }}
          >
            <div
              style={{
                ...F,
                fontSize: 11,
                display: "flex",
                alignItems: "center",
                gap: 6,
                flexWrap: "wrap",
              }}
            >
              <span style={{ color: "#4ade80" }}>➜</span>
              <span style={{ color: "#818cf8" }}>~/stackpilot</span>
              <span style={{ color: "#555" }}>on</span>
              <span style={{ color: "#f97316" }}>⎇ main</span>
              <span style={{ color: "#888" }}>./run</span>
              <span style={{ color: "#e0e0e0" }}>--tools</span>
              <span style={{ color: "#4ade80" }}>--ai</span>
              <span className="cursor" style={{ color: "#4ade80" }}>
                ▊
              </span>
            </div>
          </div>

          {/* Output header */}
          <div style={{ padding: "10px 18px 6px", background: "#111" }}>
            <span
              style={{
                ...F,
                fontSize: 10,
                color: "#333",
                letterSpacing: "0.08em",
              }}
            >
              // LOADED 4 DEVELOPER TOOLS
            </span>
          </div>

          {/* Tools */}
          <div style={{ background: "#0e0e0e" }}>
            {TOOLS_DISPLAY.map(({ num, tool, desc, color, path }, i) => (
              <div
                key={num}
                className="t-line t-line-anim"
                style={{
                  display: "flex",
                  gap: 14,
                  padding: "10px 18px",
                  borderBottom: "0.5px solid #151515",
                  animationDelay: terminalActive ? `${i * 120}ms` : "999s",
                  opacity: terminalActive ? 1 : 0,
                }}
                onClick={() => (user ? navigate(path) : navigate("/sign-up"))}
              >
                <span
                  style={{
                    ...F,
                    fontSize: 10,
                    color: "#2a2a2a",
                    minWidth: 20,
                    paddingTop: 1,
                  }}
                >
                  {num}
                </span>
                <span
                  className="t-tool-name"
                  style={{
                    ...F,
                    fontSize: 12,
                    color,
                    minWidth: 150,
                    fontWeight: 500,
                  }}
                >
                  {tool}
                </span>
                <span style={{ ...F, fontSize: 11, color: "#c9d74a" }}>
                  — {desc}
                </span>
              </div>
            ))}
          </div>

          {/* Status bar */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "10px 18px",
              background: "#141414",
              borderTop: "1px solid #1a1a1a",
            }}
          >
            <div style={{ display: "flex", gap: 16 }}>
              {[
                ["LLaMA 3.3", "#4ade80"],
                ["70B", "#f97316"],
                ["Groq", "#818cf8"],
              ].map(([label, color]) => (
                <span
                  key={label}
                  style={{
                    ...F,
                    fontSize: 10,
                    color,
                    display: "flex",
                    alignItems: "center",
                    gap: 4,
                  }}
                >
                  <span
                    style={{
                      width: 4,
                      height: 4,
                      borderRadius: "50%",
                      background: color,
                      display: "inline-block",
                    }}
                  />
                  {label}
                </span>
              ))}
            </div>
            <span style={{ ...F, fontSize: 10, color: "#2a2a2a" }}>
              exit: 0
            </span>
          </div>
        </div>
      </section>

      {/* STATS */}
      <div
        ref={statsRef}
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(4,1fr)",
          gap: 1,
          background: BORDER,
          border: `1px solid ${BORDER}`,
          borderRadius: 12,
          overflow: "hidden",
          maxWidth: 1120,
          margin: "0 auto",
        }}
      >
        {[
          ["4", "AI tools"],
          ["<1s", "avg response"],
          ["70B", "model params"],
          ["100%", "dev-focused"],
        ].map(([num, label], i) => (
          <div
            key={label}
            className="stat-card stat-num-anim"
            style={{
              background: BG,
              padding: "24px 20px",
              animationDelay: visibleStats ? `${i * 80}ms` : "999s",
              cursor: "default",
            }}
          >
            <div
              style={{
                fontSize: 36,
                fontWeight: 800,
                letterSpacing: "-2px",
                color: INK,
                marginBottom: 4,
                transition: "color 0.2s",
              }}
              onMouseEnter={(e) => (e.currentTarget.style.color = ACCENT)}
              onMouseLeave={(e) => (e.currentTarget.style.color = INK)}
            >
              {num}
            </div>
            <div
              style={{
                ...F,
                fontSize: 10,
                color: INK2,
                textTransform: "uppercase",
                letterSpacing: "0.06em",
              }}
            >
              {label}
            </div>
          </div>
        ))}
      </div>

      {/* TOOLS */}
      <section
        ref={toolsRef}
        style={{ padding: "64px 40px", maxWidth: 1200, margin: "0 auto" }}
      >
        <div
          style={{
            ...F,
            fontSize: 10,
            color: INK2,
            letterSpacing: "0.1em",
            textTransform: "uppercase",
            marginBottom: 14,
            display: "flex",
            alignItems: "center",
            gap: 10,
          }}
        >
          <span
            style={{
              width: 20,
              height: 1,
              background: ACCENT,
              display: "inline-block",
            }}
          />
          <span style={{ color: ACCENT }}>What's inside</span>
        </div>
        <h2
          style={{
            fontSize: 32,
            fontWeight: 800,
            letterSpacing: "-1px",
            marginBottom: 8,
            color: INK,
          }}
        >
          Every tool a developer needs.
        </h2>
        <p style={{ ...F, fontSize: 12, color: INK2, marginBottom: 36 }}>
          Click any tool to jump straight in.
        </p>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(2,1fr)",
            gap: 1,
            background: BORDER,
            border: `1px solid ${BORDER}`,
            borderRadius: 14,
            overflow: "hidden",
          }}
        >
          {AiToolsData.map((tool, i) => {
            const isHovered = hoveredTool === i;

            return (
              <div
                key={tool.path}
                onClick={() =>
                  user ? navigate(tool.path) : navigate("/sign-up")
                }
                onMouseEnter={() => setHoveredTool(i)}
                onMouseLeave={() => setHoveredTool(null)}
                style={{
                  background: isHovered ? "#262728" : BG,
                  padding: "30px 26px",
                  cursor: "pointer",
                  position: "relative",
                  overflow: "hidden",
                  transform: isHovered ? "translateY(-6px)" : "translateY(0)",
                  boxShadow: isHovered
                    ? `0 12px 32px ${tool.bg.from}30`
                    : "none",
                  border: `1px solid ${isHovered ? `${tool.bg.from}40` : "transparent"}`,
                  transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
                }}
              >
                {/* Accent line on hover */}
                <div
                  style={{
                    position: "absolute",
                    top: 0,
                    left: 0,
                    right: 0,
                    height: 3,
                    background: `linear-gradient(90deg, ${tool.bg.from}, ${tool.bg.to})`,
                    transform: isHovered ? "scaleX(1)" : "scaleX(0)",
                    transformOrigin: "left",
                    transition: "transform 0.4s cubic-bezier(0.4, 0, 0.2, 1)",
                  }}
                />

                <div
                  style={{
                    width: 46,
                    height: 46,
                    borderRadius: 12,
                    background: `linear-gradient(135deg, ${tool.bg.from}, ${tool.bg.to})`,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    marginBottom: 18,
                    boxShadow: isHovered ? "gray" : "none",
                    transform: isHovered ? "white" : "scale(1) rotate(0deg)",
                    transition:
                      "transform 0.4s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.3s ease",
                  }}
                >
                  <tool.Icon
                    style={{ width: 22, height: 22, color: "white" }}
                  />
                </div>

                <div
                  style={{
                    fontSize: 18,
                    fontWeight: 800,
                    color: isHovered ? "white" : "#ffffff",
                    marginBottom: 8,
                    transition: "color 0.3s ease",
                  }}
                >
                  {tool.title}
                </div>
                <div
                  style={{
                    ...F,
                    fontSize: 13,
                    color: isHovered ? "#f2ecec" : "#f3f3ef",
                    lineHeight: 1.65,
                    marginBottom: 20,
                    transition: "color 0.3s ease",
                  }}
                >
                  {tool.description}
                </div>

                <div
                  style={{
                    fontSize: 13,
                    fontWeight: 700,
                    ...F,
                    display: "inline-block",
                    color: isHovered ? ACCENT : INK2,
                    letterSpacing: isHovered ? "0.5px" : "0",
                    transform: isHovered ? "translateX(4px)" : "translateX(0)",
                    transition: "all 0.3s ease",
                  }}
                >
                  → Open tool
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Why StackPilot */}
      <section
        id="why"
        style={{
          padding: "60px 40px",
          borderTop: `0.5px solid ${BORDER}`,
          maxWidth: 1200,
          margin: "0 auto",
        }}
      >
        <div
          style={{
            ...F,
            fontSize: 10,
            color: ACCENT,
            letterSpacing: "0.1em",
            textTransform: "uppercase",
            marginBottom: 14,
            display: "flex",
            alignItems: "center",
            gap: 10,
          }}
        >
          <span
            style={{
              width: 20,
              height: 1,
              background: ACCENT,
              display: "inline-block",
            }}
          />
          Why StackPilot
        </div>
        <h2
          style={{
            fontSize: 32,
            fontWeight: 800,
            letterSpacing: "-1px",
            marginBottom: 6,
            color: INK,
          }}
        >
          Built different.
        </h2>
        <p style={{ ...F, fontSize: 12, color: INK2, marginBottom: 40 }}>
          No bloat. No subscriptions. Just tools that work.
        </p>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(3, 1fr)",
            gap: 1,
            background: BORDER,
            border: `1px solid ${BORDER}`,
            borderRadius: 14,
            overflow: "hidden",
            marginBottom: 64,
          }}
        >
          {[
            {
              tag: "01 — Speed",
              title: "Under 1s responses.",
              desc: "Powered by Groq's LPU inference engine. LLaMA 3.3 70B running faster than any GPU cluster you've seen.",
            },
            {
              tag: "02 — Focus",
              title: "Dev-only tooling.",
              desc: "No generic AI chat. Every tool is scoped to a real developer workflow — debug, explain, review, analyze.",
            },
            {
              tag: "03 — Privacy",
              title: "Nothing is stored.",
              desc: "Your code and resume are never persisted on our servers. Each session is stateless and ephemeral.",
            },
          ].map(({ tag, title, desc }) => (
            <div
              key={tag}
              style={{
                background: BG,
                padding: "28px 24px",
              }}
            >
              <div
                style={{
                  ...F,
                  fontSize: 10,
                  color: ACCENT,
                  letterSpacing: "0.08em",
                  textTransform: "uppercase",
                  marginBottom: 12,
                }}
              >
                {tag}
              </div>
              <div
                style={{
                  fontSize: 18,
                  fontWeight: 800,
                  color: INK,
                  marginBottom: 10,
                  letterSpacing: "-0.5px",
                }}
              >
                {title}
              </div>
              <div style={{ ...F, fontSize: 12, color: INK2, lineHeight: 1.7 }}>
                {desc}
              </div>
            </div>
          ))}
        </div>

        {/* FAQ */}
        <div
          id="faqs"
          style={{
            ...F,
            fontSize: 10,
            color: ACCENT,
            letterSpacing: "0.1em",
            textTransform: "uppercase",
            marginBottom: 14,
            display: "flex",
            alignItems: "center",
            gap: 10,
          }}
        >
          <span
            style={{
              width: 20,
              height: 1,
              background: ACCENT,
              display: "inline-block",
            }}
          />
          FAQ
        </div>
        <h2
          style={{
            fontSize: 32,
            fontWeight: 800,
            letterSpacing: "-1px",
            marginBottom: 40,
            color: INK,
          }}
        >
          Common questions.
        </h2>

        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: 1,
            background: BORDER,
            border: `1px solid ${BORDER}`,
            borderRadius: 14,
            overflow: "hidden",
          }}
        >
          {[
            {
              q: "Is StackPilot free to use?",
              a: "Yes. Sign up and get access to all tools immediately — no credit card required.",
            },
            {
              q: "What AI model does it use?",
              a: "LLaMA 3.3 70B served via Groq's LPU inference. It's one of the fastest and most capable open models available.",
            },
            {
              q: "Do I need my own API key?",
              a: "No. StackPilot handles all API calls on the backend. Just sign in and use the tools.",
            },
            {
              q: "Is my code or resume stored anywhere?",
              a: "No. Inputs are sent directly to the model and discarded. Nothing is saved to a database.",
            },
            {
              q: "Which tools are available right now?",
              a: "Repository Copilot, Debug Assistant, Code Explain, and Resume Reviewer — with more coming soon.",
            },
          ].map(({ q, a }) => (
            <FAQItem
              key={q}
              q={q}
              a={a}
              BG={BG}
              INK={INK}
              INK2={INK2}
              BORDER={BORDER}
              ACCENT={ACCENT}
              F={F}
            />
          ))}
        </div>
      </section>

      {/* FOOTER */}
      <footer
        style={{
          padding: "28px 40px",
          borderTop: `0.5px solid ${BORDER}`,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <NavLogo />
        <div style={{ ...F, fontSize: 10, color: INK2 }}>
          React · FastAPI · Groq · Clerk
        </div>
        <div style={{ ...F, fontSize: 10, color: INK2 }}>©2026 StackPilot</div>
      </footer>
    </div>
  );
};

export default Home;
