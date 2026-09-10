import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  getProperties,
  getVendors,
  getCostCenters,
  getProfitCenters,
  createAgreement,
} from "../../api/client";
import { formatINR } from "../../utils/formatNumber";

const emptyAllocation = () => ({
  vendor_id: "",
  cost_center_id: "",
  profit_center_id: "",
  split_percentage: "",
});

export default function AgreementForm() {
  const navigate = useNavigate();

  const [properties, setProperties] = useState([]);
  const [vendors, setVendors] = useState([]);
  const [costCenters, setCostCenters] = useState([]);
  const [profitCenters, setProfitCenters] = useState([]);

  const [form, setForm] = useState({
    agreement_name: "",
    property_id: "",
    start_date: "",
    end_date: "",
    total_rent: "",
    gst_percentage: "18",
    tds_percentage: "10",
    payment_frequency: "Monthly",
    escalation_percentage: "0",
    escalation_period: "0",
    discount_rate: "0",
    security_deposit: "0",
    created_by: "",
  });

  const [allocations, setAllocations] = useState([emptyAllocation()]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    Promise.all([getProperties(), getVendors(), getCostCenters(), getProfitCenters()])
      .then(([p, v, cc, pc]) => {
        setProperties(p);
        setVendors(v);
        setCostCenters(cc);
        setProfitCenters(pc);
      })
      .catch(() => setError("Could not load master data (properties/vendors/cost centers)."));
  }, []);

  const totalSplit = useMemo(
    () => allocations.reduce((sum, a) => sum + (parseFloat(a.split_percentage) || 0), 0),
    [allocations]
  );

  const preview = useMemo(() => {
    const totalRent = parseFloat(form.total_rent) || 0;
    const gst = parseFloat(form.gst_percentage) || 0;
    const tds = parseFloat(form.tds_percentage) || 0;

    return allocations.map((a) => {
      const split = parseFloat(a.split_percentage) || 0;
      const rent = (totalRent * split) / 100;
      const gstAmount = (rent * gst) / 100;
      const tdsAmount = (rent * tds) / 100;
      return {
        rent,
        gstAmount,
        tdsAmount,
        netPayable: rent + gstAmount - tdsAmount,
      };
    });
  }, [allocations, form.total_rent, form.gst_percentage, form.tds_percentage]);

  function updateField(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  function updateAllocation(index, field, value) {
    setAllocations((prev) =>
      prev.map((a, i) => (i === index ? { ...a, [field]: value } : a))
    );
  }

  function addAllocationRow() {
    setAllocations((prev) => [...prev, emptyAllocation()]);
  }

  function removeAllocationRow(index) {
    setAllocations((prev) => prev.filter((_, i) => i !== index));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);

    if (Math.abs(totalSplit - 100) > 0.01) {
      setError(`Allocation split must total 100%. Currently: ${totalSplit.toFixed(2)}%`);
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        ...form,
        total_rent: parseFloat(form.total_rent),
        gst_percentage: parseFloat(form.gst_percentage),
        tds_percentage: parseFloat(form.tds_percentage),
        escalation_percentage: parseFloat(form.escalation_percentage),
        escalation_period: parseInt(form.escalation_period, 10),
        discount_rate: parseFloat(form.discount_rate),
        security_deposit: parseFloat(form.security_deposit),
        allocations: allocations.map((a) => ({
          ...a,
          split_percentage: parseFloat(a.split_percentage),
        })),
      };
      const created = await createAgreement(payload);
      navigate(`/agreements/${created.id}`);
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Failed to create agreement. Check the form values.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <h1>New Agreement</h1>
      {error && <div className="error-banner">{error}</div>}

      <form onSubmit={handleSubmit} className="form">
        <fieldset>
          <legend>Agreement Details</legend>

          <div className="form-grid">
            <label>
              Agreement Name
              <input
                value={form.agreement_name}
                onChange={(e) => updateField("agreement_name", e.target.value)}
              />
            </label>

            <label>
              Property *
              <select
                required
                value={form.property_id}
                onChange={(e) => updateField("property_id", e.target.value)}
              >
                <option value="">Select property</option>
                {properties.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.property_code} — {p.property_name}
                  </option>
                ))}
              </select>
            </label>

            <label>
              Start Date *
              <input
                type="date"
                required
                value={form.start_date}
                onChange={(e) => updateField("start_date", e.target.value)}
              />
            </label>

            <label>
              End Date *
              <input
                type="date"
                required
                value={form.end_date}
                onChange={(e) => updateField("end_date", e.target.value)}
              />
            </label>

            <label>
              Total Rent (₹) *
              <input
                type="number"
                required
                min="0"
                step="0.01"
                value={form.total_rent}
                onChange={(e) => updateField("total_rent", e.target.value)}
              />
            </label>

            <label>
              GST %
              <input
                type="number"
                step="0.01"
                value={form.gst_percentage}
                onChange={(e) => updateField("gst_percentage", e.target.value)}
              />
            </label>

            <label>
              TDS %
              <input
                type="number"
                step="0.01"
                value={form.tds_percentage}
                onChange={(e) => updateField("tds_percentage", e.target.value)}
              />
            </label>

            <label>
              Payment Frequency
              <select
                value={form.payment_frequency}
                onChange={(e) => updateField("payment_frequency", e.target.value)}
              >
                <option>Monthly</option>
                <option>Quarterly</option>
                <option>Half-Yearly</option>
                <option>Annually</option>
              </select>
            </label>

            <label>
              Escalation %
              <input
                type="number"
                step="0.01"
                value={form.escalation_percentage}
                onChange={(e) => updateField("escalation_percentage", e.target.value)}
              />
            </label>

            <label>
              Escalation Period (months)
              <input
                type="number"
                value={form.escalation_period}
                onChange={(e) => updateField("escalation_period", e.target.value)}
              />
            </label>

            <label>
              Discount Rate % (IND AS 116)
              <input
                type="number"
                step="0.01"
                value={form.discount_rate}
                onChange={(e) => updateField("discount_rate", e.target.value)}
              />
            </label>

            <label>
              Security Deposit (₹)
              <input
                type="number"
                step="0.01"
                value={form.security_deposit}
                onChange={(e) => updateField("security_deposit", e.target.value)}
              />
            </label>

            <label>
              Created By *
              <input
                required
                value={form.created_by}
                onChange={(e) => updateField("created_by", e.target.value)}
              />
            </label>
          </div>
        </fieldset>

        <fieldset>
          <legend>
            Vendor Allocation Split — total must equal 100% (currently{" "}
            <strong className={Math.abs(totalSplit - 100) > 0.01 ? "split-bad" : "split-good"}>
              {totalSplit.toFixed(2)}%
            </strong>
            )
          </legend>

          <table className="alloc-table">
            <thead>
              <tr>
                <th>Vendor</th>
                <th>Cost Center</th>
                <th>Profit Center</th>
                <th>Split %</th>
                <th>Calc. Rent</th>
                <th>GST</th>
                <th>TDS</th>
                <th>Net Payable</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {allocations.map((a, i) => (
                <tr key={i}>
                  <td>
                    <select
                      required
                      value={a.vendor_id}
                      onChange={(e) => updateAllocation(i, "vendor_id", e.target.value)}
                    >
                      <option value="">Select</option>
                      {vendors.map((v) => (
                        <option key={v.id} value={v.id}>
                          {v.vendor_code} — {v.vendor_name}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td>
                    <select
                      required
                      value={a.cost_center_id}
                      onChange={(e) => updateAllocation(i, "cost_center_id", e.target.value)}
                    >
                      <option value="">Select</option>
                      {costCenters.map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.cost_center_code}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td>
                    <select
                      required
                      value={a.profit_center_id}
                      onChange={(e) => updateAllocation(i, "profit_center_id", e.target.value)}
                    >
                      <option value="">Select</option>
                      {profitCenters.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.profit_center_code}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td>
                    <input
                      type="number"
                      required
                      min="0"
                      max="100"
                      step="0.01"
                      className="split-input"
                      value={a.split_percentage}
                      onChange={(e) => updateAllocation(i, "split_percentage", e.target.value)}
                    />
                  </td>
                  <td>{formatINR(preview[i]?.rent)}</td>
                  <td>{formatINR(preview[i]?.gstAmount)}</td>
                  <td>{formatINR(preview[i]?.tdsAmount)}</td>
                  <td>{formatINR(preview[i]?.netPayable)}</td>
                  <td>
                    {allocations.length > 1 && (
                      <button type="button" className="btn-remove" onClick={() => removeAllocationRow(i)}>
                        ✕
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <button type="button" className="btn-secondary" onClick={addAllocationRow}>
            + Add Vendor Split
          </button>
        </fieldset>

        <div className="form-actions">
          <button type="submit" className="btn-primary" disabled={submitting}>
            {submitting ? "Saving…" : "Create Agreement"}
          </button>
        </div>
      </form>
    </div>
  );
}
