"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function Sidebar({ currentTab = "Dashboard", onTabChange }) {
  const pathname = usePathname();

  const navItems = [
    {
      name: "Dashboard",
      path: "/",
      icon: (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
          <rect x="3" y="3" width="7" height="9" />
          <rect x="14" y="3" width="7" height="5" />
          <rect x="14" y="12" width="7" height="9" />
          <rect x="3" y="16" width="7" height="5" />
        </svg>
      )
    },
    {
      name: "Recommendations",
      path: "#recommendations",
      icon: (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3" />
        </svg>
      )
    },
    {
      name: "Uplift",
      path: "#uplift",
      icon: (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
          <line x1="18" y1="20" x2="18" y2="10" />
          <line x1="12" y1="20" x2="12" y2="4" />
          <line x1="6" y1="20" x2="6" y2="14" />
        </svg>
      )
    },
    {
      name: "Settings",
      path: "#settings",
      icon: (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="3" />
          <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
        </svg>
      )
    }
  ];

  return (
    <aside className="sidebar">
      <div className="brand-section" onClick={() => onTabChange && onTabChange("Dashboard")} style={{ cursor: "pointer" }}>
        <div className="brand-logo">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <polyline points="22 7 13.5 15.5 8.5 10.5 2 17" />
            <polyline points="16 7 22 7 22 13" />
          </svg>
        </div>
        <div className="brand-name-wrapper">
          <span className="brand-name">EconoCausal</span>
          <span className="brand-subtitle">Smarter Insights. Higher Revenue.</span>
        </div>
      </div>

      <nav style={{ flex: 1, overflowY: "auto", marginBottom: "1rem" }}>
        <ul className="nav-menu">
          {navItems.map((item) => {
            const isActive = item.name === currentTab;
            return (
              <li key={item.name} className={`nav-item ${isActive ? "active" : ""}`}>
                <button
                  onClick={() => onTabChange && onTabChange(item.name)}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "0.75rem",
                    width: "100%",
                    padding: "0.85rem 1rem",
                    borderRadius: "8px",
                    fontWeight: "600",
                    color: isActive ? "var(--primary)" : "var(--text-secondary)",
                    backgroundColor: isActive ? "var(--primary-glow)" : "transparent",
                    cursor: "pointer",
                    textAlign: "left",
                    transition: "all 0.2s ease"
                  }}
                >
                  {item.icon}
                  <span style={{ fontSize: "0.95rem" }}>{item.name}</span>
                </button>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* AI Promotion card at the bottom of the sidebar */}
      <div className="sidebar-promo-card">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#065f46" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
        </svg>
        <span className="promo-title">AI-Powered Causal Marketing</span>
        <span className="promo-desc">Turn insights into measurable growth.</span>
        <div className="promo-badge">
          <span className="status-dot-green" />
          <span>Live Data</span>
        </div>
      </div>
    </aside>
  );
}
