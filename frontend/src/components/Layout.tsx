import { Link, NavLink, Outlet } from "react-router-dom";

const linkStyle = (active: boolean) => ({
  padding: "6px 12px",
  borderRadius: 6,
  textDecoration: "none",
  color: active ? "#fff" : "#333",
  background: active ? "#3b5bdb" : "transparent",
});

export function Layout() {
  return (
    <div style={{ fontFamily: "system-ui, sans-serif", color: "#222" }}>
      <header
        style={{
          borderBottom: "1px solid #e5e5e5",
          padding: "0.75rem 1.5rem",
          display: "flex",
          alignItems: "center",
          gap: 16,
        }}
      >
        <Link to="/" style={{ fontWeight: 700, color: "#222", textDecoration: "none" }}>
          LLM Evaluation Lab
        </Link>
        <nav style={{ display: "flex", gap: 4 }}>
          <NavLink to="/" end style={({ isActive }) => linkStyle(isActive)}>
            Dashboard
          </NavLink>
          <NavLink to="/runs/new" style={({ isActive }) => linkStyle(isActive)}>
            New run
          </NavLink>
          <NavLink to="/compare" style={({ isActive }) => linkStyle(isActive)}>
            Compare
          </NavLink>
          <NavLink to="/trends" style={({ isActive }) => linkStyle(isActive)}>
            Trends
          </NavLink>
          <NavLink to="/health" style={({ isActive }) => linkStyle(isActive)}>
            Health
          </NavLink>
        </nav>
      </header>
      <main style={{ padding: "1.5rem", maxWidth: 1100, margin: "0 auto" }}>
        <Outlet />
      </main>
    </div>
  );
}
