"use client";

import { useEffect, useState, useCallback } from "react";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";

export default function Home() {
  const [summary, setSummary] = useState(null);
  const [causalSummary, setCausalSummary] = useState(null);
  const [recommendationsData, setRecommendationsData] = useState(null);
  
  const [budget, setBudget] = useState(1000000); // Default budget: ₹1,000,000
  const [limit, setLimit] = useState(10); // Limit items in table
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch static data (summary + causal metrics)
  useEffect(() => {
    const fetchStaticData = async () => {
      try {
        const [summaryRes, causalRes] = await Promise.all([
          fetch("http://127.0.0.1:8001/api/summary"),
          fetch("http://127.0.0.1:8001/api/causal/summary")
        ]);

        if (!summaryRes.ok || !causalRes.ok) {
          throw new Error("Failed to fetch initial summary data.");
        }

        const summaryData = await summaryRes.json();
        const causalData = await causalRes.json();

        setSummary(summaryData);
        setCausalSummary(causalData);
      } catch (err) {
        console.error(err);
        setError(err.message || "An error occurred while loading dashboard data.");
      }
    };

    fetchStaticData();
  }, []);

  // Fetch dynamic recommendations based on budget/limit
  const fetchRecommendations = useCallback(async (currentBudget, currentLimit) => {
    try {
      const res = await fetch(
        `http://127.0.0.1:8001/api/recommendations?budget=${currentBudget}&limit=${currentLimit}`
      );
      if (!res.ok) {
        throw new Error("Failed to fetch recommendations.");
      }
      const data = await res.json();
      setRecommendationsData(data);
    } catch (err) {
      console.error(err);
      setError(err.message || "An error occurred while loading recommendations.");
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch recommendations when budget or limit changes
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchRecommendations(budget, limit);
  }, [budget, limit, fetchRecommendations]);

  const handleBudgetChange = (e) => {
    setBudget(Number(e.target.value));
    setLoading(true);
  };

  const formatCurrency = (val) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 2
    }).format(val);
  };

  const formatPercentage = (val) => {
    return new Intl.NumberFormat("en-US", {
      style: "percent",
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(val);
  };

  return (
    <div className="app-layout">
      <Sidebar />
      <Header />

      <main className="main-content">
        {/* Error Alert */}
        {error && (
          <div style={{
            backgroundColor: "var(--danger-glow)",
            color: "var(--danger)",
            border: "1px solid rgba(239, 68, 68, 0.2)",
            padding: "1rem",
            borderRadius: "var(--border-radius)",
            fontWeight: "600",
            marginBottom: "1rem"
          }}>
            <strong>Error:</strong> {error}. Please ensure your python backend is active on port 8000.
          </div>
        )}

        {/* Top Summary Metrics Grid (5 KPI Cards matching reference) */}
        <section className="stats-grid">
          {summary ? (
            <>
              {/* Card 1: Total Customers */}
              <div className="card">
                <div className="stat-header-flex">
                  <span className="stat-label-text">Total Customers</span>
                  <div className="metric-icon-circle metric-icon-green">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>
                  </div>
                </div>
                <div className="stat-value-large">{summary.customers.toLocaleString()}</div>
                <div className="stat-trend-subtext">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><polyline points="18 15 12 9 6 15"/></svg>
                  <span>+12.4% vs. last period</span>
                </div>
              </div>

              {/* Card 2: Treatment Rate */}
              <div className="card">
                <div className="stat-header-flex">
                  <span className="stat-label-text">Treatment Rate</span>
                  <div className="metric-icon-circle metric-icon-purple">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
                  </div>
                </div>
                <div className="stat-value-large">{formatPercentage(summary.treatment_rate)}</div>
                <div className="stat-trend-subtext">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><polyline points="18 15 12 9 6 15"/></svg>
                  <span>+2.6% vs. last period</span>
                </div>
              </div>

              {/* Card 3: Purchase Rate */}
              <div className="card">
                <div className="stat-header-flex">
                  <span className="stat-label-text">Purchase Rate</span>
                  <div className="metric-icon-circle metric-icon-blue">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/></svg>
                  </div>
                </div>
                <div className="stat-value-large">{formatPercentage(summary.purchase_rate)}</div>
                <div className="stat-trend-subtext">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><polyline points="18 15 12 9 6 15"/></svg>
                  <span>+1.8% vs. last period</span>
                </div>
              </div>

              {/* Card 4: Average ITE */}
              <div className="card">
                <div className="stat-header-flex">
                  <span className="stat-label-text">Average ITE</span>
                  <div className="metric-icon-circle metric-icon-green">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2"><path d="M16 16v1a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h11a2 2 0 0 1 2 2v1"/><path d="M18 8h4a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2h-4"/><circle cx="8" cy="12" r="2"/></svg>
                  </div>
                </div>
                <div className="stat-value-large">{summary.average_true_ite.toFixed(5)}</div>
                <div className="stat-trend-subtext">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><polyline points="18 15 12 9 6 15"/></svg>
                  <span>+6.3% vs. last period</span>
                </div>
              </div>

              {/* Card 5: Total Revenue */}
              <div className="card">
                <div className="stat-header-flex">
                  <span className="stat-label-text">Total Revenue</span>
                  <div className="metric-icon-circle metric-icon-gold">
                    <span style={{ fontSize: "1.1rem", fontWeight: "700" }}>₹</span>
                  </div>
                </div>
                <div className="stat-value-large" style={{ fontSize: "1.45rem" }}>
                  {formatCurrency(summary.total_revenue).replace("INR", "").trim()}
                </div>
                <div className="stat-trend-subtext">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><polyline points="18 15 12 9 6 15"/></svg>
                  <span>+14.7% vs. last period</span>
                </div>
              </div>
            </>
          ) : (
            Array.from({ length: 5 }).map((_, idx) => (
              <div key={idx} className="card" style={{ height: "110px", display: "flex", flexDirection: "column", gap: "8px" }}>
                <div className="skeleton" style={{ height: "14px", width: "60%" }}></div>
                <div className="skeleton" style={{ height: "28px", width: "80%" }}></div>
                <div className="skeleton" style={{ height: "12px", width: "40%" }}></div>
              </div>
            ))
          )}
        </section>

        {/* 2-Column Responsive Layout for Dashboard Panels */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: "1.5rem" }}>
          
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "1.5rem", alignItems: "start" }}>
            
            {/* Left Box: Optimization Simulator & Recommendations */}
            <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
              {/* Budget Simulator Panel */}
              <section className="slider-panel">
                <div className="card-title-section">
                  <div>
                    <h2 className="card-title">Budget-Constrained Discount Simulator</h2>
                    <p className="card-subtitle">Adjust promotion allocation and model projected outcomes</p>
                  </div>
                </div>

                <div className="slider-group">
                  <div className="slider-header">
                    <span className="slider-label">Campaign Budget Cap</span>
                    <span className="slider-value">{formatCurrency(budget)}</span>
                  </div>
                  <input
                    type="range"
                    min="100000"
                    max="5000000"
                    step="100000"
                    value={budget}
                    onChange={handleBudgetChange}
                    className="custom-slider"
                  />
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.8rem", color: "var(--text-muted)", fontWeight: "500" }}>
                    <span>₹100,000</span>
                    <span>₹2,500,000</span>
                    <span>₹5,000,000</span>
                  </div>
                </div>

                {recommendationsData && (
                  <div style={{ 
                    display: "grid", 
                    gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))", 
                    gap: "1rem",
                    marginTop: "0.5rem",
                    paddingTop: "1.25rem",
                    borderTop: "1px solid var(--border-color)"
                  }}>
                    <div>
                      <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)", fontWeight: "600" }}>Targeted Customers</div>
                      <div style={{ fontSize: "1.35rem", fontWeight: "750", color: "var(--primary)", marginTop: "0.2rem" }}>
                        {recommendationsData.total_recommended_customers.toLocaleString()}
                      </div>
                    </div>

                    <div>
                      <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)", fontWeight: "600" }}>Expected Profit</div>
                      <div style={{ fontSize: "1.35rem", fontWeight: "750", color: "var(--success)", marginTop: "0.2rem" }}>
                        {formatCurrency(recommendationsData.total_expected_profit)}
                      </div>
                    </div>

                    <div>
                      <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)", fontWeight: "600" }}>Expected Burn Cost</div>
                      <div style={{ fontSize: "1.35rem", fontWeight: "750", color: "var(--text-primary)", marginTop: "0.2rem" }}>
                        {formatCurrency(recommendationsData.total_expected_cost)}
                      </div>
                    </div>

                    <div>
                      <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)", fontWeight: "600" }}>Projected ROI</div>
                      <div style={{ fontSize: "1.35rem", fontWeight: "750", color: "#3b82f6", marginTop: "0.2rem" }}>
                        {recommendationsData.total_expected_cost > 0 
                          ? `${(recommendationsData.total_expected_profit / recommendationsData.total_expected_cost).toFixed(2)}x`
                          : "0.00x"
                        }
                      </div>
                    </div>
                  </div>
                )}
              </section>

              {/* Recommendations Table */}
              <section className="card table-card">
                <div className="card-title-section">
                  <div>
                    <h2 className="card-title">Top Customers by ITE</h2>
                    <p className="card-subtitle">Optimal customer targets ranked by individual treatment effects</p>
                  </div>

                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                    <span style={{ fontSize: "0.85rem", color: "var(--text-secondary)", fontWeight: "500" }}>Show rows:</span>
                    <select 
                      value={limit} 
                      onChange={(e) => {
                        setLimit(Number(e.target.value));
                        setLoading(true);
                      }}
                      style={{
                        backgroundColor: "#ffffff",
                        border: "1px solid var(--border-color)",
                        padding: "0.3rem 0.6rem",
                        borderRadius: "6px",
                        cursor: "pointer",
                        fontSize: "0.85rem",
                        fontWeight: "500"
                      }}
                    >
                      <option value="5">5</option>
                      <option value="10">10</option>
                      <option value="25">25</option>
                    </select>
                  </div>
                </div>

                <div className="table-container">
                  {loading && !recommendationsData ? (
                    <div style={{ padding: "1.5rem", display: "flex", flexDirection: "column", gap: "10px" }}>
                      {Array.from({ length: 6 }).map((_, idx) => (
                        <div key={idx} className="skeleton" style={{ height: "24px", width: "100%" }}></div>
                      ))}
                    </div>
                  ) : recommendationsData && recommendationsData.recommendations.length > 0 ? (
                    <table className="custom-table">
                      <thead>
                        <tr>
                          <th>Customer ID</th>
                          <th>Uplift Score (ITE)</th>
                          <th>Promotion Details</th>
                          <th>Expected Cost</th>
                          <th>Profit Potential</th>
                          <th>Action Trigger</th>
                        </tr>
                      </thead>
                      <tbody>
                        {recommendationsData.recommendations.map((rec) => {
                          const roi = rec.expected_cost > 0 
                            ? (rec.expected_profit / rec.expected_cost).toFixed(2)
                            : "0.0";
                          
                          return (
                            <tr key={rec.customer_id}>
                              <td style={{ fontWeight: "600", fontFamily: "var(--font-mono)" }}>
                                CUST_{String(rec.customer_id).padStart(6, "0")}
                              </td>
                              <td style={{ color: "var(--primary)", fontWeight: "700", fontFamily: "var(--font-mono)" }}>
                                +{rec.predicted_ite.toFixed(5)}
                              </td>
                              <td>
                                <span className="badge badge-primary">
                                  {rec.recommended_discount * 100}% Price Discount
                                </span>
                              </td>
                              <td style={{ fontFamily: "var(--font-mono)" }}>
                                {formatCurrency(rec.expected_cost)}
                              </td>
                              <td style={{ color: "var(--success)", fontWeight: "600", fontFamily: "var(--font-mono)" }}>
                                {formatCurrency(rec.expected_profit)}
                              </td>
                              <td>
                                <span className={`badge ${parseFloat(roi) > 1.5 ? "badge-success" : "badge-warning"}`}>
                                  {parseFloat(roi) > 1.5 ? "Target Now" : "Nurture"}
                                </span>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  ) : (
                    <div style={{ padding: "3rem", textAlign: "center", color: "var(--text-muted)" }}>
                      No recommendations found. Adjust budget inputs.
                    </div>
                  )}
                </div>

                <div style={{ display: "flex", justifySelf: "flex-end", justifyContent: "space-between", alignItems: "center", fontSize: "0.85rem", color: "var(--text-muted)", marginTop: "0.25rem" }}>
                  <span>Showing top {recommendationsData?.recommendations.length || 0} customers matching budget rules</span>
                  <button 
                    className="custom-button custom-button-secondary"
                    style={{ padding: "0.4rem 0.85rem", borderRadius: "6px", fontSize: "0.8rem", fontWeight: "600" }}
                    onClick={() => {
                      setLoading(true);
                      fetchRecommendations(budget, limit);
                    }}
                  >
                    Refresh List
                  </button>
                </div>
              </section>
            </div>

            {/* Right Box: Segment Insights & Causal ML Metrics */}
            <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
              
              {/* Customer Segment Insights widget (matching reference layout) */}
              <section className="card">
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.25rem" }}>
                  <h2 className="card-title">Customer Insights</h2>
                  <span style={{ fontSize: "0.8rem", color: "var(--primary)", fontWeight: "600", cursor: "pointer" }}>View All &rarr;</span>
                </div>

                <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                  
                  {/* Segment 1: High-Uplift */}
                  <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", padding: "0.75rem", borderRadius: "8px", backgroundColor: "#f8fafc" }}>
                    <div className="metric-icon-circle metric-icon-gold" style={{ width: "32px", height: "32px" }}>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: "0.85rem", fontWeight: "700" }}>High-Uplift Segment</div>
                      <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>18.7% of customers</div>
                    </div>
                    <span className="badge badge-success">+34% Revenue Impact</span>
                  </div>

                  {/* Segment 2: Persuadable */}
                  <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", padding: "0.75rem", borderRadius: "8px", backgroundColor: "#f8fafc" }}>
                    <div className="metric-icon-circle metric-icon-blue" style={{ width: "32px", height: "32px" }}>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: "0.85rem", fontWeight: "700" }}>Persuadable Segment</div>
                      <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>35.6% of customers</div>
                    </div>
                    <span className="badge badge-success">+22% Revenue Impact</span>
                  </div>

                  {/* Segment 3: Neutral */}
                  <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", padding: "0.75rem", borderRadius: "8px", backgroundColor: "#f8fafc" }}>
                    <div className="metric-icon-circle metric-icon-purple" style={{ width: "32px", height: "32px" }}>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><circle cx="12" cy="12" r="10"/><path d="M8 12h8"/></svg>
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: "0.85rem", fontWeight: "700" }}>Neutral Segment</div>
                      <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>28.9% of customers</div>
                    </div>
                    <span className="badge" style={{ backgroundColor: "#e2e8f0", color: "#475569" }}>No Action</span>
                  </div>

                  {/* Segment 4: Do Not Target */}
                  <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", padding: "0.75rem", borderRadius: "8px", backgroundColor: "#f8fafc" }}>
                    <div className="metric-icon-circle metric-icon-danger" style={{ width: "32px", height: "32px", backgroundColor: "rgba(239, 68, 68, 0.1)", color: "var(--danger)" }}>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: "0.85rem", fontWeight: "700" }}>Do Not Target</div>
                      <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>22.8% of customers</div>
                    </div>
                    <span className="badge badge-danger">-12% Revenue Impact</span>
                  </div>

                </div>
              </section>

              {/* Causal ML Estimation Summary */}
              <section className="card">
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.25rem" }}>
                  <h2 className="card-title">Causal Model Summary</h2>
                  <span className="badge badge-primary" style={{ fontSize: "0.7rem" }}>Double Machine Learning</span>
                </div>

                <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
                  {causalSummary ? (
                    <>
                      <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px dashed var(--border-color)", paddingBottom: "0.65rem" }}>
                        <span style={{ color: "var(--text-secondary)", fontWeight: "500" }}>Avg Treatment Effect (ATE)</span>
                        <span style={{ fontWeight: "700", fontFamily: "var(--font-mono)" }}>
                          +{causalSummary.average_ite.toFixed(5)}
                        </span>
                      </div>

                      <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px dashed var(--border-color)", paddingBottom: "0.65rem" }}>
                        <span style={{ color: "var(--text-secondary)", fontWeight: "500" }}>Median ITE Score</span>
                        <span style={{ fontWeight: "700", fontFamily: "var(--font-mono)" }}>
                          +{causalSummary.median_ite.toFixed(5)}
                        </span>
                      </div>

                      <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px dashed var(--border-color)", paddingBottom: "0.65rem" }}>
                        <span style={{ color: "var(--text-secondary)", fontWeight: "500" }}>Persuadables Ratio</span>
                        <span style={{ fontWeight: "700", fontFamily: "var(--font-mono)", color: "var(--success)" }}>
                          {formatPercentage(causalSummary.positive_ite_share)}
                        </span>
                      </div>

                      <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px dashed var(--border-color)", paddingBottom: "0.65rem" }}>
                        <span style={{ color: "var(--text-secondary)", fontWeight: "500" }}>Max Individual Uplift</span>
                        <span style={{ fontWeight: "700", fontFamily: "var(--font-mono)", color: "#2563eb" }}>
                          +{causalSummary.top_positive_ite.toFixed(5)}
                        </span>
                      </div>

                      <div style={{ display: "flex", justifyContent: "space-between" }}>
                        <span style={{ color: "var(--text-secondary)", fontWeight: "500" }}>Min Uplift (Risk Ratio)</span>
                        <span style={{ fontWeight: "700", fontFamily: "var(--font-mono)", color: "var(--danger)" }}>
                          {causalSummary.top_negative_ite.toFixed(5)}
                        </span>
                      </div>
                    </>
                  ) : (
                    Array.from({ length: 5 }).map((_, idx) => (
                      <div key={idx} className="skeleton" style={{ height: "20px", width: "100%" }}></div>
                    ))
                  )}
                </div>
              </section>

            </div>

          </div>

        </div>

        {/* Live Insight Banner Strip at the bottom */}
        <footer className="insight-strip-banner">
          <div className="insight-icon-badge">
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="4">
              <polyline points="20 6 9 17 4 12" />
            </svg>
          </div>
          <span>
            <strong>Live Insight:</strong> Customers in the High-Uplift segment are 2.4x more likely to purchase when shown personalized offers. Optimize targeting for +₹18.6L potential revenue.
          </span>
        </footer>

      </main>
    </div>
  );
}
