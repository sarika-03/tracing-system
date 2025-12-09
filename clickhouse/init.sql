CREATE TABLE IF NOT EXISTS spans (
    traceId String,
    spanId String,
    parentSpanId Nullable(String),
    name String,
    serviceName String,
    startTimeUnixNano UInt64,
    endTimeUnixNano UInt64,
    duration UInt64,
    statusCode String DEFAULT 'OK',
    statusMessage String DEFAULT '',
    attributes Map(String, String),
    events Array(String),
    receivedAt DateTime64(3)
) ENGINE = MergeTree()
ORDER BY (receivedAt, traceId, startTimeUnixNano);

CREATE TABLE IF NOT EXISTS traces (
    traceId String,
    rootService String,
    totalDuration UInt64,
    hasError UInt8,
    services Array(String),
    receivedAt DateTime64(3)
) ENGINE = ReplacingMergeTree(receivedAt)
ORDER BY (receivedAt, traceId);
