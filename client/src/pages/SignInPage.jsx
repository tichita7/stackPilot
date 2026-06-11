import React, { useState } from "react";
import { useSignIn } from "@clerk/clerk-react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import NavLogo from "../components/NavLogo";

const BG = "#252523";
const PANEL = "#1c1c1a";
const INK = "#F5F2EB";
const INK2 = "#9b9b98";
const BORDER = "#2a2a28";
const ACCENT = "#2a63e8";

const GitHubIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
    <path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
  </svg>
);

const GoogleIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24">
    <path
      fill="#4285F4"
      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
    />
    <path
      fill="#34A853"
      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
    />
    <path
      fill="#FBBC05"
      d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
    />
    <path
      fill="#EA4335"
      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
    />
  </svg>
);

const EyeIcon = ({ open }) => (
  <svg
    width="16"
    height="16"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
  >
    {open ? (
      <>
        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
        <circle cx="12" cy="12" r="3" />
      </>
    ) : (
      <>
        <path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94" />
        <path d="M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19" />
        <line x1="1" y1="1" x2="23" y2="23" />
      </>
    )}
  </svg>
);

const Spinner = () => (
  <svg
    width="14"
    height="14"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2.5"
    style={{ animation: "spin 0.7s linear infinite" }}
  >
    <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
  </svg>
);

const labelStyle = {
  display: "block",
  color: INK2,
  fontSize: 11,
  letterSpacing: "0.08em",
  textTransform: "uppercase",
  marginBottom: 6,
};

