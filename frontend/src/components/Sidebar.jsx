import { NavLink } from "react-router-dom";

// Matches the target architecture agreed in planning: one app, one nav,
// covering Rent + Lease instead of two separate Power Apps.
const NAV_ITEMS = [
  { to: "/", label: "Dashboard", enabled: true, icon: "grid" },
  { to: "/agreements", label: "Agreements", enabled: true, icon: "file" },
  { to: "/masters", label: "Masters", enabled: true, icon: "layers" },
  { to: "/lease", label: "Lease Schedule", enabled: true, icon: "calendar" },
  { to: "/amendments", label: "Amendments", enabled: true, icon: "edit" },
  { to: "/reports", label: "Reports", enabled: true, icon: "chart" },
  { to: "/rent-posting", label: "Rent Posting", enabled: true, icon: "send" },
];

const ICONS = {
  grid: (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6">
      <rect x="2.5" y="2.5" width="6" height="6" rx="1.2" />
      <rect x="11.5" y="2.5" width="6" height="6" rx="1.2" />
      <rect x="2.5" y="11.5" width="6" height="6" rx="1.2" />
      <rect x="11.5" y="11.5" width="6" height="6" rx="1.2" />
    </svg>
  ),
  file: (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6">
      <path d="M5 2.5h6.5L15 6v11.5H5z" strokeLinejoin="round" />
      <path d="M11.5 2.5V6H15" strokeLinejoin="round" />
      <path d="M7.3 10h5.4M7.3 12.6h5.4M7.3 15.2h3.2" strokeLinecap="round" />
    </svg>
  ),
  layers: (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6">
      <path d="M10 2.7 17.2 7 10 11.3 2.8 7z" strokeLinejoin="round" />
      <path d="M2.8 10.6 10 14.9l7.2-4.3" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M2.8 14.2 10 18.5l7.2-4.3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  calendar: (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6">
      <rect x="2.5" y="4" width="15" height="13.5" rx="1.5" />
      <path d="M2.5 8h15M6.3 2.3v3.4M13.7 2.3v3.4" strokeLinecap="round" />
    </svg>
  ),
  edit: (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6">
      <path d="M12.4 3.3 16.7 7.6 6.6 17.7 2 18.2l.6-4.7z" strokeLinejoin="round" strokeLinecap="round" />
      <path d="M10.6 5.1 14.9 9.4" strokeLinecap="round" />
    </svg>
  ),
  chart: (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6">
      <path d="M3 17.5h14" strokeLinecap="round" />
      <rect x="4.3" y="10" width="3" height="6.2" rx="0.6" />
      <rect x="8.7" y="6.4" width="3" height="9.8" rx="0.6" />
      <rect x="13.1" y="2.8" width="3" height="13.4" rx="0.6" />
    </svg>
  ),
  send: (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6">
      <path d="M17.5 2.5 2.5 8.7l6 2.6 2.6 6z" strokeLinejoin="round" strokeLinecap="round" />
      <path d="M17.5 2.5 8.7 11.3" strokeLinecap="round" />
    </svg>
  ),
};

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-glow" aria-hidden="true" />

      <div className="sidebar-brand">
        <div className="sidebar-logo-wrap">
          <img src="/spr-logo.png" alt="SPR Logo" className="sidebar-logo" />
        </div>
        <div className="sidebar-product-name">Rent &amp; Ind AS 116</div>
        <div className="sidebar-product-subtitle">Management &middot; SPR</div>
      </div>

      <nav>
        {NAV_ITEMS.map((item) =>
          item.enabled ? (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) => "nav-item" + (isActive ? " active" : "")}
            >
              <span className="nav-item-icon">{ICONS[item.icon]}</span>
              <span className="nav-item-label">{item.label}</span>
            </NavLink>
          ) : (
            <span key={item.to} className="nav-item disabled" title="Coming in a future sprint">
              <span className="nav-item-icon">{ICONS[item.icon]}</span>
              <span className="nav-item-label">{item.label}</span>
            </span>
          )
        )}
      </nav>

      <div className="sidebar-foot">
        <span className="sidebar-foot-dot" />
        Secured by SPR Consultech
      </div>
    </aside>
  );
}
