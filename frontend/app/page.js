"use client";

import { useEffect, useState, useCallback } from "react";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";

export default function Home() {
  const [currentTab, setCurrentTab] = useState("Dashboard");
  const [summary, setSummary] = useState(null);
  const [causalSummary, setCausalSummary] = useState(null);
  const [recommendationsData, setRecommendationsData] = useState(null);
  
  const [budget, setBudget] = useState(1000000); // Default budget: ₹1,000,000
  const [limit, setLimit] = useState(10); // Limit items in table
  const [searchQuery, setSearchQuery] = useState(""); // Recommendation search query
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Causal ML Retraining States
  const [modelType, setModelType] = useState("t_learner");
  const [baseEstimator, setBaseEstimator] = useState("gradient_boosting");
  const [seed, setSeed] = useState(42);
  const [isRetraining, setIsRetraining] = useState(false);
  const [retrainSuccess, setRetrainSuccess] = useState(false);

  // Side Palette / Drawer States
  const [selectedCustomerId, setSelectedCustomerId] = useState(null);
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [selectedCustomerLoading, setSelectedCustomerLoading] = useState(false);

  // Fetch static data (summary + causal metrics)
  const fetchStaticData = useCallback(async () => {
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
  }, []);

  useEffect(() => {
    fetchStaticData();
  }, [fetchStaticData]);

  // Fetch dynamic recommendations based on budget/limit
  const fetchRecommendations = useCallback(async (currentBudget, currentLimit) => {
    try {
      const res = await fetch(
        `http://127.0.0.1:8001/api/recommendations?budget=${currentBudget}&limit=100` // fetch 100 for search/paging
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
    fetchRecommendations(budget, limit);
  }, [budget, limit, fetchRecommendations]);

  const handleBudgetChange = (e) => {
    setBudget(Number(e.target.value));
    setLoading(true);
  };

  // Causal ML Retraining Handler
  const handleRetrainSubmit = async (e) => {
    e.preventDefault();
    setIsRetraining(true);
    setRetrainSuccess(false);
    setError(null);

    try {
      const res = await fetch("http://127.0.0.1:8001/api/causal/retrain", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model_type: modelType,
          base_estimator: baseEstimator,
          seed: Number(seed)
        })
      });

      if (!res.ok) {
        throw new Error("Failed to execute model retraining.");
      }

      const updatedCausalSummary = await res.json();
      setCausalSummary(updatedCausalSummary);
      setRetrainSuccess(true);
      
      // Refresh recommendations and general summary
      await Promise.all([
        fetchStaticData(),
        fetchRecommendations(budget, limit)
      ]);

      // Automatically clear success banner after 5 seconds
      setTimeout(() => setRetrainSuccess(false), 5000);

    } catch (err) {
      console.error(err);
      setError(err.message || "Retraining failed. Please check backend console logs.");
    } finally {
      setIsRetraining(false);
    }
  };

  // Click row to open Side Palette (Drawer)
  const handleRowClick = async (customerId) => {
    setSelectedCustomerId(customerId);
    setSelectedCustomerLoading(true);
    setSelectedCustomer(null);
    try {
      const res = await fetch(`http://127.0.0.1:8001/api/customers/${customerId}`);
      if (res.ok) {
        const data = await res.json();
        setSelectedCustomer(data);
      } else {
        console.error("Customer record not found on backend.");
      }
    } catch (err) {
      console.error("Error loading customer data:", err);
    } finally {
      setSelectedCustomerLoading(false);
    }
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

  // Filtering recommendations based on search
  const filteredRecs = recommendationsData?.recommendations.filter((rec) => {
    if (!searchQuery) return true;
    return String(rec.customer_id).includes(searchQuery);
  }) || [];

  const paginatedRecs = filteredRecs.slice(0, limit);

  return (
    <div className="app-layout">
      <Sidebar currentTab={currentTab} onTabChange={setCurrentTab} />
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
            <strong>Error:</strong> {error}. Please check Python console logs.
          </div>
        )}

        {/* ==================================================================
            TAB: DASHBOARD
            ================================================================== */}
        {currentTab === "Dashboard" && (
          <>
            {/* Top Summary Metrics Grid */}
            <section className="stats-grid">
              {summary ? (
                <>
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

                  <div className="card">
                    <div className="stat-header-flex">
                      <span className="stat-label-text">Average True ITE</span>
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

            {/* 2-Column Dashboard Panels */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: "1.5rem" }}>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "1.5rem", alignItems: "start" }}>
                
                {/* Left Side: Simulator and Summary Info */}
                <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
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
                </div>

                {/* Right Side: Insights & Model Diagnostics */}
                <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
                  <section className="card">
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.25rem" }}>
                      <h2 className="card-title">Customer Insights</h2>
                    </div>

                    <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
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
                    </div>
                  </section>

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

                          {causalSummary.qini_coefficient !== undefined && (
                            <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px dashed var(--border-color)", paddingBottom: "0.65rem" }}>
                              <span style={{ color: "var(--text-secondary)", fontWeight: "500" }}>Normalized Qini Coeff</span>
                              <span style={{ fontWeight: "700", fontFamily: "var(--font-mono)", color: "var(--primary)" }}>
                                {causalSummary.qini_coefficient.toFixed(4)}
                              </span>
                            </div>
                          )}

                          {causalSummary.mae !== undefined && (
                            <div style={{ display: "flex", justifyContent: "space-between" }}>
                              <span style={{ color: "var(--text-secondary)", fontWeight: "500" }}>Mean Absolute Error (MAE)</span>
                              <span style={{ fontWeight: "700", fontFamily: "var(--font-mono)" }}>
                                {causalSummary.mae.toFixed(5)}
                              </span>
                            </div>
                          )}
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
          </>
        )}

        {/* ==================================================================
            TAB: RECOMMENDATIONS
            ================================================================== */}
        {currentTab === "Recommendations" && (
          <section className="card table-card">
            <div className="card-title-section">
              <div>
                <h2 className="card-title">Top Customers by ITE</h2>
                <p className="card-subtitle">Optimal customer targets ranked by individual treatment effects. Click a customer row to view their side palette profile.</p>
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
                {/* Search query */}
                <input
                  type="text"
                  placeholder="Search customer ID..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  style={{
                    backgroundColor: "#ffffff",
                    border: "1px solid var(--border-color)",
                    padding: "0.4rem 0.8rem",
                    borderRadius: "6px",
                    fontSize: "0.85rem",
                    width: "180px",
                    fontWeight: "500"
                  }}
                />

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
                    <option value="50">50</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="table-container">
              {loading && !recommendationsData ? (
                <div style={{ padding: "1.5rem", display: "flex", flexDirection: "column", gap: "10px" }}>
                  {Array.from({ length: 6 }).map((_, idx) => (
                    <div key={idx} className="skeleton" style={{ height: "24px", width: "100%" }}></div>
                  ))}
                </div>
              ) : paginatedRecs.length > 0 ? (
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
                    {paginatedRecs.map((rec) => {
                      const roi = rec.expected_cost > 0 
                        ? (rec.expected_profit / rec.expected_cost).toFixed(2)
                        : "0.0";
                      
                      return (
                        <tr 
                          key={rec.customer_id} 
                          onClick={() => handleRowClick(rec.customer_id)}
                          className="table-row-interactive"
                        >
                          <td style={{ fontWeight: "600", fontFamily: "var(--font-mono)", color: "var(--primary)" }}>
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
                <div style={{ padding: "3rem", textAlign: "center", color: "var(--text-muted)", fontWeight: "500" }}>
                  No target customers found matching search parameters.
                </div>
              )}
            </div>

            <div style={{ display: "flex", justifySelf: "flex-end", justifyContent: "space-between", alignItems: "center", fontSize: "0.85rem", color: "var(--text-muted)", marginTop: "0.5rem" }}>
              <span>Showing {paginatedRecs.length} of {filteredRecs.length} customers</span>
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
        )}

        {/* ==================================================================
            TAB: SETTINGS (MODEL RETRAINING)
            ================================================================== */}
        {currentTab === "Settings" && (
          <section className="form-card">
            <h2 className="card-title" style={{ marginBottom: "0.5rem" }}>Causal Estimator Settings</h2>
            <p className="card-subtitle" style={{ marginBottom: "2rem" }}>Configure treatment effect models and run retraining workflows on live datasets.</p>

            {retrainSuccess && (
              <div className="retrain-success-banner">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ flexShrink: 0 }}>
                  <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                  <polyline points="22 4 12 14.01 9 11.01" />
                </svg>
                <div>
                  <strong style={{ display: "block" }}>Retraining Successful!</strong>
                  <span style={{ fontSize: "0.85rem" }}>Causal models have been successfully retrained, and target metrics updated across the dashboard.</span>
                </div>
              </div>
            )}

            {isRetraining ? (
              <div className="loading-overlay">
                <div className="spinner"></div>
                <div style={{ fontWeight: "700", color: "var(--text-primary)" }}>Executing ML Training Pipeline...</div>
                <div style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>
                  Running preprocessing, fitting models (T-Learner), computing predictions, and executing diagnostics. Please wait.
                </div>
              </div>
            ) : (
              <form onSubmit={handleRetrainSubmit}>
                <div className="form-group">
                  <label className="form-label">Causal Estimator Type</label>
                  <select 
                    value={modelType} 
                    onChange={(e) => setModelType(e.target.value)}
                    className="form-control form-select"
                  >
                    <option value="t_learner">T-Learner (Separate Treated/Control Models)</option>
                    <option value="x_learner">X-Learner (Propensity-weighted meta-learner)</option>
                    <option value="dml">Double Machine Learning (DML Residual Model)</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Base ML Estimator</label>
                  <select 
                    value={baseEstimator} 
                    onChange={(e) => setBaseEstimator(e.target.value)}
                    className="form-control form-select"
                  >
                    <option value="gradient_boosting">Gradient Boosting Classifiers/Regressors</option>
                    <option value="random_forest">Random Forest Ensembles</option>
                    <option value="linear">Linear Models (Logistic Regression / Ridge)</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Random Seed</label>
                  <input 
                    type="number"
                    value={seed}
                    onChange={(e) => setSeed(Number(e.target.value))}
                    className="form-control"
                    min="1"
                    max="100000"
                  />
                </div>

                <div style={{ marginTop: "2rem", display: "flex", justifyContent: "flex-end" }}>
                  <button 
                    type="submit" 
                    className="custom-button custom-button-primary"
                    style={{ padding: "0.75rem 1.5rem", borderRadius: "8px", fontWeight: "700" }}
                  >
                    Run Causal Model Retraining
                  </button>
                </div>
              </form>
            )}
          </section>
        )}

        {/* Live Insight Banner Strip */}
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

      {/* ==================================================================
          SIDE PALETTE / SLIDE-OVER DRAWER (CUSTOMER PROFILE)
          ================================================================== */}
      <div 
        className={`drawer-backdrop ${selectedCustomerId !== null ? "open" : ""}`}
        onClick={() => setSelectedCustomerId(null)}
      >
        <div 
          className="drawer-panel"
          onClick={(e) => e.stopPropagation()} // Prevent close on drawer body click
        >
          <div className="drawer-header">
            <h3 className="drawer-title">
              {selectedCustomerId ? `Customer CUST_${String(selectedCustomerId).padStart(6, "0")}` : "Customer Details"}
            </h3>
            <button className="drawer-close-btn" onClick={() => setSelectedCustomerId(null)}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>

          <div className="drawer-body">
            {selectedCustomerLoading ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
                <div className="skeleton" style={{ height: "40px", width: "100%" }}></div>
                <div className="skeleton" style={{ height: "100px", width: "100%" }}></div>
                <div className="skeleton" style={{ height: "120px", width: "100%" }}></div>
              </div>
            ) : selectedCustomer ? (
              <>
                {/* Section 1: Demographics */}
                <div>
                  <h4 className="detail-section-title" style={{ marginBottom: "1rem" }}>Customer Profile</h4>
                  <div className="detail-grid-cols">
                    <div className="detail-item-box">
                      <span className="detail-item-label">Age</span>
                      <div className="detail-item-val">{selectedCustomer.age} years</div>
                    </div>
                    <div className="detail-item-box">
                      <span className="detail-item-label">Customer Segment</span>
                      <div className="detail-item-val" style={{ textTransform: "capitalize" }}>
                        {selectedCustomer.customer_segment?.replace("_", " ")}
                      </div>
                    </div>
                    <div className="detail-item-box" style={{ gridColumn: "span 2" }}>
                      <span className="detail-item-label">Tenure</span>
                      <div className="detail-item-val">{selectedCustomer.tenure_months} months registered</div>
                    </div>
                  </div>
                </div>

                {/* Section 2: Historical Activities */}
                <div>
                  <h4 className="detail-section-title" style={{ marginBottom: "1rem" }}>Activity & History</h4>
                  <div className="detail-grid-cols">
                    <div className="detail-item-box">
                      <span className="detail-item-label">Historical Orders</span>
                      <div className="detail-item-val">{selectedCustomer.historical_orders}</div>
                    </div>
                    <div className="detail-item-box">
                      <span className="detail-item-label">Avg Order Value</span>
                      <div className="detail-item-val">{formatCurrency(selectedCustomer.avg_order_value)}</div>
                    </div>
                    <div className="detail-item-box" style={{ gridColumn: "span 2" }}>
                      <span className="detail-item-label">Historical Revenue</span>
                      <div className="detail-item-val" style={{ color: "var(--success)" }}>
                        {formatCurrency(selectedCustomer.historical_revenue)}
                      </div>
                    </div>
                    <div className="detail-item-box">
                      <span className="detail-item-label">Website Visits</span>
                      <div className="detail-item-val">{selectedCustomer.website_visits}</div>
                    </div>
                    <div className="detail-item-box">
                      <span className="detail-item-label">Recency</span>
                      <div className="detail-item-val">{selectedCustomer.days_since_last_purchase} days ago</div>
                    </div>
                    <div className="detail-item-box">
                      <span className="detail-item-label">Email Opens</span>
                      <div className="detail-item-val">{selectedCustomer.email_opens}</div>
                    </div>
                    <div className="detail-item-box">
                      <span className="detail-item-label">Email Clicks</span>
                      <div className="detail-item-val">{selectedCustomer.email_clicks}</div>
                    </div>
                  </div>
                </div>

                {/* Section 3: Causal Model Estimates */}
                <div>
                  <h4 className="detail-section-title" style={{ marginBottom: "1rem" }}>Causal Estimation</h4>
                  
                  {/* Find customer item in recommendations list to get predicted values */}
                  {(() => {
                    const recItem = recommendationsData?.recommendations.find(
                      (r) => r.customer_id === selectedCustomer.customer_id
                    );
                    
                    const iteVal = recItem ? recItem.predicted_ite : selectedCustomer.true_ite;
                    const roi = recItem && recItem.expected_cost > 0
                      ? (recItem.expected_profit / recItem.expected_cost).toFixed(2)
                      : "0.0";
                    
                    return (
                      <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                        <div style={{ display: "flex", gap: "1rem" }}>
                          <div className="detail-item-box" style={{ flex: 1 }}>
                            <span className="detail-item-label">Uplift Score (ITE)</span>
                            <div className="detail-item-val" style={{ color: "var(--primary)", fontSize: "1.2rem" }}>
                              +{iteVal.toFixed(5)}
                            </div>
                          </div>
                          
                          <div className="detail-item-box" style={{ flex: 1 }}>
                            <span className="detail-item-label">Projected ROI</span>
                            <div className="detail-item-val" style={{ color: parseFloat(roi) > 1.5 ? "var(--success)" : "var(--warning)" }}>
                              {roi}x
                            </div>
                          </div>
                        </div>

                        <div className="detail-item-box">
                          <span className="detail-item-label">Recommended Action</span>
                          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginTop: "0.3rem" }}>
                            <span className="badge badge-primary">
                              {selectedCustomer.discount_percentage ? `${selectedCustomer.discount_percentage * 100}%` : "10%"} Price Discount
                            </span>
                            <span className={`badge ${parseFloat(roi) > 1.5 ? "badge-success" : "badge-warning"}`}>
                              {parseFloat(roi) > 1.5 ? "Target Now" : "Nurture"}
                            </span>
                          </div>
                        </div>

                        <div className="detail-item-box" style={{ backgroundColor: "var(--bg-secondary)", borderStyle: "dashed" }}>
                          <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginBottom: "0.4rem" }}>Potential Outcome Probabilities</div>
                          <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.85rem" }}>
                            <span>Purchase Prob (Control - No Discount):</span>
                            <span style={{ fontWeight: "700", fontFamily: "var(--font-mono)" }}>
                              {formatPercentage(selectedCustomer.true_baseline_purchase_probability || 0.15)}
                            </span>
                          </div>
                          <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.85rem", marginTop: "0.25rem" }}>
                            <span>Purchase Prob (Treated - Discount):</span>
                            <span style={{ fontWeight: "700", fontFamily: "var(--font-mono)", color: "var(--primary)" }}>
                              {formatPercentage(selectedCustomer.true_treatment_purchase_probability || 0.25)}
                            </span>
                          </div>
                        </div>
                      </div>
                    );
                  })()}
                </div>
              </>
            ) : (
              <div style={{ padding: "3rem", textAlign: "center", color: "var(--text-muted)" }}>
                Failed to load profile details.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
