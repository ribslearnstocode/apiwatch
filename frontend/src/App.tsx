import { useCallback, useEffect, useRef, useState } from "react";
import {
  Activity,
  ArrowUpRight,
  Bell,
  BookOpen,
  Check,
  ChevronDown,
  CircleHelp,
  LayoutDashboard,
  Plus,
  Radio,
  RefreshCw,
  ShieldCheck,
  X,
} from "lucide-react";
import SummaryCards from "./components/SummaryCards";
import MonitorTable from "./components/MonitorTable";
import MonitorForm from "./components/MonitorForm";
import ResponseChart from "./components/ResponseChart";
import IncidentTable from "./components/IncidentTable";
import {
  request,
  type Incident,
  type MonitorInput,
  type Result,
  type Stats,
  type Summary,
} from "./services/api";

export default function App() {
  const apiDocsUrl = `${import.meta.env.VITE_API_BASE_URL || (import.meta.env.DEV ? "http://127.0.0.1:8011" : window.location.origin)}/docs`;
  const [data, setData] = useState<Summary | null>(null);
  const [hours, setHours] = useState(24);
  const [selected, setSelected] = useState<number | null>(null);
  const [results, setResults] = useState<Result[]>([]);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [form, setForm] = useState<Stats | "new" | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [updated, setUpdated] = useState<Date | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const [section, setSection] = useState("overview");
  const [deleteTarget, setDeleteTarget] = useState<Stats | null>(null);
  const deleteDialog = useRef<HTMLDialogElement>(null);
  const monitor = data?.monitors.find((m) => m.id === selected);
  const refresh = useCallback(() => setRefreshKey((k) => k + 1), []);

  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout>;
    async function load() {
      try {
        const summary = await request<Summary>(
          `/dashboard/summary?hours=${hours}`,
        );
        if (cancelled) return;
        setData(summary);
        setUpdated(new Date());
        setError("");
        setSelected((current) =>
          summary.monitors.some((m) => m.id === current)
            ? current
            : (summary.monitors[0]?.id ?? null),
        );
      } catch (e) {
        if (!cancelled) setError((e as Error).message);
      } finally {
        if (!cancelled) timer = setTimeout(load, 12000);
      }
    }
    void load();
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [hours, refreshKey]);

  useEffect(() => {
    let cancelled = false;
    setResults([]);
    setIncidents([]);
    if (selected === null) return;
    Promise.all([
      request<Result[]>(`/monitors/${selected}/results?hours=${hours}`),
      request<Incident[]>(`/monitors/${selected}/incidents`),
    ])
      .then(([r, i]) => {
        if (!cancelled) {
          setResults(r);
          setIncidents(i);
        }
      })
      .catch((e) => {
        if (!cancelled) setError(e.message);
      });
    return () => {
      cancelled = true;
    };
  }, [selected, hours, updated]);

  useEffect(() => {
    if (deleteTarget) deleteDialog.current?.showModal();
  }, [deleteTarget]);
  useEffect(() => {
    if (notice) {
      const timer = setTimeout(() => setNotice(""), 5000);
      return () => clearTimeout(timer);
    }
  }, [notice]);

  async function action(work: () => Promise<unknown>, message: string) {
    setBusy(true);
    setError("");
    try {
      await work();
      setNotice(message);
      refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function save(input: MonitorInput) {
    await request(
      form === "new" ? "/monitors" : `/monitors/${form?.id}`,
      form === "new" ? "POST" : "PUT",
      input,
    );
    setNotice(
      form === "new"
        ? "Endpoint added. Its first check will run shortly."
        : "Endpoint updated.",
    );
    refresh();
  }
  function navigate(id: string) {
    setSection(id);
    document
      .getElementById(id)
      ?.scrollIntoView({ behavior: "smooth", block: "start" });
  }
  const successes = data?.successful_checks ?? 0;
  const failures = data?.failed_checks ?? 0;
  const total = successes + failures;
  const rate = total ? (successes / total) * 100 : 0;
  const demo = data?.monitors.some((m) => m.name.startsWith("Demo ·"));

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a
          className="brand"
          href="#overview"
          onClick={() => navigate("overview")}
        >
          <span>
            <Activity size={24} />
          </span>
          apiwatch<span className="brand-dot">.</span>
        </a>
        <div className="workspace">
          <span className="workspace-avatar">AW</span>
          <div>
            <strong>My workspace</strong>
            <small>Personal project</small>
          </div>
          <ChevronDown size={14} />
        </div>
        <p className="nav-caption">WORKSPACE</p>
        <nav>
          {[
            { id: "overview", name: "Overview", icon: LayoutDashboard },
            { id: "monitors", name: "API monitors", icon: Radio },
            { id: "analytics", name: "Analytics", icon: Activity },
            { id: "incidents", name: "Incidents", icon: Bell },
          ].map(({ id, name, icon: Icon }) => (
            <button
              className={section === id ? "active" : ""}
              key={id}
              onClick={() => navigate(id)}
            >
              <Icon size={18} />
              {name}
              {id === "monitors" && (
                <span className="nav-count">{data?.total_monitors ?? 0}</span>
              )}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="sidebar-note">
            <span className="small-orbit">
              <Activity size={20} />
            </span>
            <h3>Every request tells a story.</h3>
            <p>Keep an eye on the APIs that keep your projects running.</p>
            <a href={apiDocsUrl} target="_blank" rel="noopener noreferrer">
              Explore the API <ArrowUpRight size={14} />
            </a>
          </div>
          <button
            className="help-link"
            onClick={() => {
              setNotice(
                "Add an approved endpoint, select a check interval, and use the lightning icon to check it immediately.",
              );
              navigate("monitors");
            }}
          >
            <CircleHelp size={18} />
            Quick start
          </button>
          <div className="profile">
            <span>AW</span>
            <div>
              <strong>APIWatch</strong>
              <small>Monitoring & analytics</small>
            </div>
            <span className="version">v1.0</span>
          </div>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div>
            <span className="muted">Workspace</span>
            <span className="breadcrumb">/</span>
            <strong>Overview</strong>
          </div>
          <div className="topbar-right">
            <span className={`connection ${error ? "offline" : ""}`}>
              <i />
              {error
                ? "Connection issue"
                : updated
                  ? "Connected"
                  : "Connecting"}
            </span>
            <a
              href={apiDocsUrl}
              target="_blank"
              rel="noreferrer"
              aria-label="API documentation"
            >
              <BookOpen size={18} />
            </a>
            <span className="avatar">AW</span>
          </div>
        </header>
        <main id="overview">
          <div className="page-heading">
            <div>
              <div className="eyebrow">YOUR APIS, AT A GLANCE</div>
              <h1>
                Monitoring overview
                <span className="heading-dot" />
              </h1>
              <p>
                A little clarity for every endpoint. Stay ahead of downtime.
              </p>
            </div>
            <button className="button primary" onClick={() => setForm("new")}>
              <Plus size={18} />
              Add endpoint
            </button>
          </div>
          {demo && (
            <div className="demo-banner">
              Sample dataset · Seeded historical checks are simulated for
              demonstration. New scheduled checks are live.
            </div>
          )}
          {error && (
            <div className="error-banner" role="alert">
              <span>
                {error} {data && "Previously loaded data is shown."}
              </span>
              <button onClick={refresh}>Retry</button>
            </div>
          )}
          <div className="overview-toolbar">
            <div className="live-label">
              <span className={`pulse ${error ? "stale" : ""}`} />
              {error ? "Updates interrupted" : "Auto-refresh every 12 seconds"}
              <span className="toolbar-divider" />
              <span className="muted">
                {updated
                  ? `Updated ${updated.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`
                  : "Waiting for first update"}
              </span>
            </div>
            <div className="range-controls">
              <button
                className="icon-button"
                aria-label="Refresh dashboard"
                onClick={refresh}
              >
                <RefreshCw size={16} />
              </button>
              <select
                aria-label="Time range"
                value={hours}
                onChange={(e) => setHours(Number(e.target.value))}
              >
                <option value={1}>Last hour</option>
                <option value={24}>Last 24 hours</option>
                <option value={168}>Last 7 days</option>
                <option value={720}>Last 30 days</option>
              </select>
            </div>
          </div>
          {data ? (
            <>
              <SummaryCards data={data} />
              <div
                className={`health-banner ${data.unhealthy_monitors ? "has-failures" : ""}`}
              >
                <span className="health-icon">
                  <ShieldCheck size={21} />
                </span>
                <div>
                  <strong>
                    {data.unhealthy_monitors
                      ? `${data.unhealthy_monitors} endpoint${data.unhealthy_monitors > 1 ? "s" : ""} need attention`
                      : data.healthy_monitors
                        ? "Looking good. Your checked endpoints are healthy."
                        : "Ready when you are."}
                  </strong>
                  <p>
                    {data.unhealthy_monitors
                      ? "Review the latest checks and incident history below."
                      : data.healthy_monitors
                        ? "We’ll keep checking while the monitoring service is running."
                        : "Add or enable an endpoint to start monitoring."}
                  </p>
                </div>
                <span className="small muted">
                  {data.active_monitors} active monitors
                </span>
              </div>
              <MonitorTable
                monitors={data.monitors}
                selected={selected}
                busy={busy}
                onSelect={(id) => {
                  setSelected(id);
                  navigate("analytics");
                }}
                onEdit={setForm}
                onAdd={() => setForm("new")}
                onToggle={(m) =>
                  void action(
                    () =>
                      request(`/monitors/${m.id}`, "PUT", {
                        ...m,
                        is_active: !m.is_active,
                      }),
                    m.is_active ? "Monitoring paused." : "Monitoring enabled.",
                  )
                }
                onCheck={(m) =>
                  void action(
                    () => request(`/monitors/${m.id}/check`, "POST"),
                    "Check completed.",
                  )
                }
                onDelete={setDeleteTarget}
              />
              <div className="analytics-grid">
                <ResponseChart results={results} monitor={monitor} />
                <section className="panel check-panel">
                  <div className="panel-heading">
                    <div>
                      <h2>Check performance</h2>
                      <p>All endpoints · selected period</p>
                    </div>
                    <Activity size={18} className="muted" />
                  </div>
                  <div
                    className="donut"
                    style={{
                      background: total
                        ? `conic-gradient(#7760e8 0% ${rate}%, #f1a776 ${rate}% 100%)`
                        : "#eeeef5",
                    }}
                  >
                    <div>
                      <strong>{total ? `${rate.toFixed(1)}%` : "—"}</strong>
                      <span>successful checks</span>
                    </div>
                  </div>
                  <div className="check-legend">
                    <div>
                      <i className="purple-dot" />
                      Successful<strong>{successes.toLocaleString()}</strong>
                    </div>
                    <div>
                      <i className="orange-dot" />
                      Failed<strong>{failures.toLocaleString()}</strong>
                    </div>
                  </div>
                  <div className="check-total">
                    <span>Total completed checks</span>
                    <strong>{total.toLocaleString()}</strong>
                  </div>
                </section>
              </div>
              <IncidentTable incidents={incidents} name={monitor?.name} />
            </>
          ) : (
            <div className="panel loading">
              <Activity size={35} />
              <h2>
                {error
                  ? "Unable to load your workspace"
                  : "Connecting to your workspace…"}
              </h2>
              <p>
                {error
                  ? "Start the backend and database, then retry."
                  : "Loading your endpoints and recent checks."}
              </p>
            </div>
          )}
          <footer>
            <span>
              <Activity size={14} />
              APIWatch · A clearer view of your APIs.
            </span>
            <span>All times shown in your local timezone</span>
          </footer>
        </main>
      </div>
      {notice && (
        <div className="toast" role="status">
          <Check size={18} />
          <span>{notice}</span>
          <button
            aria-label="Dismiss notification"
            onClick={() => setNotice("")}
          >
            <X size={16} />
          </button>
        </div>
      )}
      {form && (
        <MonitorForm
          monitor={form === "new" ? null : form}
          onClose={() => setForm(null)}
          onSave={save}
        />
      )}
      {deleteTarget && (
        <dialog
          ref={deleteDialog}
          className="modal delete-modal"
          onCancel={() => setDeleteTarget(null)}
        >
          <h2>Delete {deleteTarget.name}?</h2>
          <p>
            This permanently removes the monitor, its check history, and its
            incidents.
          </p>
          <div className="modal-footer">
            <button className="button" onClick={() => setDeleteTarget(null)}>
              Cancel
            </button>
            <button
              className="button danger"
              onClick={() => {
                const id = deleteTarget.id;
                setDeleteTarget(null);
                void action(
                  () => request(`/monitors/${id}`, "DELETE"),
                  "Endpoint deleted.",
                );
              }}
            >
              Delete endpoint
            </button>
          </div>
        </dialog>
      )}
    </div>
  );
}
