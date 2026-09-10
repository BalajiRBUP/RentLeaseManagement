import { useState } from "react";
import MasterTable from "./MasterTable";
import {
  getProperties, createProperty, removeProperty,
  getVendors, createVendor, removeVendor,
  getCostCenters, createCostCenter, removeCostCenter,
  getProfitCenters, createProfitCenter, removeProfitCenter,
} from "../../api/client";

const CONFIGS = {
  properties: {
    title: "Properties",
    idField: "id",
    columns: [
      { key: "property_code", label: "Code" },
      { key: "property_name", label: "Name" },
      { key: "location", label: "Location" },
    ],
    fields: [
      { key: "property_code", label: "Property Code", placeholder: "PROP-003" },
      { key: "property_name", label: "Property Name" },
      { key: "location", label: "Location" },
    ],
    list: getProperties,
    create: createProperty,
    remove: removeProperty,
  },
  vendors: {
    title: "Vendors",
    idField: "id",
    columns: [
      { key: "vendor_code", label: "Code" },
      { key: "vendor_name", label: "Name" },
    ],
    fields: [
      { key: "vendor_code", label: "Vendor Code", placeholder: "V-1003" },
      { key: "vendor_name", label: "Vendor Name" },
    ],
    list: getVendors,
    create: createVendor,
    remove: removeVendor,
  },
  costCenters: {
    title: "Cost Centers",
    idField: "id",
    columns: [
      { key: "cost_center_code", label: "Code" },
      { key: "cost_center_text", label: "Description" },
    ],
    fields: [
      { key: "cost_center_code", label: "Cost Center Code", placeholder: "CC-300" },
      { key: "cost_center_text", label: "Description" },
    ],
    list: getCostCenters,
    create: createCostCenter,
    remove: removeCostCenter,
  },
  profitCenters: {
    title: "Profit Centers",
    idField: "id",
    columns: [
      { key: "profit_center_code", label: "Code" },
      { key: "profit_center_text", label: "Description" },
    ],
    fields: [
      { key: "profit_center_code", label: "Profit Center Code", placeholder: "PC-300" },
      { key: "profit_center_text", label: "Description" },
    ],
    list: getProfitCenters,
    create: createProfitCenter,
    remove: removeProfitCenter,
  },
};

const TABS = [
  { key: "properties", label: "Properties" },
  { key: "vendors", label: "Vendors" },
  { key: "costCenters", label: "Cost Centers" },
  { key: "profitCenters", label: "Profit Centers" },
];

export default function MastersView() {
  const [activeTab, setActiveTab] = useState("properties");

  return (
    <div>
      <h1>Masters</h1>

      <div style={{ display: "flex", gap: 8, marginBottom: 20 }}>
        {TABS.map((t) => (
          <button
            key={t.key}
            type="button"
            className={activeTab === t.key ? "btn-primary" : "btn-secondary"}
            style={{ marginTop: 0 }}
            onClick={() => setActiveTab(t.key)}
          >
            {t.label}
          </button>
        ))}
      </div>

      <MasterTable key={activeTab} config={CONFIGS[activeTab]} />
    </div>
  );
}
