import Sidebar from "./Sidebar";
import ChatWidget from "./ChatWidget";
import { useTheme } from "../hooks/useTheme";

export default function Layout({ children }) {
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="app-shell">
      <Sidebar />
      <main className="content">
        <div className="theme-toggle-wrap">
          <button
            type="button"
            className="theme-toggle-btn"
            onClick={toggleTheme}
            title={theme === "light" ? "Switch to dark mode" : "Switch to light mode"}
          >
            {theme === "light" ? "🌙 Dark" : "☀️ Light"}
          </button>
        </div>
        {children}
      </main>
      <ChatWidget />
    </div>
  );
}
