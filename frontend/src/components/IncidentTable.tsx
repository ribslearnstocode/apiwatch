import { ShieldCheck } from "lucide-react";
import { date, type Incident } from "../services/api";

export default function IncidentTable({
  incidents,
  name,
}: {
  incidents: Incident[];
  name?: string;
}) {
  return (
    <section className="panel" id="incidents">
      <div className="panel-heading">
        <div>
          <h2>
            Incident history <span className="count">{incidents.length}</span>
          </h2>
          <p>
            {name
              ? `${name} · latest 100 incidents, all time`
              : "Select a monitor to see its incident history"}
          </p>
        </div>
        <ShieldCheck size={19} className="muted" />
      </div>
      {incidents.length ? (
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Incident</th>
                <th>Status</th>
                <th>Started</th>
                <th>Resolved</th>
                <th>Duration</th>
              </tr>
            </thead>
            <tbody>
              {incidents.map((i) => (
                <tr key={i.id}>
                  <td>
                    <strong className="incident-description">
                      {i.description}
                    </strong>
                    <small className="block muted">Incident #{i.id}</small>
                  </td>
                  <td>
                    <span
                      className={`status ${i.resolved_at ? "healthy" : "unhealthy"}`}
                    >
                      <i />
                      {i.resolved_at ? "Resolved" : "Ongoing"}
                    </span>
                  </td>
                  <td className="small">{date(i.started_at)}</td>
                  <td className="small">
                    {i.resolved_at ? date(i.resolved_at) : "—"}
                  </td>
                  <td className="small">
                    {Math.max(
                      0,
                      Math.round(
                        ((i.resolved_at
                          ? new Date(i.resolved_at).getTime()
                          : Date.now()) -
                          new Date(i.started_at).getTime()) /
                          60000,
                      ),
                    )}{" "}
                    min
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="empty incident-empty">
          <ShieldCheck size={28} />
          <h3>No incidents recorded</h3>
          <p>Failures and recoveries will be tracked here automatically.</p>
        </div>
      )}
    </section>
  );
}
