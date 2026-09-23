import { useEffect, useState } from "react";
import { getProjectDashboard } from "../api";

function barColor(pct) {
  if (pct >= 80) return "var(--accent2)";
  if (pct >= 50) return "var(--accent)";
  return "var(--danger)";
}

export default function InstructorDashboard({ projectId }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!projectId) return;
    getProjectDashboard(projectId)
      .then(setData)
      .catch(() => setError("Could not load dashboard. Check the project ID and that you're logged in as lecturer/admin."));
  }, [projectId]);

  if (error) return <div className="panel error">{error}</div>;
  if (!data) return <div className="panel sub">Loading…</div>;

  return (
    <div className="panel">
      <h1>{data.title}</h1>
      <p className="sub">Verified contribution share per student</p>
      {data.students.map((s) => (
        <div key={s.student_id} style={{ marginBottom: 14 }}>
          <div className="row" style={{ border: "none", padding: "0 0 4px" }}>
            <span>{s.student_name}</span>
            <span>{s.contribution_share_pct}% &middot; trust {s.trust_mean}</span>
          </div>
          <div className="bar-track">
            <div
              className="bar-fill"
              style={{ width: `${s.contribution_share_pct}%`, background: barColor(s.contribution_share_pct) }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
