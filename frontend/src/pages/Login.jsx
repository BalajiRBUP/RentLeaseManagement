import { useState } from "react";
import "../styles/login.css";

// Split-screen login page: dark hero panel (left) + sign-in card (right).
// Palette intentionally reuses the app's existing CSS vars (--primary green,
// --accent gold) instead of introducing new colors, so it matches the
// sidebar / logo branding already in use across the app.
export default function Login({ onLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (!email || !password) {
      setError("Please enter both email and password.");
      return;
    }
    setLoading(true);
    try {
      if (onLogin) await onLogin({ email, password });
    } catch (err) {
      setError(err?.message || "Sign in failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-shell">
      {/* Left: hero / brand panel */}
      <div className="login-hero">
        <div className="login-hero-glow" />
        <div className="login-hero-content">
          <div className="login-eyebrow">RENT &amp; IND AS 116 &middot; LEASE LEDGER</div>
          <h1 className="login-headline">
            Track, post, and close the loop on
            <br />
            <span className="login-headline-accent">every lease agreement</span>
          </h1>
          <p className="login-subtext">
            Agreements, amendments, and rent postings run behind every
            journal entry &mdash; from ROU asset to SAP.
          </p>

          <div className="login-pillars">
            <div className="login-pillar">
              <span className="login-pillar-icon login-pillar-icon-primary">&#9670;</span>
              <span>Agreement 360&deg;</span>
            </div>
            <div className="login-pillar">
              <span className="login-pillar-icon login-pillar-icon-accent">&#9671;</span>
              <span>Lease schedule</span>
            </div>
            <div className="login-pillar">
              <span className="login-pillar-icon login-pillar-icon-primary">&#9678;</span>
              <span>SAP handoff</span>
            </div>
          </div>

          <div className="login-flow">
            <div className="login-flow-step">
              <div className="login-flow-title login-flow-title-primary">Agreements</div>
              <div className="login-flow-desc">Onboarding, masters, escalation terms</div>
            </div>
            <div className="login-flow-arrow">&rarr;</div>
            <div className="login-flow-step">
              <div className="login-flow-title login-flow-title-accent">Lease Schedule</div>
              <div className="login-flow-desc">ROU asset, liability, amendments</div>
            </div>
            <div className="login-flow-arrow">&rarr;</div>
            <div className="login-flow-step">
              <div className="login-flow-title login-flow-title-primary">Postings</div>
              <div className="login-flow-desc">Recognition, interest, rent to SAP</div>
            </div>
          </div>

          <div className="login-flow-caption">
            Agreement signed &rarr; schedule computed &rarr; ledger posted
          </div>
        </div>
      </div>

      {/* Right: sign-in card */}
      <div className="login-panel">
        <div className="login-card">
          <div className="login-card-brand">
            <div className="login-card-logo-wrap">
              <img src="/spr-logo.png" alt="SPR Logo" className="login-card-logo" />
            </div>
            <div>
              <div className="login-card-title">Rent &amp; Ind AS 116</div>
            </div>
            <span className="login-card-badge">GMMCO</span>
          </div>

          <form onSubmit={handleSubmit} noValidate>
            <label className="login-field-label" htmlFor="login-email">
              EMAIL
            </label>
            <input
              id="login-email"
              type="email"
              className="login-input"
              placeholder="you@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="username"
            />

            <label className="login-field-label" htmlFor="login-password">
              PASSWORD
            </label>
            <div className="login-input-wrap">
              <input
                id="login-password"
                type={showPassword ? "text" : "password"}
                className="login-input"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
              />
              <button
                type="button"
                className="login-input-icon-btn"
                onClick={() => setShowPassword((s) => !s)}
                aria-label={showPassword ? "Hide password" : "Show password"}
                tabIndex={-1}
              >
                {showPassword ? "🙈" : "👁"}
              </button>
            </div>

            {error && <div className="login-error">{error}</div>}

            <button type="submit" className="login-submit-btn" disabled={loading}>
              {loading ? "Signing in…" : <>Sign in &rarr;</>}
            </button>

            <div className="login-links">
              <a href="#forgot" onClick={(e) => e.preventDefault()}>
                Forgot password?
              </a>
              <a href="#request" onClick={(e) => e.preventDefault()}>
                Request access
              </a>
            </div>
          </form>

          <div className="login-secured-by">
            <span className="login-lock">🔒</span> Secured by SPR Consultech
          </div>
        </div>
      </div>
    </div>
  );
}
