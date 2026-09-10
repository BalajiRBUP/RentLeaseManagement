import { useEffect, useState } from "react";
import {
  listAgreements,
  getAmendmentTypes,
  listAmendments,
  createAmendmentRequest,
  decideAmendment,
  postAmendment,
} from "../../api/client";

const DATE_TYPES = new Set(["End Date Change", "Full Termination"]);
const INT_TYPES = new Set(["Escalation Period Change"]);

export default function AmendmentsView() {
  const [agreements, setAgreements] = useState([]);
  const [selectedId, setSelectedId] = useState("");
  const [types, setTypes] = useState([]);
  const [amendments, setAmendments] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const [form, setForm] = useState({
    amendment_type: "",
    effective_date: "",
    new_value: "",
    requested_by: "",
  });

  useEffect(() => {
    listAgreements().then(setAgreements).catch(() => setError("Could not load agreements."));
    getAmendmentTypes().then(setTypes).catch(() => {});
  }, []);

  function refreshAmendments(agreementId) {
    if (!agreementId) return;
    listAmendments(agreementId)
      .then(setAmendments)
      .catch(() => setError("Could not load amendment history."));
  }

  function handleSelectAgreement(agreementId) {
    setSelectedId(agreementId);
    setAmendments([]);
    setError(null);
    refreshAmendments(agreementId);
  }

  function updateField(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await createAmendmentRequest({ ...form, agreement_id: selectedId });
      setForm({ amendment_type: "", effective_date: "", new_value: "", requested_by: form.requested_by });
      refreshAmendments(selectedId);
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Failed to create amendment request.");
    } finally {
      setLoading(false);
    }
  }

  async function handleDecision(amendmentId, approve) {
    const decided_by = prompt(approve ? "Approving as (your name):" : "Rejecting as (your name):");
    if (!decided_by) return;
    setError(null);
    try {
      await decideAmendment(amendmentId, { decided_by, approve });
      refreshAmendments(selectedId);
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Failed to record decision.");
    }
  }

  async function handlePost(amendmentId) {
    setError(null);
    try {
      await postAmendment(amendmentId);
      refreshAmendments(selectedId);
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Failed to post this amendment.");
    }
  }

  const newValueInputType = DATE_TYPES.has(form.amendment_type)
    ? "date"
    : INT_TYPES.has(form.amendment_type)
    ? "number"
    : "text";

  return (
    <div>
      <h1>Amendments</h1>
      {error && <div className="error-banner">{error}</div>}

      <fieldset>
        <legend>Select Agreement</legend>
        <div className="form-grid">
          <label>
            Agreement
            <select value={selectedId} onChange={(e) => handleSelectAgreement(e.target.value)}>
              <option value="">Select an agreement</option>
              {agreements.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.urn} — {a.agreement_name || "Unnamed"}
                </option>
              ))}
            </select>
          </label>
        </div>
      </fieldset>

      {selectedId && (
        <>
          <fieldset>
            <legend>Request New Amendment</legend>
            <form onSubmit={handleSubmit} className="form-grid">
              <label>
                Amendment Type *
                <select
                  required
                  value={form.amendment_type}
                  onChange={(e) => updateField("amendment_type", e.target.value)}
                >
                  <option value="">Select type</option>
                  {types.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </label>

              <label>
                Effective Date *
                <input
                  type="date"
                  required
                  value={form.effective_date}
                  onChange={(e) => updateField("effective_date", e.target.value)}
                />
              </label>

              <label>
                New Value *{" "}
                {form.amendment_type === "Full Termination" && "(termination date)"}
                <input
                  type={newValueInputType}
                  required
                  value={form.new_value}
                  onChange={(e) => updateField("new_value", e.target.value)}
                  placeholder={
                    form.amendment_type === "Rent Increase" || form.amendment_type === "Rent Reduction"
                      ? "New total rent, e.g. 125000"
                      : form.amendment_type === "Discounting Rate Change"
                      ? "New discount rate %, e.g. 10.5"
                      : form.amendment_type === "Escalation Percentage Change"
                      ? "New escalation %, e.g. 7"
                      : ""
                  }
                />
              </label>

              <label>
                Requested By *
                <input
                  required
                  value={form.requested_by}
                  onChange={(e) => updateField("requested_by", e.target.value)}
                />
              </label>

              <div style={{ alignSelf: "flex-end" }}>
                <button type="submit" className="btn-primary" disabled={loading}>
                  {loading ? "Submitting…" : "Submit Amendment"}
                </button>
              </div>
            </form>
          </fieldset>

          <fieldset>
            <legend>Amendment History</legend>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Type</th>
                  <th>Effective Date</th>
                  <th>Old Value</th>
                  <th>New Value</th>
                  <th>Status</th>
                  <th>Requested By</th>
                  <th>Approved By</th>
                  <th>Posting Amount (SAP)</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {amendments.length === 0 && (
                  <tr>
                    <td colSpan={9} className="empty-row">
                      No amendments yet for this agreement.
                    </td>
                  </tr>
                )}
                {amendments.map((a) => (
                  <tr key={a.id}>
                    <td>{a.amendment_type}</td>
                    <td>{a.effective_date}</td>
                    <td>{a.old_value}</td>
                    <td>{a.new_value}</td>
                    <td>
                      <span className={`status-badge status-${a.status.toLowerCase()}`}>{a.status}</span>
                    </td>
                    <td>{a.requested_by}</td>
                    <td>{a.approved_by || "—"}</td>
                    <td>
                      {a.posting_amount != null
                        ? new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR" }).format(a.posting_amount)
                        : "—"}
                      {a.posting_status === "Posted" && (
                        <div style={{ fontSize: 11, color: "#64748b" }}>
                          Posted {a.posted_on ? new Date(a.posted_on).toLocaleDateString() : ""}
                        </div>
                      )}
                    </td>
                    <td>
                      {a.status === "Pending" && (
                        <>
                          <button
                            type="button"
                            className="btn-secondary"
                            style={{ marginRight: 8 }}
                            onClick={() => handleDecision(a.id, true)}
                          >
                            Approve
                          </button>
                          <button type="button" className="btn-remove" onClick={() => handleDecision(a.id, false)}>
                            Reject
                          </button>
                        </>
                      )}
                      {a.status === "Approved" && a.posting_amount != null && a.posting_status !== "Posted" && (
                        <button type="button" className="btn-secondary" onClick={() => handlePost(a.id)}>
                          Post
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </fieldset>
        </>
      )}
    </div>
  );
}
