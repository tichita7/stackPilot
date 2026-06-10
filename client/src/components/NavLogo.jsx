// src/components/NavLogo.jsx
import React from "react";
import { useNavigate } from "react-router-dom";
import logo from "../assets/logo.svg";

const NavLogo = () => {
  const navigate = useNavigate();

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 8,
        cursor: "pointer",
      }}
      onClick={() => navigate("/")}
    >
      <img
        src={logo}
        alt="logo"
        style={{ height: 26, width: "auto", transition: "transform 0.2s" }}
        onMouseEnter={(e) =>
          (e.currentTarget.style.transform = "rotate(15deg)")
        }
        onMouseLeave={(e) => (e.currentTarget.style.transform = "rotate(0deg)")}
      />
      <span
        style={{
          fontFamily: "'DM Mono', monospace",
          fontSize: 20,
          fontWeight: 400,
          letterSpacing: "0.08em",
          color: "#F5F2EB",
        }}
      >
        StackPilot
        {/* <span
          style={{
            background:
              "linear-gradient(90deg, #ff7e5f, #feb47b, #86a8e7, #91eae4)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            backgroundClip: "text",
            color: "transparent",
            fontWeight: "bold", // Optional, but makes gradients pop!
          }}
        >
          Pilot 
        </span> */}
      </span>
    </div>
  );
};

export default NavLogo;