const SignInPage = () => {
  const { isLoaded, signIn, setActive } = useSignIn();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [oauthLoading, setOauthLoading] = useState("");
  const navigate = useNavigate();
  const location = useLocation();
  const from = location.state?.from?.pathname || "/ai";

  const handleSignIn = async (e) => {
    e.preventDefault();
    if (!isLoaded) return;
    setError("");
    setLoading(true);
    try {
      const result = await signIn.create({ identifier: email, password });
      if (result.status === "complete") {
        await setActive({ session: result.createdSessionId });
        navigate(from, { replace: true });
      } else {
        setError("Sign-in incomplete. Please try again.");
      }
    } catch (err) {
      setError(
        err?.errors?.[0]?.longMessage ||
          "Invalid credentials. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  };

  // Clerk handles the entire Google/GitHub OAuth flow on its backend.
  // You don't need custom OAuth credentials — Clerk's shared keys do it all.
  const handleOAuth = async (provider) => {
    if (!isLoaded) return;
    setOauthLoading(provider);
    setError("");
    try {
      await signIn.authenticateWithRedirect({
        strategy: `oauth_${provider}`,
        redirectUrl: `https://stack-pilot-agentic.vercel.app/sso-callback`,
        redirectUrlComplete: `https://stack-pilot-agentic.vercel.app/ai`,
      });
    } catch (err) {
      setError(`Could not sign in with ${provider}. Please try again.`);
      setOauthLoading("");
    }
  };

  const inputStyle = {
    width: "100%",
    background: BG,
    border: `1px solid ${BORDER}`,
    borderRadius: 8,
    padding: "11px 14px",
    color: INK,
    fontSize: 14,
    outline: "none",
    boxSizing: "border-box",
    fontFamily: "'DM Mono', monospace",
    transition: "border-color 0.15s",
  };

  const oauthBtnStyle = {
    width: "100%",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: 10,
    background: "#1a1a18",
    border: `1px solid ${BORDER}`,
    borderRadius: 8,
    padding: "11px 0",
    color: INK,
    fontSize: 13,
    fontFamily: "'Syne', sans-serif",
    fontWeight: 600,
    cursor: "pointer",
    transition: "border-color 0.15s, background 0.15s",
  };

  return (
    <div
      style={{
        background: BG,
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: "'DM Mono', monospace",
      }}
    >
      <div
        style={{
          background: PANEL,
          border: `1px solid ${BORDER}`,
          borderRadius: 14,
          padding: "44px 40px",
          width: "100%",
          maxWidth: 420,
        }}
      >
        {/* Logo */}
        <div style={{ textAlign: "center", marginBottom: 32 }}>
          <div
            style={{
              display: "flex",
              justifyContent: "center",
              marginBottom: 6,
            }}
          >
            <NavLogo />
          </div>
          <p
            style={{
              color: INK2,
              fontSize: 13,
              fontFamily: "'Syne', sans-serif",
            }}
          >
            Sign in to your workspace
          </p>
        </div>

        {/* OAuth Buttons */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: 10,
            marginBottom: 24,
          }}
        >
          <button
            onClick={() => handleOAuth("github")}
            disabled={!!oauthLoading}
            style={{
              ...oauthBtnStyle,
              opacity: oauthLoading === "github" ? 0.6 : 1,
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = "#555";
              e.currentTarget.style.background = "#222";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = BORDER;
              e.currentTarget.style.background = "#1a1a18";
            }}
          >
            {oauthLoading === "github" ? <Spinner /> : <GitHubIcon />}
            {oauthLoading === "github"
              ? "Redirecting..."
              : "Continue with GitHub"}
          </button>

          <button
            onClick={() => handleOAuth("google")}
            disabled={!!oauthLoading}
            style={{
              ...oauthBtnStyle,
              opacity: oauthLoading === "google" ? 0.6 : 1,
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = "#555";
              e.currentTarget.style.background = "#222";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = BORDER;
              e.currentTarget.style.background = "#1a1a18";
            }}
          >
            {oauthLoading === "google" ? <Spinner /> : <GoogleIcon />}
            {oauthLoading === "google"
              ? "Redirecting..."
              : "Continue with Google"}
          </button>
        </div>

        {/* Divider */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 12,
            marginBottom: 24,
          }}
        >
          <div style={{ flex: 1, height: 1, background: BORDER }} />
          <span style={{ color: INK2, fontSize: 11, letterSpacing: "0.06em" }}>
            OR
          </span>
          <div style={{ flex: 1, height: 1, background: BORDER }} />
        </div>

        {/* Email + Password Form */}
        <form
          onSubmit={handleSignIn}
          style={{ display: "flex", flexDirection: "column", gap: 14 }}
        >
          <div>
            <label style={labelStyle}>Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@company.com"
              required
              style={inputStyle}
              onFocus={(e) => (e.target.style.borderColor = ACCENT)}
              onBlur={(e) => (e.target.style.borderColor = BORDER)}
            />
          </div>

          <div>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: 6,
              }}
            >
              <label style={{ ...labelStyle, marginBottom: 0 }}>Password</label>
              <Link
                to="/forgot-password"
                style={{
                  color: INK2,
                  fontSize: 11,
                  textDecoration: "none",
                  fontFamily: "'Syne', sans-serif",
                  transition: "color 0.15s",
                }}
                onMouseEnter={(e) => (e.target.style.color = ACCENT)}
                onMouseLeave={(e) => (e.target.style.color = INK2)}
              >
                Forgot password?
              </Link>
            </div>
            <div style={{ position: "relative" }}>
              <input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                style={{ ...inputStyle, paddingRight: 42 }}
                onFocus={(e) => (e.target.style.borderColor = ACCENT)}
                onBlur={(e) => (e.target.style.borderColor = BORDER)}
              />
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                style={{
                  position: "absolute",
                  right: 12,
                  top: "50%",
                  transform: "translateY(-50%)",
                  background: "none",
                  border: "none",
                  color: INK2,
                  cursor: "pointer",
                  padding: 0,
                  display: "flex",
                  alignItems: "center",
                }}
              >
                <EyeIcon open={showPassword} />
              </button>
            </div>
          </div>

          {error && (
            <div
              style={{
                background: "rgba(232,87,42,0.08)",
                border: `1px solid rgba(232,87,42,0.25)`,
                borderRadius: 8,
                padding: "10px 14px",
                color: ACCENT,
                fontSize: 13,
                display: "flex",
                alignItems: "center",
                gap: 8,
              }}
            >
              <span>⚠</span> {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading || !isLoaded}
            style={{
              marginTop: 4,
              background: loading ? "#2a2a28" : ACCENT,
              color: loading ? INK2 : "#fff",
              border: "none",
              borderRadius: 8,
              padding: "13px",
              fontSize: 14,
              fontWeight: 700,
              cursor: loading ? "not-allowed" : "pointer",
              fontFamily: "'Syne', sans-serif",
              letterSpacing: "0.02em",
              transition: "background 0.15s",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: 8,
            }}
          >
            {loading ? (
              <>
                <Spinner /> Signing in...
              </>
            ) : (
              "Unlock Workspace →"
            )}
          </button>
        </form>

        <p
          style={{
            textAlign: "center",
            marginTop: 24,
            color: INK2,
            fontSize: 13,
            fontFamily: "'Syne', sans-serif",
          }}
        >
          No account?{" "}
          <Link
            to="/sign-up"
            style={{ color: ACCENT, textDecoration: "none", fontWeight: 600 }}
          >
            Get started
          </Link>
        </p>
      </div>
    </div>
  );
};

export default SignInPage;
