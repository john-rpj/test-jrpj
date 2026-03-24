import { headers } from "next/headers";

export default async function Home() {
  const h = await headers();
  const email = h.get("x-user-email") || "unknown";
  const appName = process.env.APP_NAME || "test-jrpj";
  const branchName = process.env.BRANCH_NAME || "feature-widget";

  return (
    <div className="container">
      <div className="card">
        <span className="badge">{branchName}</span>
        <h1>{appName}</h1>
        <p className="meta">Authenticated as: {email}</p>
        <p className="meta">Stack: Next.js</p>
      </div>

      <div className="stats">
        <div className="stat-card">
          <div className="stat-value">142</div>
          <div className="stat-label">Active Users</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">$12.4k</div>
          <div className="stat-label">Revenue</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">98.5%</div>
          <div className="stat-label">Uptime</div>
        </div>
      </div>
    </div>
  );
}
