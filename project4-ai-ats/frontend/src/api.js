const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";
async function req(path, opts = {}) {
  const r = await fetch(BASE + path, opts);
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.detail || "Request failed");
  return data;
}
const json = (method, body) => ({ method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
export const api = {
  jobs: () => req("/jobs"),
  createJob: (b) => req("/jobs", json("POST", b)),
  deleteJob: (id) => req(`/jobs/${id}`, { method: "DELETE" }),
  apply: (id, file, name) => { const f = new FormData(); f.append("file", file); if (name) f.append("name", name); return req(`/jobs/${id}/apply`, { method: "POST", body: f }); },
  ranking: (id) => req(`/jobs/${id}/ranking`),
  pipeline: (id) => req(`/jobs/${id}/pipeline`),
  setStage: (id, stage) => req(`/applications/${id}/stage`, json("PATCH", { stage })),
  interviews: () => req("/interviews"),
  schedule: (b) => req("/interviews", json("POST", b)),
  cancel: (id) => req(`/interviews/${id}`, { method: "DELETE" }),
  stats: () => req("/stats"),
};
