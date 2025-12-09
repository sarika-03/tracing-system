from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List, Optional
from clickhouse_driver import Client
from datetime import datetime
import uvicorn

app = FastAPI(title="Tracing Backend")
ch_client = None

class TraceSummary(BaseModel):
    traceId: str
    rootService: str
    totalDuration: int
    hasError: bool
    services: List[str]

@app.on_event("startup")
async def startup():
    global ch_client
    ch_client = Client(host="clickhouse")

@app.get("/traces/{trace_id}")
async def get_trace(trace_id: str):
    spans = ch_client.execute("""
        SELECT * FROM spans WHERE traceId = %(trace_id)s ORDER BY startTimeUnixNano
    """, {"trace_id": trace_id})
    
    if not spans:
        return {"error": "Trace not found"}
    
    return {
        "traceId": trace_id,
        "spans": spans,
        "total_spans": len(spans)
    }

@app.get("/search")
async def search_traces(limit: int = Query(20, le=100)):
    traces = ch_client.execute("""
        SELECT traceId, argMax(serviceName, startTimeUnixNano) as rootService,
               max(duration) as totalDuration,
               max(statusCode != 'OK') as hasError,
               groupArrayDistinct(serviceName) as services
        FROM spans 
        GROUP BY traceId 
        ORDER BY max(startTimeUnixNano) DESC 
        LIMIT %(limit)s
    """, {"limit": limit})
    
    return traces

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
