import React, { useState, useRef, useEffect } from "react";
import { useClerk } from "@clerk/clerk-react";

const BG = "#131312";
const INK = "#F5F2EB";
const INK2 = "#9b9b98";
const BORDER = "#2a2a28";
const ACCENT = "#E8572A";

const CustomUserMenu = ({ user }) => {
  const { signOut } = useClerk();
  const [open, setOpen] = useState(false);
  const ref = useRef();

  useEffect(() => {
    const handler = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  if (!user) return null;

  return (
    <div ref={ref} style={{ position: "relative" }}>
      <button
        onClick={() => setOpen((o) => !o)}
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          background: "none",
          border: `1px solid ${BORDER}`,
          borderRadius: 999,
          padding: "4px 12px 4px 4px",
          cursor: "pointer",
          transition: "border-color 0.15s",
        }}
        onMouseEnter={(e) => (e.currentTarget.style.borderColor = "#555")}
        onMouseLeave={(e) => (e.currentTarget.style.borderColor = BORDER)}
      >
        <img
          src={user.imageUrl}
          alt={user.fullName}
          style={{
            width: 26,
            height: 26,
            borderRadius: "50%",
            objectFit: "cover",
          }}
        />
        <span
          style={{
            fontFamily: "'Syne', sans-serif",
            fontSize: 12,
            fontWeight: 600,
            color: INK,
          }}
        >
          {user.firstName}
        </span>
        <svg
          width="11"
          height="11"
          viewBox="0 0 24 24"
          fill="none"
          stroke={INK2}
          strokeWidth="2.5"
          style={{
            transform: open ? "rotate(180deg)" : "rotate(0deg)",
            transition: "transform 0.2s",
          }}
        >
          <path d="M6 9l6 6 6-6" />
        </svg>
      </button>

      {open && (
        <div
          style={{
            position: "absolute",
            right: 0,
            top: "calc(100% + 8px)",
            background: "#1c1c1a",
            border: `1px solid ${BORDER}`,
            borderRadius: 12,
            minWidth: 220,
            zIndex: 999,
            boxShadow: "0 8px 32px rgba(0,0,0,0.5)",
            overflow: "hidden",
          }}
        >
          {/* User info */}
          <div
            style={{
              padding: "14px 16px",
              borderBottom: `1px solid ${BORDER}`,
              display: "flex",
              alignItems: "center",
              gap: 10,
            }}
          >
            <img
              src={user.imageUrl}
              alt={user.fullName}
              style={{
                width: 34,
                height: 34,
                borderRadius: "50%",
                objectFit: "cover",
              }}
            />
            <div>
              <div
                style={{
                  fontFamily: "'Syne', sans-serif",
                  fontWeight: 700,
                  fontSize: 13,
                  color: INK,
                }}
              >
                {user.fullName}
              </div>
              <div
                style={{
                  fontFamily: "'DM Mono', monospace",
                  fontSize: 11,
                  color: INK2,
                  marginTop: 2,
                }}
              >
                {user.primaryEmailAddress?.emailAddress}
              </div>
            </div>
          </div>

          {/* Sign out */}
          <button
            onClick={() => signOut({ redirectUrl: "/" })}
            style={{
              width: "100%",
              padding: "11px 16px",
              background: "none",
              border: "none",
              color: ACCENT,
              fontSize: 13,
              textAlign: "left",
              cursor: "pointer",
              fontFamily: "'Syne', sans-serif",
              fontWeight: 600,
              display: "flex",
              alignItems: "center",
              gap: 8,
            }}
            onMouseEnter={(e) =>
              (e.currentTarget.style.background = "rgba(232,87,42,0.08)")
            }
            onMouseLeave={(e) => (e.currentTarget.style.background = "none")}
          >
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9" />
            </svg>
            Sign out
          </button>
        </div>
      )}
    </div>
  );
};

export default CustomUserMenu;
