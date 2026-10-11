import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Activity } from "lucide-react";
import { ms, type Result, type Stats } from "../services/api";

export default function ResponseChart({
  results,
  monitor,
}: {
  results: Result[];
  monitor: Stats | undefined;
}) {
  const points = [...results]
    .reverse()
    .map((r) => ({ ...r, time: new Date(r.checked_at).getTime() }));
  return (
    <section className="panel chart-panel" id="analytics">
      <div className="panel-heading">
        <div>
          <h2>Response time</h2>
          <p>
            {monitor
              ? monitor.name
              : "Select an endpoint to explore its performance"}
          </p>
        </div>
        <span className="legend">
          <i />
          Latency
        </span>
      </div>
      <div className="chart-stats">
        <div>
          <span>Average</span>
          <strong>{ms(monitor?.avg_response_time ?? null)}</strong>
        </div>
        <div>
          <span>Minimum</span>
          <strong>{ms(monitor?.min_response_time ?? null)}</strong>
        </div>
        <div>
          <span>Maximum</span>
          <strong>{ms(monitor?.max_response_time ?? null)}</strong>
        </div>
      </div>
      <div className="chart">
        {points.length ? (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart
              data={points}
              margin={{ top: 10, right: 20, left: 0, bottom: 0 }}
            >
              <defs>
                <linearGradient id="latencyFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#7862e9" stopOpacity={0.22} />
                  <stop offset="100%" stopColor="#7862e9" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid
                strokeDasharray="4 5"
                vertical={false}
                stroke="#ececf3"
              />
              <XAxis
                dataKey="time"
                type="number"
                domain={["dataMin", "dataMax"]}
                tickFormatter={(t) =>
                  new Date(t).toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                  })
                }
                tick={{ fill: "#9294a7", fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                minTickGap={45}
              />
              <YAxis
                tick={{ fill: "#9294a7", fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                width={52}
                tickFormatter={(v) => `${v}`}
              />
              <Tooltip
                labelFormatter={(value) =>
                  new Date(Number(value)).toLocaleString()
                }
                formatter={(value) => [
                  `${Number(value).toFixed(1)} ms`,
                  "Response time",
                ]}
                contentStyle={{ border: "1px solid #e9e7f3", borderRadius: 12 }}
              />
              <Area
                type="linear"
                dataKey="response_time_ms"
                stroke="#7862e9"
                strokeWidth={2.5}
                fill="url(#latencyFill)"
                dot={points.length < 3}
                isAnimationActive={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div className="empty chart-empty">
            <Activity size={28} />
            <p>Response-time history will appear after the first check.</p>
          </div>
        )}
      </div>
      <div className="panel-footer">
        Latest {results.length} checks in selected period
        <span>Time to response headers · milliseconds</span>
      </div>
    </section>
  );
}
