import { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { getKpis } from "../../api/client";

function formatINR(value) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value || 0);
}

function formatINRShort(value) {
  // compact axis labels, e.g. 54,15,309 -> ₹54.2L
  const v = value || 0;
  if (Math.abs(v) >= 10000000) return `₹${(v / 10000000).toFixed(1)}Cr`;
  if (Math.abs(v) >= 100000) return `₹${(v / 100000).toFixed(1)}L`;
  return `₹${v}`;
}

export default function ReportsView() {
  const [kpis, setKpis] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    getKpis()
      .then(setKpis)
      .catch(() => setError("Could not load KPIs. Is the backend running?"));
  }, []);

  if (error) return <div className="error-banner">{error}</div>;
  if (!kpis) return <div>Loading KPIs…</div>;

  const liabilitySplitData = [
    { name: "Current (next 12 mo.)", value: kpis.liability_current },
    { name: "Non-current", value: kpis.liability_noncurrent },
  ];

  const liabilityMovementData = [
    { name: "Opening", value: kpis.liability_movement.opening },
    { name: "+ Interest", value: kpis.liability_movement.interest },
    { name: "- Payment", value: -kpis.liability_movement.payment },
    { name: "Closing", value: kpis.liability_movement.closing },
  ];

  const rouMovementData = [
    { name: "Opening", value: kpis.rou_movement.opening },
    { name: "- Depreciation", value: -kpis.rou_movement.depreciation },
    { name: "+ Additions", value: kpis.rou_movement.additions },
    { name: "- Deletions", value: kpis.rou_movement.deletions },
    { name: "Closing", value: kpis.rou_movement.closing },
  ];

  return (
    <div>
      <h1>Reports — IND AS 116 KPIs</h1>

      {/* KPI 1, 2, 3, 9 - headline cards */}
      <div className="card-grid">
        <div className="card">
          <div className="card-label">ROU Asset — Gross</div>
          <div className="card-value">{formatINR(kpis.rou_gross)}</div>
        </div>
        <div className="card">
          <div className="card-label">ROU Asset — Net Book Value</div>
          <div className="card-value">{formatINR(kpis.rou_nbv)}</div>
        </div>
        <div className="card">
          <div className="card-label">Lease Liability — Closing</div>
          <div className="card-value">{formatINR(kpis.liability_closing)}</div>
        </div>
        <div className="card">
          <div className="card-label">Ind AS 116 Coverage</div>
          <div className="card-value">{kpis.coverage_percentage}%</div>
          <div style={{ fontSize: 12, color: "#64748b" }}>
            {kpis.coverage_numerator} of {kpis.coverage_denominator} agreements
          </div>
        </div>
      </div>

      {/* KPI 5, 6 - current month / YTD cards */}
      <div className="card-grid" style={{ marginTop: 16 }}>
        <div className="card">
          <div className="card-label">Interest Expense — This Month</div>
          <div className="card-value">{formatINR(kpis.interest_current_month)}</div>
        </div>
        <div className="card">
          <div className="card-label">Interest Expense — YTD</div>
          <div className="card-value">{formatINR(kpis.interest_ytd)}</div>
        </div>
        <div className="card">
          <div className="card-label">Depreciation — This Month</div>
          <div className="card-value">{formatINR(kpis.depreciation_current_month)}</div>
        </div>
        <div className="card">
          <div className="card-label">Depreciation — YTD</div>
          <div className="card-value">{formatINR(kpis.depreciation_ytd)}</div>
        </div>
      </div>

      {/* KPI 4 - Current vs Non-current */}
      <fieldset style={{ marginTop: 24 }}>
        <legend>Lease Liability Split — Current vs Non-current</legend>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={liabilitySplitData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis tickFormatter={formatINRShort} />
            <Tooltip formatter={(v) => formatINR(v)} />
            <Bar dataKey="value" fill="#1d4ed8" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </fieldset>

      {/* KPI 5, 6 - 12 month trend */}
      <fieldset style={{ marginTop: 24 }}>
        <legend>Interest &amp; Depreciation — 12 Month Trend</legend>
        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={kpis.monthly_trend}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis tickFormatter={formatINRShort} />
            <Tooltip formatter={(v) => formatINR(v)} />
            <Legend />
            <Bar dataKey="interest" name="Interest" fill="#1d4ed8" />
            <Bar dataKey="depreciation" name="Depreciation" fill="#16a34a" />
          </BarChart>
        </ResponsiveContainer>
      </fieldset>

      {/* KPI 7 - Liability Movement */}
      <fieldset style={{ marginTop: 24 }}>
        <legend>Lease Liability Movement — Current Month</legend>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={liabilityMovementData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis tickFormatter={formatINRShort} />
            <Tooltip formatter={(v) => formatINR(v)} />
            <Bar dataKey="value" fill="#1d4ed8" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
        <p style={{ fontSize: 13, color: "#64748b" }}>
          Opening {formatINR(kpis.liability_movement.opening)} + Interest {formatINR(kpis.liability_movement.interest)} −
          Payment {formatINR(kpis.liability_movement.payment)} = Closing {formatINR(kpis.liability_movement.closing)}
        </p>
      </fieldset>

      {/* KPI 8 - ROU Movement */}
      <fieldset style={{ marginTop: 24 }}>
        <legend>ROU Asset Movement — Current Month</legend>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={rouMovementData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis tickFormatter={formatINRShort} />
            <Tooltip formatter={(v) => formatINR(v)} />
            <Bar dataKey="value" fill="#16a34a" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
        <p style={{ fontSize: 13, color: "#64748b" }}>
          Additions/deletions are detected automatically: if a period's opening ROU doesn't match the previous
          period's closing ROU, the difference is an amendment-driven remeasurement, not ordinary depreciation.
        </p>
      </fieldset>
    </div>
  );
}
