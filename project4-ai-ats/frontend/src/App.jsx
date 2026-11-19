import { useEffect, useState, useCallback } from "react";
import { api } from "./api";

const STAGES = ["Applied", "Screening", "Interview", "Offer", "Hired", "Rejected"];
const scoreColor = (s) => (s >= 70 ? "#16a34a" : s >= 40 ? "#d97706" : "#dc2626");

export default function App() {
  const [tab, setTab] = useState("jobs");
  const [jobs, setJobs] = useState([]);
  const [jobId, setJobId] = useState(null);
  const [stats, setStats] = useState(null);
  const [err, setErr] = useState("");

  const loadJobs = useCallback(async () => {
    try {
      const j = await api.jobs(); setJobs(j);
      setJobId((cur) => cur ?? j[0]?.id ?? null);
      setStats(await api.stats());
    } catch (e) { setErr(e.message); }
  }, []);
  useEffect(() => { loadJobs(); }, [loadJobs]);

  return (
    <div className="app">
      <header>
        <h1>🎯 AI Recruitment ATS</h1>
        <nav>{["jobs", "candidates", "pipeline", "interviews"].map((t) => (
          <button key={t} className={tab === t ? "on" : ""} onClick={() => setTab(t)}>{t}</button>))}</nav>
        {tab !== "jobs" && tab !== "interviews" && (
          <select value={jobId ?? ""} onChange={(e) => setJobId(+e.target.value)}>
            {jobs.map((j) => <option key={j.id} value={j.id}>{j.title}</option>)}
          </select>)}
      </header>
      {err && <div className="err" onClick={() => setErr("")}>{err} ✕</div>}
      {stats && (
        <div className="stats">
          <div><b>{stats.jobs}</b>Open jobs</div><div><b>{stats.applications}</b>Applications</div>
          <div><b>{stats.avg_score}</b>Avg match score</div><div><b>{stats.by_stage.Hired}</b>Hired</div>
        </div>)}
      {tab === "jobs" && <Jobs jobs={jobs} reload={loadJobs} setErr={setErr} />}
      {tab === "candidates" && jobId && <Candidates jobId={jobId} setErr={setErr} reload={loadJobs} />}
      {tab === "pipeline" && jobId && <Pipeline jobId={jobId} setErr={setErr} />}
      {tab === "interviews" && <Interviews jobs={jobs} setErr={setErr} />}
      {tab !== "jobs" && tab !== "interviews" && !jobId && <p>Create a job first.</p>}
    </div>
  );
}

function Jobs({ jobs, reload, setErr }) {
  const [f, setF] = useState({ title: "", description: "", skills: "" });
  const submit = async (e) => {
    e.preventDefault();
    try {
      await api.createJob({ title: f.title, description: f.description, required_skills: f.skills.split(",") });
      setF({ title: "", description: "", skills: "" }); reload();
    } catch (x) { setErr(x.message); }
  };
  return (
    <div className="grid2">
      <form className="card" onSubmit={submit}>
        <h3>New job</h3>
        <input required placeholder="Job title" value={f.title} onChange={(e) => setF({ ...f, title: e.target.value })} />
        <textarea required rows={6} placeholder="Job description" value={f.description} onChange={(e) => setF({ ...f, description: e.target.value })} />
        <input placeholder="Required skills (comma separated, blank = auto-detect)" value={f.skills} onChange={(e) => setF({ ...f, skills: e.target.value })} />
        <button className="primary">Create job</button>
      </form>
      <div>{jobs.map((j) => (
        <div className="card" key={j.id}>
          <div className="row"><h3>{j.title}</h3>
            <button onClick={async () => { await api.deleteJob(j.id); reload(); }}>Delete</button></div>
          <p className="muted">{j.applicants} applicants</p>
          <div>{j.required_skills.map((s) => <span className="chip" key={s}>{s}</span>)}</div>
        </div>))}</div>
    </div>
  );
}

