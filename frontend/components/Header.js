"use client";

import { useEffect, useState } from "react";

export default function Header() {
  const [apiStatus, setApiStatus] = useState("checking");

  useEffect(() => {
    // Check backend health
    fetch("http://127.0.0.1:8001/api/health")
      .then((res) => res.json())
      .then((data) => {
        if (data.status === "ok") {
          setApiStatus("connected");
        } else {
          setApiStatus("error");
        }
      })
      .catch(() => {
        setApiStatus("disconnected");
      });
  }, []);

  return (
    <header className="header">
      <div className="header-title-section">
        <h1>Welcome to EconoCausal</h1>
        <p>AI-Powered Causal Inference & Uplift Optimization Platform</p>
      </div>

      <div className="header-actions">
        {/* Date Selector widget */}
        <div className="calendar-selector">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
            <line x1="16" y1="2" x2="16" y2="6" />
            <line x1="8" y1="2" x2="8" y2="6" />
            <line x1="3" y1="10" x2="21" y2="10" />
          </svg>
          <span>Apr 15, 2025 - May 15, 2025</span>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </div>

        {/* Live status dot badge */}
        <div className="status-indicator-badge">
          <span 
            className="status-dot-green" 
            style={{ 
              backgroundColor: 
                apiStatus === "connected" ? "var(--success)" : 
                apiStatus === "checking" ? "var(--warning)" : "var(--danger)"
            }} 
          />
          <span style={{ fontSize: "0.8rem", color: "#065f46" }}>
            {apiStatus === "checking" && "Checking"}
            {apiStatus === "connected" && "Live"}
            {apiStatus === "disconnected" && "Offline"}
            {apiStatus === "error" && "Error"}
          </span>
        </div>

        {/* User Profile avatar block */}
        <div className="user-profile-widget">
          <div className="user-avatar">JW</div>
          <div className="user-info-text">
            <span className="user-name">John Wick</span>
            <span className="user-role">Data Scientist</span>
          </div>
        </div>
      </div>
    </header>
  );
}
