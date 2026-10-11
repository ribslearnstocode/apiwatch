-- Per-monitor analytics; this is the query executed by AnalyticsRepository.

SELECT m.id, m.name, m.url, m.is_active, m.check_interval,
       COUNT(r.id) AS total_checks,
       COALESCE(SUM(CASE WHEN r.is_success THEN 1 ELSE 0 END), 0) AS successful_checks,
       COUNT(r.id) - COALESCE(SUM(CASE WHEN r.is_success THEN 1 ELSE 0 END), 0) AS failed_checks,
       100.0 * SUM(CASE WHEN r.is_success THEN 1 ELSE 0 END) / NULLIF(COUNT(r.id), 0) AS uptime_percentage,
       AVG(r.response_time_ms) AS avg_response_time,
       MIN(r.response_time_ms) AS min_response_time,
       MAX(r.response_time_ms) AS max_response_time,
       (SELECT COUNT(*) FROM incidents i WHERE i.monitor_id = m.id AND i.started_at >= (CURRENT_TIMESTAMP - INTERVAL '24 hours')) AS incident_count,
       latest.response_time_ms AS latest_response_time,
       latest.checked_at AS last_checked,
       CASE WHEN NOT m.is_active THEN 'inactive'
            WHEN latest.id IS NULL THEN 'not_yet_checked'
            WHEN latest.is_success THEN 'healthy' ELSE 'unhealthy' END AS status
FROM monitors m
LEFT JOIN monitor_results r ON r.monitor_id = m.id AND r.checked_at >= (CURRENT_TIMESTAMP - INTERVAL '24 hours')
LEFT JOIN monitor_results latest ON latest.id = (
    SELECT lr.id FROM monitor_results lr WHERE lr.monitor_id = m.id
    ORDER BY lr.checked_at DESC, lr.id DESC LIMIT 1
)
GROUP BY m.id, m.name, m.url, m.is_active, m.check_interval,
         latest.id, latest.response_time_ms, latest.checked_at, latest.is_success
ORDER BY m.created_at DESC, m.id DESC
;

-- Hourly trend (PostgreSQL date_trunc) for SQL demonstrations.
SELECT monitor_id, date_trunc('hour', checked_at) AS hour, AVG(response_time_ms) AS avg_ms, COUNT(*) AS checks FROM monitor_results WHERE checked_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours' GROUP BY monitor_id, hour ORDER BY hour;

-- Active/inactive totals.
SELECT is_active, COUNT(*) FROM monitors GROUP BY is_active;
