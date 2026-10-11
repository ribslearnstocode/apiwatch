import {
  ChevronRight,
  Pencil,
  Play,
  Pause,
  Trash2,
  Zap,
  Search,
  Radio,
} from "lucide-react";
import { useState } from "react";
import { date, ms, type Stats } from "../services/api";

export const statusNames = {
  healthy: "Healthy",
  unhealthy: "Unhealthy",
  not_yet_checked: "Not yet checked",
  inactive: "Inactive",
};
export function Status({ status }: { status: Stats["status"] }) {
  return (
    <span className={`status ${status}`}>
      <i />
      {statusNames[status]}
    </span>
  );
}

type Props = {
  monitors: Stats[];
  selected: number | null;
  busy: boolean;
  onSelect: (id: number) => void;
  onEdit: (monitor: Stats) => void;
  onToggle: (monitor: Stats) => void;
  onCheck: (monitor: Stats) => void;
  onDelete: (monitor: Stats) => void;
  onAdd: () => void;
};
export default function MonitorTable(props: Props) {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("all");
  const filtered = props.monitors.filter(
    (m) =>
      `${m.name} ${m.url}`.toLowerCase().includes(query.toLowerCase()) &&
      (status === "all" || m.status === status),
  );
  return (
    <section className="panel" id="monitors">
      <div className="panel-heading">
        <div>
          <h2>
            API monitors <span className="count">{props.monitors.length}</span>
          </h2>
          <p>A live pulse on every endpoint.</p>
        </div>
        <div className="table-filters">
          <label className="search">
            <Search size={16} />
            <input
              aria-label="Search monitors"
              placeholder="Search endpoints…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </label>
          <select
            aria-label="Filter by status"
            value={status}
            onChange={(e) => setStatus(e.target.value)}
          >
            <option value="all">All statuses</option>
            {Object.entries(statusNames).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </div>
      </div>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Endpoint</th>
              <th>Status</th>
              <th>Response time</th>
              <th>Uptime</th>
              <th>Last checked</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((m) => (
              <tr
                key={m.id}
                className={props.selected === m.id ? "selected-row" : ""}
              >
                <td>
                  <button
                    className="endpoint-name"
                    onClick={() => props.onSelect(m.id)}
                  >
                    <span className="endpoint-icon">
                      <Radio size={17} />
                    </span>
                    <span>
                      <strong>{m.name}</strong>
                      <small>{m.url}</small>
                    </span>
                    <ChevronRight size={14} />
                  </button>
                </td>
                <td>
                  <Status status={m.status} />
                </td>
                <td className="tabular">{ms(m.latest_response_time)}</td>
                <td>
                  <div className="uptime">
                    <span>
                      {m.uptime_percentage === null
                        ? "—"
                        : `${m.uptime_percentage.toFixed(1)}%`}
                    </span>
                    <div>
                      <i style={{ width: `${m.uptime_percentage ?? 0}%` }} />
                    </div>
                  </div>
                </td>
                <td className="muted small">{date(m.last_checked)}</td>
                <td>
                  <div className="actions">
                    <button
                      disabled={props.busy || !m.is_active}
                      title="Run check"
                      aria-label={`Check ${m.name}`}
                      onClick={() => props.onCheck(m)}
                    >
                      <Zap size={15} />
                    </button>
                    <button
                      disabled={props.busy}
                      title={m.is_active ? "Pause" : "Enable"}
                      aria-label={`${m.is_active ? "Pause" : "Enable"} ${m.name}`}
                      onClick={() => props.onToggle(m)}
                    >
                      {m.is_active ? <Pause size={15} /> : <Play size={15} />}
                    </button>
                    <button
                      disabled={props.busy}
                      title="Edit"
                      aria-label={`Edit ${m.name}`}
                      onClick={() => props.onEdit(m)}
                    >
                      <Pencil size={15} />
                    </button>
                    <button
                      disabled={props.busy}
                      title="Delete"
                      aria-label={`Delete ${m.name}`}
                      onClick={() => props.onDelete(m)}
                    >
                      <Trash2 size={15} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {!filtered.length && (
        <div className="empty">
          <Radio size={30} />
          <h3>
            {props.monitors.length
              ? "No matching endpoints"
              : "Your first endpoint starts here"}
          </h3>
          <p>
            {props.monitors.length
              ? "Try another search or status filter."
              : "Add an API to start collecting response times and health checks."}
          </p>
          {!props.monitors.length && (
            <button className="button primary" onClick={props.onAdd}>
              Add your first endpoint
            </button>
          )}
        </div>
      )}
      <div className="panel-footer">
        Showing {filtered.length} of {props.monitors.length} endpoints
        <span>Uptime = successful checks ÷ completed checks</span>
      </div>
    </section>
  );
}
