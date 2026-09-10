import { useEffect, useState } from "react";
import {
  listAgreements,
  getAgreement,
  getLeaseSchedule,
  getRentCap,
  submitRentInvoice,
  getPendingRentPostings,
  getRentPostingHistory,
  bulkDecideRentPostings,
  getRentPostingDownloadUrl,
} from "../../api/client";
import { formatMonthYear } from "../../utils/formatDate";

function formatINR(value) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  }).format(value || 0);
}

export default function RentPostingView() {
  const [error, setError] = useState(null);

  // --- Submit Invoice (Operational SPOC) ---
  const [agreements, setAgreements] = useState([]);
  const [selectedAgreement, setSelectedAgreement] = useState("");
  const [vendors, setVendors] = useState([]);
  const [periods, setPeriods] = useState([]);
  const [selectedVendor, setSelectedVendor] = useState("");
  const [selectedPeriod, setSelectedPeriod] = useState("");
  const [rentCap, setRentCap] = useState(null);
  const [invoiceAmount, setInvoiceAmount] = useState("");
  const [submittedBy, setSubmittedBy] = useState("");
  const [file, setFile] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(null);

  // --- Approve Postings (Finance SPOC) ---
  const [pending, setPending] = useState([]);
  const [selectedIds, setSelectedIds] = useState([]);
  const [decisionLoading, setDecisionLoading] = useState(false);

  // --- Posting Details (history) ---
  const [history, setHistory] = useState([]);
  const [historyAgreementFilter, setHistoryAgreementFilter] = useState("");
  const [historyMonthFilter, setHistoryMonthFilter] = useState("");

  useEffect(() => {
    listAgreements().then(setAgreements).catch(() => setError("Could not load agreements."));
    refreshPending();
    refreshHistory();
  }, []);

  function refreshPending() {
    getPendingRentPostings().then(setPending).catch(() => setError("Could not load the Finance review queue."));
  }

  function refreshHistory(agreementFilter = historyAgreementFilter, monthFilter = historyMonthFilter) {
    getRentPostingHistory(agreementFilter || undefined, monthFilter || undefined)
      .then(setHistory)
      .catch(() => setError("Could not load posting details."));
  }

  async function handleAgreementChange(agreementId) {
    setSelectedAgreement(agreementId);
    setSelectedVendor("");
    setSelectedPeriod("");
    setRentCap(null);
    setVendors([]);
    setPeriods([]);
    if (!agreementId) return;
    try {
      const [agreementDetail, schedule] = await Promise.all([
        getAgreement(agreementId),
        getLeaseSchedule(agreementId).catch(() => null),
      ]);
      setVendors(agreementDetail.allocations.map((a) => a.vendor));
      setPeriods(schedule && schedule.total_periods > 0 ? schedule.periods : []);
    } catch {
      setError("Could not load this agreement's vendors/months.");
    }
  }

  async function handleVendorOrPeriodChange(vendorId, periodNumber) {
    setSelectedVendor(vendorId);
    setSelectedPeriod(periodNumber);
    setRentCap(null);
    if (!vendorId || !periodNumber) return;
    try {
      const data = await getRentCap(selectedAgreement, vendorId, parseInt(periodNumber, 10));
      setRentCap(data.calculated_rent_amount);
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Could not check the rent cap for this month.");
    }
  }

  async function handleSubmitInvoice(e) {
    e.preventDefault();
    setError(null);
    setSubmitSuccess(null);

    if (!file) {
      setError("Attach the invoice file before submitting.");
      return;
    }
    if (rentCap !== null && parseFloat(invoiceAmount) > rentCap) {
      setError(`Invoice amount cannot exceed this vendor's rent for the month (${formatINR(rentCap)}).`);
      return;
    }

    setSubmitting(true);
    try {
      const formData = new FormData();
      formData.append("agreement_id", selectedAgreement);
      formData.append("vendor_id", selectedVendor);
      formData.append("period_number", selectedPeriod);
      formData.append("invoice_amount", invoiceAmount);
      formData.append("submitted_by", submittedBy);
      formData.append("file", file);

      await submitRentInvoice(formData);
      setSubmitSuccess("Invoice submitted for Finance approval.");
      setInvoiceAmount("");
      setFile(null);
      refreshPending();
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Could not submit this invoice.");
    } finally {
      setSubmitting(false);
    }
  }

  function toggleSelect(id) {
    setSelectedIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  }

  function toggleSelectAll() {
    setSelectedIds((prev) => (prev.length === pending.length ? [] : pending.map((p) => p.id)));
  }

  async function handleBulkDecision(approve) {
    if (selectedIds.length === 0) return;
    const decided_by = prompt(approve ? "Approving as (your name):" : "Rejecting as (your name):");
    if (!decided_by) return;

    setDecisionLoading(true);
    setError(null);
    try {
      const result = await bulkDecideRentPostings({ request_ids: selectedIds, decided_by, approve });
      if (result.failed.length > 0) {
        setError(`${result.failed.length} item(s) could not be processed: ${result.failed.map((f) => f.reason).join("; ")}`);
      }
      setSelectedIds([]);
      refreshPending();
      refreshHistory();
    } catch {
      setError("Could not process the selected items.");
    } finally {
      setDecisionLoading(false);
    }
  }

  function handleHistoryAgreementFilter(value) {
    setHistoryAgreementFilter(value);
    refreshHistory(value, historyMonthFilter);
  }

  function handleHistoryMonthFilter(value) {
    setHistoryMonthFilter(value);
    refreshHistory(historyAgreementFilter, value);
  }

  return (
    <div>
      <h1>Rent Posting</h1>
      {error && <div className="error-banner">{error}</div>}

      <fieldset>
        <legend>Submit Invoice — Operational SPOC</legend>
        {submitSuccess && (
          <p style={{ color: "#16a34a", fontSize: 14 }}>{submitSuccess}</p>
        )}
        <form onSubmit={handleSubmitInvoice} className="form-grid">
          <label>
            Agreement *
            <select required value={selectedAgreement} onChange={(e) => handleAgreementChange(e.target.value)}>
              <option value="">Select agreement</option>
              {agreements.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.urn} — {a.agreement_name || "Unnamed"}
                </option>
              ))}
            </select>
          </label>

          <label>
            Vendor *
            <select
              required
              value={selectedVendor}
              onChange={(e) => handleVendorOrPeriodChange(e.target.value, selectedPeriod)}
              disabled={!selectedAgreement}
            >
              <option value="">Select vendor</option>
              {vendors.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.vendor_code} — {v.vendor_name}
                </option>
              ))}
            </select>
          </label>

          <label>
            Month *
            <select
              required
              value={selectedPeriod}
              onChange={(e) => handleVendorOrPeriodChange(selectedVendor, e.target.value)}
              disabled={!selectedAgreement}
            >
              <option value="">Select month</option>
              {periods.map((p) => (
                <option key={p.period_number} value={p.period_number}>
                  {formatMonthYear(p.period_start)}
                </option>
              ))}
            </select>
          </label>

          <label>
            Rent Amount for this month
            <input value={rentCap !== null ? formatINR(rentCap) : ""} readOnly disabled />
          </label>

          <label>
            Invoice Amount *
            <input
              type="number"
              required
              min="0.01"
              step="0.01"
              max={rentCap !== null ? rentCap : undefined}
              value={invoiceAmount}
              onChange={(e) => setInvoiceAmount(e.target.value)}
            />
          </label>

          <label>
            Invoice Attachment *
            <input type="file" required onChange={(e) => setFile(e.target.files[0])} />
          </label>

          <label>
            Submitted By *
            <input required value={submittedBy} onChange={(e) => setSubmittedBy(e.target.value)} />
          </label>

          <div style={{ alignSelf: "flex-end" }}>
            <button type="submit" className="btn-primary" disabled={submitting}>
              {submitting ? "Submitting…" : "Submit Invoice"}
            </button>
          </div>
        </form>
      </fieldset>

      <fieldset>
        <legend>Approve Postings — Finance SPOC</legend>

        {pending.length === 0 ? (
          <p style={{ color: "#64748b", fontSize: 14 }}>No invoices waiting for approval.</p>
        ) : (
          <>
            <div style={{ marginBottom: 12 }}>
              <button type="button" className="btn-secondary" onClick={toggleSelectAll}>
                {selectedIds.length === pending.length ? "Deselect All" : "Select All"}
              </button>
              <button
                type="button"
                className="btn-primary"
                style={{ marginLeft: 8 }}
                onClick={() => handleBulkDecision(true)}
                disabled={selectedIds.length === 0 || decisionLoading}
              >
                {decisionLoading ? "Working…" : `Approve Selected (${selectedIds.length})`}
              </button>
              <button
                type="button"
                className="btn-remove"
                style={{ marginLeft: 8 }}
                onClick={() => handleBulkDecision(false)}
                disabled={selectedIds.length === 0 || decisionLoading}
              >
                Reject Selected
              </button>
            </div>

            <table className="data-table">
              <thead>
                <tr>
                  <th></th>
                  <th>Agreement</th>
                  <th>Vendor</th>
                  <th>Month</th>
                  <th>Rent Cap</th>
                  <th>Invoice Amount</th>
                  <th>Attachment</th>
                  <th>Submitted By</th>
                  <th>Submitted On</th>
                </tr>
              </thead>
              <tbody>
                {pending.map((p) => (
                  <tr key={p.id}>
                    <td>
                      <input
                        type="checkbox"
                        checked={selectedIds.includes(p.id)}
                        onChange={() => toggleSelect(p.id)}
                      />
                    </td>
                    <td>{p.agreement_urn}</td>
                    <td>{p.vendor_name}</td>
                    <td>
                      {p.period_start} → {p.period_end}
                    </td>
                    <td>{formatINR(p.calculated_rent_amount)}</td>
                    <td>{formatINR(p.invoice_amount)}</td>
                    <td>
                      <a href={getRentPostingDownloadUrl(p.id)} download>
                        {p.invoice_file_name}
                      </a>
                    </td>
                    <td>{p.submitted_by}</td>
                    <td>{new Date(p.submitted_on).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}
      </fieldset>

      <fieldset>
        <legend>Posting Details — Rent-wise History</legend>

        <div className="form-grid" style={{ marginBottom: 16 }}>
          <label>
            Filter by Agreement
            <select value={historyAgreementFilter} onChange={(e) => handleHistoryAgreementFilter(e.target.value)}>
              <option value="">All Agreements</option>
              {agreements.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.urn} — {a.agreement_name || "Unnamed"}
                </option>
              ))}
            </select>
          </label>
          <label>
            Filter by Month
            <input type="month" value={historyMonthFilter} onChange={(e) => handleHistoryMonthFilter(e.target.value)} />
          </label>
        </div>

        {history.length === 0 ? (
          <p style={{ color: "#64748b", fontSize: 14 }}>No decided invoices match this filter.</p>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Agreement</th>
                  <th>Property</th>
                  <th>Vendor (this invoice)</th>
                  <th>All Vendors on Agreement</th>
                  <th>Month</th>
                  <th>Invoice Amount</th>
                  <th>Posted Amount</th>
                  <th>Document No.</th>
                  <th>Status</th>
                  <th>Attachment</th>
                  <th>Submitted By</th>
                  <th>Approved By</th>
                  <th>Decided On</th>
                </tr>
              </thead>
              <tbody>
                {history.map((h) => (
                  <tr key={h.id}>
                    <td>
                      {h.agreement_urn}
                      <div style={{ fontSize: 12, color: "#64748b" }}>{h.agreement_name}</div>
                    </td>
                    <td>{h.property_name}</td>
                    <td>{h.vendor_name}</td>
                    <td style={{ fontSize: 12 }}>{h.all_vendors_on_agreement}</td>
                    <td>
                      {h.period_start} → {h.period_end}
                    </td>
                    <td>{formatINR(h.invoice_amount)}</td>
                    <td>{h.posted_amount != null ? formatINR(h.posted_amount) : "—"}</td>
                    <td style={{ fontSize: 12 }}>{h.document_number || "—"}</td>
                    <td>
                      <span
                        className={`status-badge status-${h.status === "Rejected" ? "terminated" : h.status.toLowerCase()}`}
                      >
                        {h.status}
                      </span>
                    </td>
                    <td>
                      <a href={getRentPostingDownloadUrl(h.id)} download>
                        {h.invoice_file_name}
                      </a>
                    </td>
                    <td>{h.submitted_by}</td>
                    <td>{h.approved_by}</td>
                    <td>{h.approved_on ? new Date(h.approved_on).toLocaleDateString() : "—"}</td>
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
