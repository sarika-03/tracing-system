from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from clickhouse_driver import Client
from datetime import datetime
import uvicorn
import os

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
    try:
        clickhouse_host = os.getenv("CLICKHOUSE_HOST", "clickhouse")
        ch_client = Client(host=clickhouse_host)
        print(f"✅ Backend connected to ClickHouse at {clickhouse_host}")
    except Exception as e:
        print(f"❌ Failed to connect to ClickHouse: {e}")
        raise

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "backend"}

@app.get("/traces/{trace_id}")
async def get_trace(trace_id: str):
    try:
        spans = ch_client.execute("""
            SELECT 
                traceId,
                spanId,
                parentSpanId,
                name,
                serviceName,
                startTimeUnixNano as startTime,
                duration,
                statusCode,
                attributes
            FROM spans 
            WHERE traceId = %(trace_id)s 
            ORDER BY startTimeUnixNano
        """, {"trace_id": trace_id})
        
        if not spans:
            raise HTTPException(404, "Trace not found")
        
        # Convert to dict format
        span_dicts = []
        for span in spans:
            span_dicts.append({
                "traceId": span[0],
                "spanId": span[1],
                "parentSpanId": span[2],
                "name": span[3],
                "serviceName": span[4],
                "startTime": span[5],
                "duration": span[6],
                "statusCode": span[7],
                "attributes": span[8]
            })
        
        # Calculate trace summary
        root_service = span_dicts[0]['serviceName'] if span_dicts else "unknown"
        total_duration = max([s['duration'] for s in span_dicts]) if span_dicts else 0
        
        return {
            "traceId": trace_id,
            "rootService": root_service,
            "totalDuration": total_duration,
            "spans": span_dicts,
            "total_spans": len(span_dicts)
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error fetching trace: {e}")
        raise HTTPException(500, f"Error fetching trace: {str(e)}")

@app.get("/search")
async def search_traces(
    limit: int = Query(20, le=100),
    service: Optional[str] = None,
    status: Optional[str] = None,
    min_duration: Optional[int] = None
):
    try:
        query = """
            SELECT 
                traceId,
                argMax(serviceName, startTimeUnixNano) as rootService,
                max(duration) as totalDuration,
                max(statusCode != 'OK') as hasError,
                groupArray(DISTINCT serviceName) as services
            FROM spans
        """
        
        conditions = []
        params = {"limit": limit}
        
        if service:
            conditions.append("serviceName = %(service)s")
            params["service"] = service
        
        if status:
            if status.upper() == "ERROR":
                conditions.append("statusCode = 'ERROR'")
            else:
                conditions.append("statusCode = %(status)s")
                params["status"] = status.upper()
        
        if min_duration:
            conditions.append("duration >= %(min_duration)s")
            params["min_duration"] = min_duration
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += """
            GROUP BY traceId
            ORDER BY max(startTimeUnixNano) DESC
            LIMIT %(limit)s
        """
        
        traces = ch_client.execute(query, params)
        
        # Convert to proper format
        result = []
        for trace in traces:
            result.append({
                "traceId": trace[0],
                "rootService": trace[1],
                "totalDuration": trace[2],
                "hasError": bool(trace[3]),
                "services": trace[4]
            })
        
        return result
    except Exception as e:
        print(f"❌ Error searching traces: {e}")
        raise HTTPException(500, f"Error searching traces: {str(e)}")

@app.get("/services")
async def list_services():
    try:
        services = ch_client.execute("""
            SELECT DISTINCT serviceName, count() as spanCount
            FROM spans
            GROUP BY serviceName
            ORDER BY spanCount DESC
        """)
        
        return [{"name": s[0], "spanCount": s[1]} for s in services]
    except Exception as e:
        print(f"❌ Error listing services: {e}")
        raise HTTPException(500, f"Error listing services: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)

    