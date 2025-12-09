CREATE DATABASE IF NOT EXISTS tracing;
CREATE TABLE IF NOT EXISTS tracing.spans (
  traceId String,
  spanId String,
  serviceName String,
  duration UInt64,
  receivedAt DateTime
) ENGINE = MergeTree()
ORDER BY (receivedAt, traceId);
