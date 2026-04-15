import React, { useMemo, useRef, useState } from "react";
import "./app.css";

const ROLE_META = {
  User: { color: "user", title: "You", subtitle: "Problem owner" },
  System: { color: "system", title: "System", subtitle: "Validation" },
  CEO: { color: "ceo", title: "CEO", subtitle: "Strategy & alignment" },
  CFO: { color: "cfo", title: "CFO", subtitle: "Finance & risk" },
  CTO: { color: "cto", title: "CTO", subtitle: "Technology & architecture" },
  CMO: { color: "cmo", title: "CMO", subtitle: "Market & growth" },
  COO: { color: "coo", title: "COO", subtitle: "Operations & execution" },
  Debate: { color: "debate", title: "Debate", subtitle: "Team dynamics" },
  Devil: { color: "devil", title: "Devil’s Advocate", subtitle: "Challenge assumptions" },
  Resolution: { color: "resolution", title: "Resolution", subtitle: "Board-ready summary" },
  FinalReport: { color: "final", title: "Final Decision", subtitle: "Consensus synthesis" },
};

const EXEC_ROLES = ["CEO", "CFO", "CTO", "CMO", "COO"];

function nowTime() {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function initials(role) {
  if (role === "Devil’s Advocate" || role === "Devil") return "DA";
  return String(role || "?")
    .split(/\s+/)
    .slice(0, 2)
    .map((s) => s[0]?.toUpperCase() ?? "?")
    .join("");
}

function safeJsonLine(line) {
  try {
    return JSON.parse(line);
  } catch {
    return null;
  }
}

export default function App() {
  const [problem, setProblem] = useState("");
  const [saveToMemory, setSaveToMemory] = useState(true);
  const [speedMode, setSpeedMode] = useState(true);
  const [messages, setMessages] = useState([]);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState("");
  const [startedAt, setStartedAt] = useState(null);

  const abortRef = useRef(null);
  const feedRef = useRef(null);

  const heroHint = useMemo(() => {
    const examples = [
      "Should we launch a freemium tier in the EU next quarter?",
      "We’re missing our Q2 growth target — should we prioritize sales hiring or product-led growth?",
      "We need to cut cloud costs by 20% without hurting reliability — what’s the plan?",
    ];
    return examples[Math.floor(Math.random() * examples.length)];
  }, []);

  function scrollToBottom() {
    const el = feedRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }

  const receivedRoles = useMemo(() => {
    const s = new Set();
    for (const m of messages) {
      if (EXEC_ROLES.includes(m.role)) s.add(m.role);
      if (m.role === "FinalReport") s.add("FinalReport");
      if (m.role === "Resolution") s.add("Resolution");
    }
    return s;
  }, [messages]);

  const progress = useMemo(() => {
    const execDone = EXEC_ROLES.filter((r) => receivedRoles.has(r)).length;
    const base = execDone / EXEC_ROLES.length;
    const hasFinal = receivedRoles.has("FinalReport") ? 1 : 0;
    // weighting: execs are 80%, final is 20%
    return Math.round((base * 0.8 + hasFinal * 0.2) * 100);
  }, [receivedRoles]);

  async function runBoard() {
    setError("");
    setStartedAt(Date.now());
    setMessages([{ id: crypto.randomUUID(), role: "User", content: problem.trim(), t: nowTime() }]);
    setIsRunning(true);

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      // Speed mode toggles extra phases via env-backed defaults; we keep it client-side by
      // encouraging users to set env vars for full mode. Here we just run the stream.
      const res = await fetch("/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ problem: problem.trim(), save_to_memory: saveToMemory }),
        signal: controller.signal,
      });

      if (!res.ok || !res.body) {
        throw new Error(`Request failed (${res.status})`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buf = "";

      const typingId = crypto.randomUUID();
      setMessages((m) => [
        ...m,
        { id: typingId, role: "System", content: "Board is discussing…", t: nowTime(), typing: true },
      ]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });

        let idx;
        while ((idx = buf.indexOf("\n")) >= 0) {
          const line = buf.slice(0, idx).trim();
          buf = buf.slice(idx + 1);
          if (!line) continue;
          const obj = safeJsonLine(line);
          if (!obj || !obj.role) continue;

          setMessages((prev) => {
            const next = prev.filter((x) => x.id !== typingId);
            next.push({
              id: crypto.randomUUID(),
              role: obj.role,
              content: obj.content ?? "",
              t: nowTime(),
            });
            // keep typing indicator until FinalReport arrives
            if (obj.role !== "FinalReport") {
              next.push({
                id: typingId,
                role: "System",
                content: "Board is discussing…",
                t: nowTime(),
                typing: true,
              });
            }
            return next;
          });
          queueMicrotask(scrollToBottom);
        }
      }
    } catch (e) {
      if (e?.name !== "AbortError") {
        setError(String(e?.message || e));
      }
    } finally {
      setIsRunning(false);
      abortRef.current = null;
      queueMicrotask(scrollToBottom);
    }
  }

  function stop() {
    abortRef.current?.abort();
  }

  const elapsed =
    startedAt && isRunning ? Math.max(0, Math.round((Date.now() - startedAt) / 1000)) : null;

  const canRun = !isRunning && problem.trim().length > 0;

  return (
    <div className="app">
      <div className="bg" aria-hidden="true" />

      <header className="topbar">
        <div className="brand">
          <div className="logo">
            <span className="logoDot" />
          </div>
          <div className="brandText">
            <div className="brandTitle">Executive Board</div>
            <div className="brandSub">Multi-agent group discussion → one decision</div>
          </div>
        </div>

        <div className="topActions">
          <label className="toggle">
            <input
              type="checkbox"
              checked={saveToMemory}
              onChange={(e) => setSaveToMemory(e.target.checked)}
              disabled={isRunning}
            />
            <span>Save to memory</span>
          </label>
          <label className="toggle">
            <input
              type="checkbox"
              checked={speedMode}
              onChange={(e) => setSpeedMode(e.target.checked)}
              disabled
            />
            <span>Speed mode</span>
          </label>
          {isRunning ? (
            <button className="btn ghost" onClick={stop}>
              Stop
            </button>
          ) : (
            <a className="btn ghost" href="/health" target="_blank" rel="noreferrer">
              API
            </a>
          )}
        </div>
      </header>

      <main className="layout2">
        <aside className="side">
          <div className="panel card">
            <div className="panelHeader">
              <div className="panelTitle">Boardroom</div>
              <div className="panelSub">Status & participants</div>
            </div>

            <div className="kpis">
              <div className="kpi">
                <div className="kpiLabel">Progress</div>
                <div className="kpiValue">{isRunning ? `${progress}%` : "—"}</div>
              </div>
              <div className="kpi">
                <div className="kpiLabel">Time</div>
                <div className="kpiValue">{elapsed != null ? `${elapsed}s` : "—"}</div>
              </div>
              <div className="kpi">
                <div className="kpiLabel">Mode</div>
                <div className="kpiValue">{speedMode ? "Fast" : "Full"}</div>
              </div>
            </div>

            <div className="bar">
              <div className="barFill" style={{ width: `${isRunning ? progress : 0}%` }} />
            </div>

            <div className="people">
              {EXEC_ROLES.map((r) => {
                const meta = ROLE_META[r];
                const done = receivedRoles.has(r);
                return (
                  <div key={r} className={`person ${meta.color} ${done ? "done" : ""}`}>
                    <div className="personAvatar">{initials(meta.title)}</div>
                    <div className="personInfo">
                      <div className="personTop">
                        <span className="personName">{meta.title}</span>
                        <span className={`pill ${done ? "ok" : isRunning ? "wait" : "idle"}`}>
                          {done ? "Replied" : isRunning ? "Thinking" : "Idle"}
                        </span>
                      </div>
                      <div className="personSub">{meta.subtitle}</div>
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="note">
              Tip: write a concrete decision. Include “goal”, “constraint”, and “timeline”.
            </div>
          </div>
        </aside>

        <section className="composer card">
          <div className="cardHeader">
            <div>
              <div className="cardTitle">Business problem</div>
              <div className="cardSub">Be specific: goal, constraint, and context.</div>
            </div>
            <div className="hint">Example: {heroHint}</div>
          </div>

          <textarea
            className="input"
            value={problem}
            onChange={(e) => setProblem(e.target.value)}
            placeholder={heroHint}
            rows={4}
            disabled={isRunning}
          />

          <div className="composerActions">
            <button className="btn primary" onClick={runBoard} disabled={!canRun}>
              Run board discussion
            </button>
            <div className="status">
              {isRunning ? "Generating messages…" : "Ready"}
              {error ? <span className="err"> · {error}</span> : null}
            </div>
          </div>
        </section>

        <section className="feed card">
          <div className="feedHeader">
            <div className="feedTitle">Live discussion</div>
            <div className="feedSub">Executives respond, react, and converge on a decision.</div>
          </div>

          <div className="messages" ref={feedRef}>
            {messages.length === 0 ? (
              <div className="empty">
                <div className="emptyTitle">No messages yet</div>
                <div className="emptySub">Run the board to watch the discussion unfold.</div>
              </div>
            ) : (
              messages.map((m) => {
                const meta = ROLE_META[m.role] || { color: "other", title: m.role, subtitle: "" };
                return (
                  <div key={m.id} className={`msg ${meta.color} ${m.typing ? "typing" : ""}`}>
                    <div className="avatar" aria-hidden="true">
                      {initials(meta.title)}
                    </div>
                    <div className="bubble">
                      <div className="bubbleTop">
                        <div className="who">
                          <span className="role">{meta.title}</span>
                          {meta.subtitle ? <span className="sub">{meta.subtitle}</span> : null}
                        </div>
                        <div className="time">{m.t}</div>
                      </div>
                      <div className="content">
                        {m.typing ? (
                          <div className="dots" aria-label="typing">
                            <span />
                            <span />
                            <span />
                          </div>
                        ) : (
                          <div className="text">{m.content}</div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </section>
      </main>
    </div>
  );
}

