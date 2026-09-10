import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { exportAgreements, listAgreements } from "../../api/client";

function formatINR(value) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Number(value) || 0);
}

function csvCell(value) {
  const text = String(value ?? "");
  return `"${text.replaceAll('"', '""')}"`;
}

const EXPORT_COLUMNS = [
  ["Agreement ID", "agreement_id"],
  ["Agreement URN", "agreement_urn"],
  ["Agreement Name", "agreement_name"],
  ["Property ID", "property_id"],
  ["Start Date", "start_date"],
  ["End Date", "end_date"],
  ["Total Rent", "total_rent"],
  ["GST %", "gst_percentage"],
  ["TDS %", "tds_percentage"],
  ["Payment Frequency", "payment_frequency"],
  ["Escalation %", "escalation_percentage"],
  ["Escalation Period", "escalation_period"],
  ["Discount Rate %", "discount_rate"],
  ["Security Deposit", "security_deposit"],
  ["Agreement Status", "agreement_status"],
  ["Created By", "created_by"],
  ["Created On", "created_on"],
  ["Modified By", "modified_by"],
  ["Modified On", "modified_on"],
  ["Amendment ID", "amendment_id"],
  ["Amendment Type", "amendment_type"],
  ["Amendment Effective Date", "amendment_effective_date"],
  ["Amendment Old Value", "amendment_old_value"],
  ["Amendment New Value", "amendment_new_value"],
  ["Amendment Status", "amendment_status"],
  ["Amendment Requested By", "amendment_requested_by"],
  ["Amendment Approved By", "amendment_approved_by"],
  ["Amendment Approved On", "amendment_approved_on"],
  ["Amendment Created On", "amendment_created_on"],
];

export default function AgreementList() {
  const [agreements, setAgreements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    listAgreements()
      .then((data) => setAgreements(data))
      .catch(() => setError("Could not load agreements from the API."))
      .finally(() => setLoading(false));
  }, []);

  async function handleExport() {
    setError(null);

    try {
      const rows = await exportAgreements();

      const csvRows = [
        EXPORT_COLUMNS.map(([label]) => label),
        ...rows.map((row) =>
          EXPORT_COLUMNS.map(([, key]) => row[key])
        ),
      ];

      const csv = `\uFEFF${csvRows
        .map((row) => row.map(csvCell).join(","))
        .join("\r\n")}`;

      const file = new Blob([csv], {
        type: "text/csv;charset=utf-8",
      });

      const url = URL.createObjectURL(file);

      const link = document.createElement("a");
      link.href = url;
      link.download = "Agreements_with_Amendments.csv";
      link.click();

      URL.revokeObjectURL(url);
    } catch (err) {
      const detail = err?.response?.data?.detail;

      setError(
        typeof detail === "string"
          ? detail
          : "Could not export agreements."
      );
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1>Agreements</h1>

        <div>
          <button
            type="button"
            className="btn-secondary"
            onClick={handleExport}
            style={{ marginRight: 10 }}
          >
            Export to Excel
          </button>

          <Link
            to="/agreements/new"
            className="btn-primary"
          >
            + New Agreement
          </Link>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {loading && <div>Loading...</div>}

      {!loading && !error && (
        <table className="data-table">
          <thead>
            <tr>
              <th>URN</th>
              <th>Name</th>
              <th>Start Date</th>
              <th>End Date</th>
              <th style={{ textAlign: "right" }}>Total Rent</th>
              <th>Status</th>
            </tr>
          </thead>

          <tbody>
            {agreements.length === 0 && (
              <tr>
                <td
                  colSpan={6}
                  className="empty-row"
                >
                  No agreements yet. Click "New Agreement"
                  to create the first one.
                </td>
              </tr>
            )}

            {agreements.map((a) => (
              <tr key={a.id}>
                <td>
                  <Link to={`/agreements/${a.id}`}>
                    {a.urn}
                  </Link>
                </td>

                <td>{a.agreement_name || "—"}</td>

                <td>{a.start_date}</td>

                <td>{a.end_date}</td>

                <td className="amount">
                  {formatINR(a.total_rent)}
                </td>

                <td>
                  <span
                    className={`status-badge status-${a.status.toLowerCase()}`}
                  >
                    {a.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}