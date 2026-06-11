CREATE SCHEMA IF NOT EXISTS logs;

CREATE TABLE IF NOT EXISTS logs.fluentbit (
    id       BIGSERIAL PRIMARY KEY,
    tag      VARCHAR(200),
    time     TIMESTAMP,
    data     JSONB
);

CREATE INDEX IF NOT EXISTS idx_fb_time ON logs.fluentbit(time);
CREATE INDEX IF NOT EXISTS idx_fb_tag  ON logs.fluentbit(tag);
CREATE INDEX IF NOT EXISTS idx_fb_data ON logs.fluentbit USING GIN(data);

CREATE OR REPLACE VIEW logs.recent_logs AS
SELECT id, to_char(time, 'YYYY-MM-DD HH24:MI:SS') AS time, tag,
       REPLACE(data->>'container_name', '/', '') AS container,
       data->>'source' AS source,
       LEFT(data->>'log', 200) AS log_preview
FROM logs.fluentbit ORDER BY time DESC LIMIT 100;

CREATE OR REPLACE VIEW logs.structured_logs AS
SELECT id, time AS received_at, tag,
       REPLACE(data->>'container_name', '/', '') AS container_name,
       (data->>'log')::jsonb->>'level' AS log_level,
       (data->>'log')::jsonb->>'message' AS message,
       (data->>'log')::jsonb->>'service' AS service
FROM logs.fluentbit
WHERE data->>'log' IS NOT NULL AND LEFT(TRIM(data->>'log'), 1) = '{'
ORDER BY time DESC;

CREATE OR REPLACE VIEW logs.error_summary AS
SELECT REPLACE(data->>'container_name', '/', '') AS container_name,
       (data->>'log')::jsonb->>'level' AS log_level,
       COUNT(*) AS count, MAX(time) AS last_seen
FROM logs.fluentbit
WHERE data->>'log' IS NOT NULL AND LEFT(TRIM(data->>'log'), 1) = '{'
  AND (data->>'log')::jsonb->>'level' IN ('ERROR', 'WARN', 'CRITICAL')
GROUP BY 1, 2 ORDER BY count DESC;
