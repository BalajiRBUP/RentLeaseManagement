import { useEffect, useState } from "react";
import {
  listAgreements,
  getAgreement,
  generateLeaseSchedule,
  getLeaseSchedule,
  postLeaseSchedulePeriod,
  postRecognition,
  getPostingFilter,
  postPostingEntry,
  postInterestAndDepreciation,
} from "../../api/client";
import { formatMonthYear } from "../../utils/formatDate";
import { exportToExcel } from "../../utils/exportExcel";

function formatINR(value) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  }).format(value || 0);
}

export default function LeaseScheduleView() {
  const [agreements, setAgreements] = useState([]);
  const [selectedId, setSelectedId] = useState("");
  const [selectedUrn, setSelectedUrn] = useState("");
  const [schedule, setSchedule] = useState(null);
  const [vendors, setVendors] = useState([]); // from agreement's allocations
  const [loading, setLoading] = useState(false);
  const [postingId, setPostingId] = useState(null);
  const [recognitionPosting, setRecognitionPosting] = useState(false);
  const [error, setError] = useState(null);

  // Filter state
  const [filterPeriod, setFilterPeriod] = useState("");
  const [filterVendor, setFilterVendor] = useState("");
  const [filterData, setFilterData] = useState(null);
  const [filterLoading, setFilterLoading] = useState(false);
  const [postingType, setPostingType] = useState(null);

  useEffect(() => {
    listAgreements().then(setAgreements).catch(() => setError("Could not load agreements."));
  }, []);

  async function loadExisting(agreementId) {
    setSelectedId(agreementId);
    const agr = agreements.find((a) => a.id === agreementId);
    setSelectedUrn(agr ? agr.urn : "");
    setSchedule(null);
    setVendors([]);
    setFilterPeriod("");
    setFilterVendor("");
    setFilterData(null);
    setError(null);
    if (!agreementId) return;
    setLoading(true);
    try {
      const [data, agreementDetail] = await Promise.all([getLeaseSchedule(agreementId), getAgreement(agreementId)]);
      setSchedule(data.total_periods > 0 ? data : null);
      setVendors(agreementDetail.allocations.map((a) => a.vendor));
    } catch {
      setSchedule(null);
    } finally {
      setLoading(false);
    }
  }

  async function refreshSchedule() {
    const data = await getLeaseSchedule(selectedId);
    setSchedule(data.total_periods > 0 ? data : null);
  }

  async function handleGenerate() {
    if (!selectedId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await generateLeaseSchedule(selectedId);
      setSchedule(data);
      const agreementDetail = await getAgreement(selectedId);
      setVendors(agreementDetail.allocations.map((a) => a.vendor));
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Could not generate schedule. Check the agreement's dates/discount rate.");
    } finally {
      setLoading(false);
    }
  }

  async function handlePostRecognition() {
    setRecognitionPosting(true);
    setError(null);
    try {
      await postRecognition(selectedId);
      await refreshSchedule();
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Could not post recognition.");
    } finally {
      setRecognitionPosting(false);
    }
  }

  async function handlePostPeriod(periodId) {
    setPostingId(periodId);
    setError(null);
    try {
      await postLeaseSchedulePeriod(periodId);
      await refreshSchedule();
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Could not post this period.");
    } finally {
      setPostingId(null);
    }
  }

  async function runFilter(periodNumber, vendorId) {
    if (!periodNumber || !vendorId) {
      setFilterData(null);
      return;
    }
    setFilterLoading(true);
    setError(null);
    try {
      const data = await getPostingFilter(selectedId, periodNumber, vendorId);
      setFilterData(data);
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Could not load posting data for this month/vendor.");
      setFilterData(null);
    } finally {
      setFilterLoading(false);
    }
  }

  function handleFilterPeriodChange(value) {
    setFilterPeriod(value);
    runFilter(value ? parseInt(value, 10) : "", filterVendor);
  }

  function handleFilterVendorChange(value) {
    setFilterVendor(value);
    runFilter(filterPeriod ? parseInt(filterPeriod, 10) : "", value);
  }

  async function handlePostEntry(type) {
    setPostingType(type);
    setError(null);
    try {
      await postPostingEntry({
        agreement_id: selectedId,
        vendor_id: filterVendor,
        period_number: parseInt(filterPeriod, 10),
        posting_type: type,
      });
      await runFilter(parseInt(filterPeriod, 10), filterVendor);
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : `Could not post ${type}.`);
    } finally {
      setPostingType(null);
    }
  }

  async function handlePostInterestDepreciation() {
    setPostingType("Interest+Depreciation");
    setError(null);
    try {
      await postInterestAndDepreciation({
        agreement_id: selectedId,
        vendor_id: filterVendor,
        period_number: parseInt(filterPeriod, 10),
      });
      await runFilter(parseInt(filterPeriod, 10), filterVendor);
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Could not post Interest and Depreciation.");
    } finally {
      setPostingType(null);
    }
  }

  function handleExport() {
    if (!schedule) return;
    const rows = schedule.periods.map((p) => ({
      "Period #": p.period_number,
      "Period Start": p.period_start,
      "Period End": p.period_end,
      "Opening Liability": p.opening_liability,
      Interest: p.interest_expense,
      "Rent Payment": p.lease_payment,
      "Closing Liability": p.closing_liability,
      "Opening ROU": p.opening_rou,
      Depreciation: p.depreciation,
      "Closing ROU": p.closing_rou,
      Status: p.status,
      "Posted On": p.posted_on || "",
    }));
    exportToExcel(rows, `lease_schedule_${selectedUrn || "agreement"}`);
  }

  return (
    <div>
      <h1>Lease Schedule (IND AS 116)</h1>
      {error && <div className="error-banner">{error}</div>}

      <fieldset>
        <legend>Select Agreement</legend>
        <div className="form-grid">
          <label>
            Agreement
            <select value={selectedId} onChange={(e) => loadExisting(e.target.value)}>
              <option value="">Select an agreement</option>
              {agreements.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.urn} — {a.agreement_name || "Unnamed"}
                </option>
              ))}
            </select>
          </label>
        </div>

        {selectedId && (
          <button type="button" className="btn-primary" style={{ marginTop: 16 }} onClick={handleGenerate} disabled={loading}>
            {loading ? "Working…" : schedule ? "Regenerate Schedule" : "Generate Schedule"}
          </button>
        )}
        {selectedId && schedule && (
          <p style={{ fontSize: 13, color: "#64748b", marginTop: 8 }}>
            Regenerating keeps periods before the latest approved amendment's effective date untouched.
          </p>
        )}
      </fieldset>

      {schedule && (
        <>
          <fieldset>
            <legend>Recognition — one-time entry (Dr ROU Asset / Cr Lease Liability)</legend>
            <div className="card-grid">
              <div className="card">
                <div className="card-label">Recognition Amount</div>
                <div className="card-value">{formatINR(schedule.recognition_amount)}</div>
              </div>
              <div className="card">
                <div className="card-label">Status</div>
                <div className="card-value">
                  <span className={`status-badge status-${(schedule.recognition_status || "").toLowerCase().replace(" ", "")}`}>
                    {schedule.recognition_status}
                  </span>
                </div>
                {schedule.recognition_posted_on && (
                  <div style={{ fontSize: 11, color: "#64748b", marginTop: 4 }}>
                    {new Date(schedule.recognition_posted_on).toLocaleDateString()}
                  </div>
                )}
              </div>
            </div>
            {schedule.recognition_status !== "Posted" && (
              <button
                type="button"
                className="btn-primary"
                style={{ marginTop: 12 }}
                onClick={handlePostRecognition}
                disabled={recognitionPosting}
              >
                {recognitionPosting ? "Posting…" : "Post Recognition"}
              </button>
            )}
          </fieldset>

          <fieldset>
            <legend>Filter — post Interest, Depreciation, Rent by month and vendor</legend>
            <div className="form-grid">
              <label>
                Month
                <select value={filterPeriod} onChange={(e) => handleFilterPeriodChange(e.target.value)}>
                  <option value="">Select month</option>
                  {schedule.periods.map((p) => (
                    <option key={p.period_number} value={p.period_number}>
                      {formatMonthYear(p.period_start)}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Vendor
                <select value={filterVendor} onChange={(e) => handleFilterVendorChange(e.target.value)}>
                  <option value="">Select vendor</option>
                  {vendors.map((v) => (
                    <option key={v.id} value={v.id}>
                      {v.vendor_code} — {v.vendor_name}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            {filterLoading && <div style={{ marginTop: 12 }}>Loading…</div>}

            {filterData && !filterLoading && (
              <div style={{ marginTop: 16, overflowX: "auto" }}>
                <p style={{ fontSize: 13, color: "#64748b" }}>
                  FY start: {filterData.fy_start} · YTD is cumulative from FY start through the selected month.
                  Interest and Depreciation post together as one action; Rent posts independently.
                </p>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Posting Type</th>
                      <th>This Month</th>
                      <th>YTD Amount</th>
                      <th>Document No.</th>
                      <th>Status</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    {["Interest", "Depreciation", "Rent"].map((type, idx) => {
                      const entry = filterData.entries[type];
                      const isCombinedRow = type === "Interest" || type === "Depreciation";
                      const interestEntry = filterData.entries["Interest"];
                      const depreciationEntry = filterData.entries["Depreciation"];
                      const bothCombinedPosted = interestEntry.posted && depreciationEntry.posted;

                      return (
                        <tr key={type}>
                          <td>{type}</td>
                          <td>{formatINR(entry.period_amount)}</td>
                          <td>
                            {/* Visible as a plain view field before posting too - shows the
                                live YTD figure. Once posted, shows the frozen amount actually
                                recorded at posting time (won't drift if the schedule changes later). */}
                            <strong>{formatINR(entry.posted ? entry.posted_amount : entry.ytd_amount)}</strong>
                          </td>
                          <td style={{ fontSize: 12 }}>{entry.document_number || "—"}</td>
                          <td>
                            {entry.posted ? (
                              <>
                                <span className="status-badge status-approved">Posted</span>
                                <div style={{ fontSize: 11, color: "#64748b" }}>
                                  {entry.posted_on ? new Date(entry.posted_on).toLocaleDateString() : ""}
                                </div>
                              </>
                            ) : (
                              <span className="status-badge status-draft">Not Posted</span>
                            )}
                          </td>
                          <td>
                            {isCombinedRow ? (
                              // One shared button for Interest + Depreciation - only render it
                              // once, on the first (Interest) row, spanning both conceptually.
                              type === "Interest" &&
                              !bothCombinedPosted && (
                                <button
                                  type="button"
                                  className="btn-secondary"
                                  onClick={handlePostInterestDepreciation}
                                  disabled={postingType === "Interest+Depreciation"}
                                >
                                  {postingType === "Interest+Depreciation" ? "Posting…" : "Post Interest + Depreciation"}
                                </button>
                              )
                            ) : (
                              !entry.posted && (
                                <button
                                  type="button"
                                  className="btn-secondary"
                                  onClick={() => handlePostEntry(type)}
                                  disabled={postingType === type}
                                >
                                  {postingType === type ? "Posting…" : "Post"}
                                </button>
                              )
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </fieldset>

          <fieldset>
            <legend>Summary</legend>
            <div className="card-grid">
              <div className="card">
                <div className="card-label">Initial Lease Liability</div>
                <div className="card-value">{formatINR(schedule.initial_liability)}</div>
              </div>
              <div className="card">
                <div className="card-label">Initial ROU Asset</div>
                <div className="card-value">{formatINR(schedule.initial_rou)}</div>
              </div>
              <div className="card">
                <div className="card-label">Total Interest</div>
                <div className="card-value">{formatINR(schedule.total_interest)}</div>
              </div>
              <div className="card">
                <div className="card-label">Total Depreciation</div>
                <div className="card-value">{formatINR(schedule.total_depreciation)}</div>
              </div>
              <div className="card">
                <div className="card-label">Total Periods</div>
                <div className="card-value">{schedule.total_periods}</div>
              </div>
            </div>
          </fieldset>

          <fieldset>
            <legend>Full Monthly Schedule</legend>
            <button type="button" className="btn-secondary" style={{ marginBottom: 12 }} onClick={handleExport}>
              Export to Excel
            </button>
            <div style={{ overflowX: "auto" }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Period</th>
                    <th>Opening Liability</th>
                    <th>Interest</th>
                    <th>Rent Payment</th>
                    <th>Closing Liability</th>
                    <th>Opening ROU</th>
                    <th>Depreciation</th>
                    <th>Closing ROU</th>
                    <th>Status</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {schedule.periods.map((p) => (
                    <tr key={p.id}>
                      <td>{p.period_number}</td>
                      <td>
                        {p.period_start} → {p.period_end}
                      </td>
                      <td>{formatINR(p.opening_liability)}</td>
                      <td>{formatINR(p.interest_expense)}</td>
                      <td>{formatINR(p.lease_payment)}</td>
                      <td>{formatINR(p.closing_liability)}</td>
                      <td>{formatINR(p.opening_rou)}</td>
                      <td>{formatINR(p.depreciation)}</td>
                      <td>{formatINR(p.closing_rou)}</td>
                      <td>
                        <span className={`status-badge status-${p.status.toLowerCase()}`}>{p.status}</span>
                        {p.posted_on && (
                          <div style={{ fontSize: 11, color: "#64748b" }}>{new Date(p.posted_on).toLocaleDateString()}</div>
                        )}
                      </td>
                      <td>
                        {p.status !== "Posted" && (
                          <button
                            type="button"
                            className="btn-secondary"
                            onClick={() => handlePostPeriod(p.id)}
                            disabled={postingId === p.id}
                          >
                            {postingId === p.id ? "Posting…" : "Close Period"}
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </fieldset>
        </>
      )}
    </div>
  );
}
