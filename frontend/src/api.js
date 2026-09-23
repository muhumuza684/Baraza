const API_BASE = "http://127.0.0.1:8000";

function getToken() {
  return localStorage.getItem("baraza_token");
}

export async function login(email, password) {
  const body = new URLSearchParams();
  body.append("username", email);
  body.append("password", password);

  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  if (!res.ok) throw new Error("Login failed");
  const data = await res.json();
  localStorage.setItem("baraza_token", data.access_token);
  return data;
}

export async function register(payload) {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Registration failed");
  return res.json();
}

async function authed(path, options = {}) {
  const token = getToken();
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...(options.headers || {}),
      Authorization: `Bearer ${token}`,
    },
  });
  if (!res.ok) throw new Error(`Request failed: ${path}`);
  return res.json();
}

export const getMySubmissions = () => authed("/submissions/mine");
export const getMyTrust = () => authed("/dashboard/me");
export const getProjectDashboard = (projectId) => authed(`/dashboard/project/${projectId}`);
export const submitWork = (taskId, content) =>
  authed("/submissions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ task_id: taskId, content }),
  });

export function logout() {
  localStorage.removeItem("baraza_token");
}

export function isLoggedIn() {
  return !!getToken();
}
