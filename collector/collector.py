from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import yaml
import time
import uuid
from clickhouse_driver import Client
from anomaly_detector import detector
import numpy as np
from datetime import datetime

app = FastAPI(title="Tracing Collector")
ch_client: Client = None

class Span(BaseModel):
    traceId: str
    spanId: str
    parentSpanId: Optional[str] = None
    name: str
    serviceName: str
    startTimeUnixNano: int
    endTimeUnixNano: int
    status: Dict[str, Any] = {}
    attributes: Dict[str, str] = {}
    events: List[str] = []

class TracesRequest(BaseModel):
    resourceSpans: List[Dict[str, List[Span]]]

import os
import yaml

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RULES_PATH = os.path.join(BASE_DIR, "rules.yaml")

with open(RULES_PATH, "r") as f:
    SAMPLING_RULES = yaml.safe_load(f)

def head_sample(spans: List[Span], rate: float = 0.1) -> List[Span]:
    return spans[:int(len(spans) * rate)]

def tail_sample(spans: List[Span]) -> List[Span]:
    high_latency = [s for s in spans if s.endTimeUnixNano - s.startTimeUnixNano > 300_000_000]  # 300ms
    errors = [s for s in spans if s.status.get("code") == 2]  # ERROR status
    return list(set(high_latency + errors))

@app.on_event("startup")
async def startup():
    global ch_client
    ch_client = Client(host="clickhouse")

@app.post("/v1/traces")
async def receive_traces(request: TracesRequest):
    all_spans = []
    for resource_span in request.resourceSpans:
        spans = resource_span.get("scopeSpans", [{}])[0].get("spans", [])
        all_spans.extend([Span(**s) for s in spans])

    # Apply sampling
    sampled_spans = head_sample(all_spans, SAMPLING_RULES["head_sample_rate"])
    sampled_spans.extend(tail_sample(all_spans))

    # Anomaly detection - keep if anomalous
    service_spans = {}
    for span in sampled_spans:
        service_spans.setdefault(span.serviceName, []).append({
            "traceId": span.traceId, "spanId": span.spanId, "parentSpanId": span.parentSpanId,
            "name": span.name, "serviceName": span.serviceName,
            "startTimeUnixNano": span.startTimeUnixNano // 1000,  # to microseconds
            "endTimeUnixNano": span.endTimeUnixNano // 1000,
            "duration": (span.endTimeUnixNano - span.startTimeUnixNano) // 1000,
            "statusCode": span.status.get("code", 0) and "ERROR" or "OK",
            "statusMessage": span.status.get("message", ""),
            "attributes": span.attributes,
            "events": span.events,
            "receivedAt": datetime.now()
        })

    for service, spans in service_spans.items():
        if detector.detect_latency_spike(spans, service) or detector.detect_error_spike(spans, service):
            all_spans.extend(spans)

    # Bulk insert to ClickHouse
    if all_spans:
        ch_client.execute(
            "INSERT INTO spans VALUES",
            all_spans,
            types_check=True
        )

    return {"received": len(all_spans), "sampled": len(sampled_spans)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
