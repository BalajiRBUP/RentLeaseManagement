import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getAgreement, getRentPostingsForAgreement, getRentPostingDownloadUrl } from "../../api/client";

function formatINR(value) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Number(value) || 0);
}

export default function AgreementDetail() {
  const { id } = useParams();
  const [agreement, setAgreement] = useState(null);
  const [rentPostings, setRentPostings] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    getAgreement(id)
      .then(setAgreement)
      .catch(() => setError("Could not load this agreement."));
    getRentPostingsForAgreement(id)
      .then(setRentPostings)
      .catch(() => {}); // non-critical - agreement page still works without this
  }, [id]);

  if (error) return <div className="error-banner">{error}</div>;
  if (!agreement) return <div>Loading…</div>;

  return (
    <div>
      <div className="page-header">
        <h1>
          {agreement.urn} <span className={`status-badge status-${agreement.status.toLowerCase()}`}>{agreement.status}</span>
        </h1>
        <Link to="/agreements" className="btn-secondary">
          ← Back to list
        </Link>
      </div>

      <fieldset>
        <legend>Summary</legend>
        <div className="detail-grid">
          <div>
            <span className="detail-label">Name</span>
            <div>{agreement.agreement_name || "—"}</div>
          </div>
          <div>
            <span className="detail-label">Period</span>
            <div>
              {agreement.start_date} → {agreement.end_date}
            </div>
          </div>
          <div>
            <span className="detail-label">Total Rent</span>
            <div className="amount">{formatINR(agreement.total_rent)}</div>
          </div>
          <div>
            <span className="detail-label">GST % / TDS %</span>
            <div>
              {agreement.gst_percentage}% / {agreement.tds_percentage}%
            </div>
          </div>
          <div>
            <span className="detail-label">Escalation</span>
            <div>
              {agreement.escalation_percentage}% every {agreement.escalation_period} months
            </div>
          </div>
          <div>
            <span className="detail-label">Discount Rate (IND AS 116)</span>
            <div>{agreement.discount_rate}%</div>
          </div>
          <div>
            <span className="detail-label">Security Deposit</span>
            <div className="amount">{formatINR(agreement.security_deposit)}</div>
          </div>
          <div>
            <span className="detail-label">Created By</span>
            <div>{agreement.created_by}</div>
          </div>
        </div>
      </fieldset>

      {/* Section 1: Agreement + vendor-wise details */}
      <fieldset>
        <legend>Vendor Allocation Breakdown</legend>
        <table className="data-table">
          <thead>
            <tr>
              <th>Vendor</th>
              <th>Cost Center</th>
              <th>Profit Center</th>
              <th>Split %</th>
              <th className="amount">Rent</th>
              <th className="amount">GST</th>
              <th className="amount">TDS</th>
              <th className="amount">Net Payable</th>
            </tr>
          </thead>
          <tbody>
            {agreement.allocations.map((a) => (
              <tr key={a.id}>
                <td>{a.vendor.vendor_name}</td>
                <td>{a.cost_center.cost_center_text}</td>
                <td>{a.profit_center.profit_center_text}</td>
                <td>{a.split_percentage}%</td>
                <td className="amount">{formatINR(a.calculated_rent)}</td>
                <td className="amount">{formatINR(a.calculated_gst)}</td>
                <td className="amount">{formatINR(a.calculated_tds)}</td>
                <td className="amount">{formatINR(a.net_payable)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </fieldset>

      {/* Section 2: Rent payment details - every invoice submitted for this agreement */}
      <fieldset>
        <legend>Rent Payment Details</legend>
        {rentPostings.length === 0 ? (
          <p style={{ color: "#64748b", fontSize: 14 }}>No rent invoices submitted for this agreement yet.</p>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Month</th>
                  <th>Vendor</th>
                  <th className="amount">Invoice Amount</th>
                  <th className="amount">Rent Cap</th>
                  <th>Status</th>
                  <th>Document No.</th>
                  <th>Attachment</th>
                  <th>Submitted By</th>
                  <th>Approved By</th>
                </tr>
              </thead>
              <tbody>
                {rentPostings.map((r) => (
                  <tr key={r.id}>
                    <td>
                      {r.period_start} → {r.period_end}
                    </td>
                    <td>{r.vendor_name}</td>
                    <td className="amount">{formatINR(r.invoice_amount)}</td>
                    <td className="amount">{formatINR(r.calculated_rent_amount)}</td>
                    <td>
                      <span
                        className={`status-badge status-${r.status === "Rejected" ? "terminated" : r.status === "Submitted" ? "pending" : r.status.toLowerCase()}`}
                      >
                        {r.status}
                      </span>
                    </td>
                    <td style={{ fontSize: 12 }}>{r.document_number || "—"}</td>
                    <td>
                      <a href={getRentPostingDownloadUrl(r.id)} download>
                        {r.invoice_file_name}
                      </a>
                    </td>
                    <td>{r.submitted_by}</td>
                    <td>{r.approved_by || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </fieldset>
    </div>
  );
}
