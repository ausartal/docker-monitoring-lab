CREATE SCHEMA IF NOT EXISTS logs;
CREATE TABLE IF NOT EXISTS logs.fluentbit (
    id BIGSERIAL PRIMARY KEY, tag VARCHAR(255), time TIMESTAMP, data JSONB
);
CREATE INDEX IF NOT EXISTS idx_fluentbit_time ON logs.fluentbit(time DESC);
CREATE INDEX IF NOT EXISTS idx_fluentbit_tag  ON logs.fluentbit(tag);
CREATE INDEX IF NOT EXISTS idx_fluentbit_data ON logs.fluentbit USING GIN(data);
CREATE OR REPLACE VIEW logs.recent_logs AS
SELECT tag, time, data->>'level' AS level, data->>'message' AS message, data->>'service' AS service
FROM logs.fluentbit ORDER BY time DESC LIMIT 100;
CREATE OR REPLACE VIEW logs.error_summary AS
SELECT date_trunc('hour',time) AS hour, data->>'level' AS level, COUNT(*) AS count
FROM logs.fluentbit WHERE time > NOW()-INTERVAL '24 hours' GROUP BY 1,2 ORDER BY 1 DESC,3 DESC;
CREATE OR REPLACE FUNCTION logs.cleanup_old_logs(days INTEGER DEFAULT 7) RETURNS INTEGER AS $$
DECLARE deleted INTEGER;
BEGIN DELETE FROM logs.fluentbit WHERE time < NOW()-(days||' days')::INTERVAL;
GET DIAGNOSTICS deleted = ROW_COUNT; RETURN deleted; END; $$ LANGUAGE plpgsql;
GRANT USAGE ON SCHEMA logs TO app_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA logs TO app_reader;
