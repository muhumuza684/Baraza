import { useState } from "react";
import { login } from "../api";

export default function Login({ onLoggedIn }) {
  const [email, setEmail] = useState("bright@must.ac.ug");
  const [password, setPassword] = useState("password123");
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    try {
      await login(email, password);
      onLoggedIn();
    } catch (err) {
      setError("Login failed. Check email/password, and that the API is running.");
    }
  }

  return (
    <div className="panel">
      <h1>Baraza</h1>
      <p className="sub">Sign in. Try the seeded demo accounts below.</p>
      {error && <div className="error">{error}</div>}
      <form onSubmit={handleSubmit}>
        <label>Email</label>
        <input value={email} onChange={(e) => setEmail(e.target.value)} />
        <label>Password</label>
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
        <button type="submit">Log in</button>
      </form>
      <p className="sub" style={{ marginTop: 16 }}>
        Demo: bright@must.ac.ug / password123 (student) &middot; lecturer@must.ac.ug / password123 (lecturer)
      </p>
    </div>
  );
}
