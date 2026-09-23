import { useState } from "react";
import Login from "./pages/Login";
import StudentDashboard from "./pages/StudentDashboard";
import InstructorDashboard from "./pages/InstructorDashboard";
import { isLoggedIn, logout } from "./api";

export default function App() {
  const [loggedIn, setLoggedIn] = useState(isLoggedIn());
  const [view, setView] = useState("student");
  const [projectId, setProjectId] = useState("");

  if (!loggedIn) {
    return (
      <div className="wrap">
        <Login onLoggedIn={() => setLoggedIn(true)} />
      </div>
    );
  }

  return (
    <div className="wrap">
      <nav>
        <div>
          <a onClick={() => setView("student")} style={{ marginRight: 16 }}>My view</a>
          <a onClick={() => setView("instructor")}>Instructor view</a>
        </div>
        <a onClick={() => { logout(); setLoggedIn(false); }}>Log out</a>
      </nav>

      {view === "student" && <StudentDashboard />}

      {view === "instructor" && (
        <div>
          <div className="panel">
            <label>Project ID</label>
            <input
              placeholder="paste a project id (see backend/seed.py output)"
              value={projectId}
              onChange={(e) => setProjectId(e.target.value)}
            />
          </div>
          <InstructorDashboard projectId={projectId} />
        </div>
      )}
    </div>
  );
}
