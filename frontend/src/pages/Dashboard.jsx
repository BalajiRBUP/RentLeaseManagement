import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getDashboardSummary } from "../api/client";

function formatINR(value) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value || 0);
}

export default function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    getDashboardSummary()
      .then(setSummary)
      .catch(() => setError("Could not reach the API. Is the backend running on the configured URL?"));
  }, []);

  if (error) return <div className="error-banner">{error}</div>;
  if (!summary) return <div>Loading dashboard…</div>;

  return (
    <div>
      <h1>Dashboard</h1>

      <div className="card-grid">
        <div className="card">
          <div className="card-label">Total Agreements</div>
          <div className="card-value">{summary.total_agreements}</div>
        </div>
        <div className="card">
          <div className="card-label">Total Rent (monthly)</div>
          <div className="card-value">{formatINR(summary.total_rent)}</div>
        </div>
        {Object.entries(summary.by_status).map(([status, count]) => (
          <div className="card" key={status}>
            <div className="card-label">{status}</div>
            <div className="card-value">{count}</div>
          </div>
        ))}
      </div>

      <fieldset style={{ marginTop: 24 }}>
        <legend>Portfolio Exposure (as of today, IND AS 116)</legend>
        <div className="card-grid">
          <div className="card">
            <div className="card-label">Outstanding Lease Liability</div>
            <div className="card-value">{formatINR(summary.outstanding_liability)}</div>
          </div>
          <div className="card">
            <div className="card-label">Outstanding ROU Asset</div>
            <div className="card-value">{formatINR(summary.outstanding_rou)}</div>
          </div>
          <div className="card">
            <div className="card-label">Pending Amendments</div>
            <div className="card-value">{summary.pending_amendments_count}</div>
            {summary.pending_amendments_count > 0 && (
              <Link to="/amendments" style={{ fontSize: 13 }}>
                Review →
              </Link>
            )}
          </div>
          <div className="card">
            <div className="card-label">Overdue / Unposted Periods</div>
            <div className="card-value">{summary.overdue_postings_count}</div>
            {summary.overdue_postings_count > 0 && (
              <Link to="/lease" style={{ fontSize: 13 }}>
                Review →
              </Link>
            )}
          </div>
        </div>
      </fieldset>

      <fieldset style={{ marginTop: 24 }}>
        <legend>Upcoming Expirations (next 90 days)</legend>
        {summary.upcoming_expirations.length === 0 ? (
          <p style={{ color: "#64748b", fontSize: 14 }}>No agreements expiring in the next 90 days.</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>URN</th>
                <th>Name</th>
                <th>End Date</th>
                <th>Days Remaining</th>
              </tr>
            </thead>
            <tbody>
              {summary.upcoming_expirations.map((a) => (
                <tr key={a.id}>
                  <td>
                    <Link to={`/agreements/${a.id}`}>{a.urn}</Link>
                  </td>
                  <td>{a.agreement_name || "—"}</td>
                  <td>{a.end_date}</td>
                  <td>
                    <span className={a.days_remaining <= 30 ? "split-bad" : ""}>{a.days_remaining} days</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </fieldset>
    </div>
  );
}
