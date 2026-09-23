import { useEffect, useState } from "react";
import { getMySubmissions, getMyTrust } from "../api";

function statusPill(status) {
  if (status === "on_time") return <span className="pill p-ok">on time</span>;
  if (status === "late") return <span className="pill p-warn">late</span>;
  if (status === "missed") return <span className="pill p-risk">missed</span>;
  return <span className="pill p-risk">disputed</span>;
}

export default function StudentDashboard() {
  const [submissions, setSubmissions] = useState([]);
  const [trust, setTrust] = useState([]);

  useEffect(() => {
    getMySubmissions().then(setSubmissions).catch(() => {});
    getMyTrust().then(setTrust).catch(() => {});
  }, []);

  return (
    <div>
      <div className="panel">
        <h1>My submissions</h1>
        {submissions.length === 0 && <p className="sub">No submissions yet.</p>}
        {submissions.map((s) => (
          <div className="row" key={s.id}>
            <span>Task {s.task_id.slice(0, 8)}…</span>
            {statusPill(s.status)}
          </div>
        ))}
      </div>

      <div className="panel">
        <h1>My trust score</h1>
        {trust.length === 0 && <p className="sub">No trust record yet &mdash; submit something first.</p>}
        {trust.map((t) => (
          <div key={t.project_id} style={{ marginBottom: 14 }}>
            <div style={{ fontSize: "1.6rem", fontWeight: 700 }}>
              {t.trust_mean} <span className="sub" style={{ fontSize: ".8rem" }}>± {t.trust_confidence_width}</span>
            </div>
            <p className="sub">
              current state: {t.current_state} &middot; audit probability: {(t.audit_probability * 100).toFixed(0)}%
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
