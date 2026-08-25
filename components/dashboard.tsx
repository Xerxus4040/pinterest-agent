"use client";

import { useState } from "react";

const activity = [
  ["Student 01", "Modern 3 Bedroom Plan", "Waiting approval"],
  ["Student 02", "Small House Blueprint", "Published"],
  ["Student 03", "Minimal Villa Plan", "Processing"],
  ["Student 04", "2 Bedroom Floor Plan", "Published"],
];

export default function Dashboard() {
  const [mode, setMode] = useState<"approval" | "auto">("approval");

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="logo">◈ PinPilot AI</div>
        <nav className="nav">
          <a className="active" href="#">Overview</a>
          <a href="#queue">Approval Queue</a>
          <a href="#students">Students</a>
          <a href="#connections">Connections</a>
          <a href="#ai">AI Settings</a>
          <a href="#scheduler">Scheduler</a>
          <a href="#logs">Activity & Logs</a>
        </nav>
      </aside>

      <main className="main">
        <div className="topbar">
          <div>
            <div className="title">AI Pinterest Agent</div>
            <div className="sub">Blueprint → creative → SEO → approval → Pinterest</div>
          </div>
          <div className="pill">System <b>● Online</b></div>
        </div>

        <div className="banner">
          <b>Testing mode:</b> Human Approval is ON. The agent can prepare content,
          but it will not publish until you approve it. Switch to Fully Automatic only
          after testing is complete.
        </div>

        <section className="grid4">
          <div className="card"><div className="label">Active Students</div><div className="metric">10</div></div>
          <div className="card"><div className="label">Pins Today</div><div className="metric">12</div></div>
          <div className="card"><div className="label">Pending Approval</div><div className="metric">4</div></div>
          <div className="card"><div className="label">Success Rate</div><div className="metric">98.2%</div></div>
        </section>

        <div className="grid2">
          <section className="card" id="connections">
            <div className="section-title">Connections</div>
            <div className="row">
              <div><b>Pinterest</b><div className="help">OAuth connection</div></div>
              <span className="status ok">Ready</span>
            </div>
            <div className="row">
              <div><b>Google Drive</b><div className="help">Public/shared source folder</div></div>
              <span className="status ok">Ready</span>
            </div>
            <div className="row">
              <div><b>Gemini</b><div className="help">Server-side API key</div></div>
              <span className="status ok">Configured</span>
            </div>
          </section>

          <section className="card" id="ai">
            <div className="section-title">Automation Mode</div>
            <div className="form">
              <label className="row">
                <span><b>Human Approval</b><div className="help">Recommended for testing</div></span>
                <input type="radio" checked={mode === "approval"} onChange={() => setMode("approval")} />
              </label>
              <label className="row">
                <span><b>Fully Automatic</b><div className="help">Publish after QA without approval</div></span>
                <input type="radio" checked={mode === "auto"} onChange={() => setMode("auto")} />
              </label>
              <div className="help">
                Current mode: <b>{mode === "approval" ? "Human Approval" : "Fully Automatic"}</b>
              </div>
            </div>
          </section>
        </div>

        <section className="card" id="queue" style={{marginTop:18}}>
          <div className="section-title">Recent Agent Activity</div>
          {activity.map(([student, item, status]) => (
            <div className="row" key={student}>
              <div>
                <b>{student}</b>
                <div className="help">{item}</div>
              </div>
              <span className={`status ${status === "Published" ? "ok" : "wait"}`}>{status}</span>
            </div>
          ))}
        </section>

        <section className="card" id="scheduler" style={{marginTop:18}}>
          <div className="section-title">Scheduler Preview</div>
          <div className="row">
            <div><b>Daily publishing window</b><div className="help">Asia/Karachi · 8:00 PM</div></div>
            <span className="status ok">Enabled</span>
          </div>
          <div className="help">
            The production scheduler will run server-side, so a student does not need
            to keep this dashboard open.
          </div>
        </section>
      </main>
    </div>
  );
}