function Candidates({ jobId, setErr, reload }) {
  const [rows, setRows] = useState([]);
  const [busy, setBusy] = useState(false);
  const load = useCallback(() => api.ranking(jobId).then(setRows).catch((e) => setErr(e.message)), [jobId, setErr]);
  useEffect(() => { load(); }, [load]);
  const upload = async (e) => {
    setBusy(true);
    try { for (const f of e.target.files) await api.apply(jobId, f); await load(); reload(); }
    catch (x) { setErr(x.message); }
    setBusy(false); e.target.value = "";
  };
  return (
    <div>
      <div className="card"><h3>Upload resumes (PDF, DOCX, TXT)</h3>
        <input type="file" multiple accept=".pdf,.docx,.txt" onChange={upload} />{busy && <span> Parsing & scoring…</span>}</div>
      <table><thead><tr><th>#</th><th>Candidate</th><th>Match</th><th>Skills</th><th>Exp</th><th>Matched</th><th>Missing</th></tr></thead>
        <tbody>{rows.map((r, i) => (
          <tr key={r.id}><td>{i + 1}</td>
            <td><b>{r.candidate.name}</b><br /><span className="muted">{r.candidate.email}</span></td>
            <td><span className="score" style={{ background: scoreColor(r.score) }}>{r.score}%</span></td>
            <td>{r.skill_score}% / text {r.text_score}%</td><td>{r.candidate.experience_years} yrs</td>
            <td>{r.matched_skills.map((s) => <span className="chip ok" key={s}>{s}</span>)}</td>
            <td>{r.missing_skills.map((s) => <span className="chip bad" key={s}>{s}</span>)}</td></tr>))}</tbody></table>
    </div>
  );
}

function Pipeline({ jobId, setErr }) {
  const [data, setData] = useState(null);
  const load = useCallback(() => api.pipeline(jobId).then(setData).catch((e) => setErr(e.message)), [jobId, setErr]);
  useEffect(() => { load(); }, [load]);
  const drop = async (e, stage) => {
    const id = e.dataTransfer.getData("id");
    if (id) { await api.setStage(id, stage); load(); }
  };
  if (!data) return null;
  return (
    <div className="kanban">{STAGES.map((s) => (
      <div className="col" key={s} onDragOver={(e) => e.preventDefault()} onDrop={(e) => drop(e, s)}>
        <h4>{s} <span className="muted">({data[s].length})</span></h4>
        {data[s].map((a) => (
          <div className="kcard" key={a.id} draggable onDragStart={(e) => e.dataTransfer.setData("id", a.id)}>
            <b>{a.candidate.name}</b>
            <div><span className="score" style={{ background: scoreColor(a.score) }}>{a.score}%</span></div>
          </div>))}
      </div>))}</div>
  );
}

function Interviews({ jobs, setErr }) {
  const [list, setList] = useState([]);
  const [apps, setApps] = useState([]);
  const [f, setF] = useState({ application_id: "", interviewer: "", scheduled_at: "", duration_min: 45, mode: "Video" });
  const load = useCallback(() => api.interviews().then(setList).catch((e) => setErr(e.message)), [setErr]);
  useEffect(() => { load(); }, [load]);
  useEffect(() => { Promise.all(jobs.map((j) => api.ranking(j.id).then((r) => r.map((a) => ({ ...a, job: j.title }))))).then((x) => setApps(x.flat())); }, [jobs]);
  const submit = async (e) => {
    e.preventDefault();
    try { await api.schedule({ ...f, application_id: +f.application_id, duration_min: +f.duration_min }); load(); }
    catch (x) { setErr(x.message); }
  };
  return (
    <div className="grid2">
      <form className="card" onSubmit={submit}>
        <h3>Schedule interview</h3>
        <select required value={f.application_id} onChange={(e) => setF({ ...f, application_id: e.target.value })}>
          <option value="">Select candidate…</option>
          {apps.map((a) => <option key={a.id} value={a.id}>{a.candidate.name} — {a.job}</option>)}</select>
        <input required placeholder="Interviewer" value={f.interviewer} onChange={(e) => setF({ ...f, interviewer: e.target.value })} />
        <input required type="datetime-local" value={f.scheduled_at} onChange={(e) => setF({ ...f, scheduled_at: e.target.value })} />
        <input type="number" min="15" step="15" value={f.duration_min} onChange={(e) => setF({ ...f, duration_min: e.target.value })} />
        <select value={f.mode} onChange={(e) => setF({ ...f, mode: e.target.value })}><option>Video</option><option>Phone</option><option>On-site</option></select>
        <button className="primary">Schedule</button>
      </form>
      <div>{list.map((i) => (
        <div className="card" key={i.id}><div className="row"><b>{i.candidate}</b>
          <button onClick={async () => { await api.cancel(i.id); load(); }}>Cancel</button></div>
          <div className="muted">{i.job} · {i.mode} · {i.duration_min} min</div>
          <div>{new Date(i.scheduled_at).toLocaleString()} with {i.interviewer}</div></div>))}</div>
    </div>
  );
}
