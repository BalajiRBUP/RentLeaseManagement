import { useEffect, useState } from "react";
import { exportToExcel } from "../../utils/exportExcel";

/**
 * Generic list+add+deactivate table for a single master data type.
 * `config` shape:
 *   {
 *     title, idField,
 *     columns: [{ key, label }],
 *     fields: [{ key, label, placeholder }],   // for the add form, in order
 *     list: () => Promise<items>,
 *     create: (payload) => Promise<item>,
 *     remove: (id) => Promise<item>,
 *   }
 */
export default function MasterTable({ config }) {
  const [items, setItems] = useState([]);
  const [form, setForm] = useState(() => Object.fromEntries(config.fields.map((f) => [f.key, ""])));
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  function refresh() {
    config
      .list()
      .then(setItems)
      .catch(() => setError(`Could not load ${config.title.toLowerCase()}.`));
  }

  useEffect(refresh, []); // eslint-disable-line react-hooks/exhaustive-deps

  function updateField(key, value) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function handleAdd(e) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await config.create(form);
      setForm(Object.fromEntries(config.fields.map((f) => [f.key, ""])));
      refresh();
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : `Failed to add ${config.title.toLowerCase()}.`);
    } finally {
      setLoading(false);
    }
  }

  async function handleRemove(id) {
    if (!confirm(`Deactivate this ${config.title.toLowerCase().slice(0, -1)}?`)) return;
    try {
      await config.remove(id);
      refresh();
    } catch {
      setError(`Failed to deactivate.`);
    }
  }

  return (
    <div>
      {error && <div className="error-banner">{error}</div>}

      <fieldset>
        <legend>Add {config.title.slice(0, -1)}</legend>
        <form onSubmit={handleAdd} className="form-grid">
          {config.fields.map((f) => (
            <label key={f.key}>
              {f.label} *
              <input
                required
                value={form[f.key]}
                placeholder={f.placeholder || ""}
                onChange={(e) => updateField(f.key, e.target.value)}
              />
            </label>
          ))}
          <div style={{ alignSelf: "flex-end" }}>
            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? "Adding…" : `Add ${config.title.slice(0, -1)}`}
            </button>
          </div>
        </form>
      </fieldset>

      <fieldset>
        <legend>{config.title}</legend>
        <button
          type="button"
          className="btn-secondary"
          style={{ marginBottom: 12 }}
          onClick={() => {
            const exportRows = items.map((item) => {
              const row = {};
              config.columns.forEach((c) => {
                row[c.label] = item[c.key];
              });
              return row;
            });
            exportToExcel(exportRows, config.title.toLowerCase().replace(/\s+/g, "_"));
          }}
        >
          Export to Excel
        </button>
        <table className="data-table">
          <thead>
            <tr>
              {config.columns.map((c) => (
                <th key={c.key}>{c.label}</th>
              ))}
              <th></th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 && (
              <tr>
                <td colSpan={config.columns.length + 1} className="empty-row">
                  No {config.title.toLowerCase()} yet.
                </td>
              </tr>
            )}
            {items.map((item) => (
              <tr key={item[config.idField]}>
                {config.columns.map((c) => (
                  <td key={c.key}>{item[c.key] || "—"}</td>
                ))}
                <td>
                  <button type="button" className="btn-remove" onClick={() => handleRemove(item[config.idField])}>
                    Deactivate
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </fieldset>
    </div>
  );
}
