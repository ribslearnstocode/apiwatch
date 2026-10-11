import {
  Activity,
  ArrowUpRight,
  CircleCheck,
  Clock3,
  Radio,
} from "lucide-react";
import { ms, type Summary } from "../services/api";

export default function SummaryCards({ data }: { data: Summary }) {
  const cards = [
    {
      label: "Total endpoints",
      value: data.total_monitors,
      note: `${data.active_monitors} active · ${data.inactive_monitors} paused`,
      icon: Radio,
      color: "purple",
    },
    {
      label: "Healthy endpoints",
      value: data.healthy_monitors,
      note: "Latest check returned HTTP 2xx",
      icon: CircleCheck,
      color: "green",
    },
    {
      label: "Unhealthy endpoints",
      value: data.unhealthy_monitors,
      note: data.unhealthy_monitors
        ? "Endpoints need your attention"
        : "No failures in the latest checks",
      icon: Activity,
      color: "orange",
    },
    {
      label: "Avg. response time",
      value: ms(data.average_response_time),
      note: "Across checks in the selected period",
      icon: Clock3,
      color: "blue",
    },
  ];
  return (
    <div className="summary-grid">
      {cards.map(({ label, value, note, icon: Icon, color }) => (
        <article className="summary-card" key={label}>
          <div className="card-top">
            <span>{label}</span>
            <span className={`icon-box ${color}`}>
              <Icon size={18} />
            </span>
          </div>
          <strong>{value}</strong>
          <p>{note}</p>
          <ArrowUpRight className="card-corner" size={16} />
        </article>
      ))}
    </div>
  );
}
