import { headers } from "next/headers";

export default async function Home() {
  const h = await headers();
  const email = h.get("x-user-email") || "unknown";
  const appName = process.env.APP_NAME || "test-jrpj";
  const branchName = process.env.BRANCH_NAME || "feature-theme";

  return (
    <div className="container">
      <div className="card">
        <span className="badge">{branchName}</span>
        <h1>{appName}</h1>
        <p className="meta">Authenticated as: {email}</p>
        <p className="meta">Stack: Next.js</p>
      </div>
    </div>
  );
}
