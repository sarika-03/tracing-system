import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from clickhouse_driver import Client
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()

# ClickHouse configuration
CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "clickhouse")
CLICKHOUSE_PORT = int(os.getenv("CLICKHOUSE_PORT", "8123"))
CLICKHOUSE_DB = os.getenv("CLICKHOUSE_DB", "traces")

# Initialize ClickHouse client
ch_client = None

def get_clickhouse_client():
    """Get or create ClickHouse client"""
    global ch_client
    if ch_client is None:
        try:
            ch_client = Client(
                host=CLICKHOUSE_HOST,
                port=9000,  # Native protocol port
                database=CLICKHOUSE_DB
            )
            logger.info(f"✅ Connected to ClickHouse at {CLICKHOUSE_HOST}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to ClickHouse: {e}")
            raise
    return ch_client

@app.on_event("startup")
async def startup_event():
    """Initialize ClickHouse connection on startup"""
    get_clickhouse_client()

@app.get("/")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "collector"}

@app.get("/health")
async def detailed_health():
    """Detailed health check"""
    try:
        client = get_clickhouse_client()
        client.execute("SELECT 1")
        return {
            "status": "healthy",
            "clickhouse": "connected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

@app.post("/v1/traces")
async def receive_traces(request: Request):
    """Receive OTLP traces via HTTP"""
    try:
        # Get raw body
        body = await request.body()
        
        if not body:
            return JSONResponse(
                status_code=400,
                content={"error": "Empty request body"}
            )

        # Try to parse as JSON
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            # If not JSON, try to handle as protobuf (simplified)
            logger.warning("Received non-JSON data, treating as protobuf")
            return {"status": "accepted", "message": "Protobuf traces received"}

        # Process resource spans
        if "resourceSpans" not in data:
            logger.warning("No resourceSpans in request")
            return {"status": "accepted", "message": "No spans to process"}

        client = get_clickhouse_client()
        spans_inserted = 0

        for resource_span in data.get("resourceSpans", []):
            # Extract resource attributes
            resource_attrs = {}
            if "resource" in resource_span and "attributes" in resource_span["resource"]:
                for attr in resource_span["resource"]["attributes"]:
                    key = attr.get("key", "")
                    value = attr.get("value", {})
                    if "stringValue" in value:
                        resource_attrs[key] = value["stringValue"]
                    elif "intValue" in value:
                        resource_attrs[key] = value["intValue"]

            service_name = resource_attrs.get("service.name", "unknown")

            # Process scope spans
            for scope_span in resource_span.get("scopeSpans", []):
                for span in scope_span.get("spans", []):
                    try:
                        # Extract span data
                        trace_id = span.get("traceId", "")
                        span_id = span.get("spanId", "")
                        parent_span_id = span.get("parentSpanId", "")
                        span_name = span.get("name", "unknown")
                        start_time = int(span.get("startTimeUnixNano", 0))
                        end_time = int(span.get("endTimeUnixNano", 0))
                        duration_ns = end_time - start_time

                        # Extract span attributes
                        span_attrs = {}
                        for attr in span.get("attributes", []):
                            key = attr.get("key", "")
                            value = attr.get("value", {})
                            if "stringValue" in value:
                                span_attrs[key] = value["stringValue"]
                            elif "intValue" in value:
                                span_attrs[key] = str(value["intValue"])
                            elif "boolValue" in value:
                                span_attrs[key] = str(value["boolValue"])

                        # Check for errors
                        status = span.get("status", {})
                        status_code = status.get("code", 0)
                        status_message = status.get("message", "")
                        has_error = status_code == 2  # ERROR status

                        # Extract HTTP attributes
                        http_method = span_attrs.get("http.method", "")
                        http_url = span_attrs.get("http.url", "")
                        http_status_code = span_attrs.get("http.status_code", "")

                        # Insert into ClickHouse
                        insert_query = """
                        INSERT INTO spans (
                            timestamp, traceId, spanId, parentSpanId, serviceName,
                            spanName, duration, hasError, statusCode, statusMessage,
                            attributes, httpMethod, httpUrl, httpStatusCode
                        ) VALUES
                        """

                        client.execute(insert_query, [{
                            'timestamp': datetime.fromtimestamp(start_time / 1e9),
                            'traceId': trace_id,
                            'spanId': span_id,
                            'parentSpanId': parent_span_id,
                            'serviceName': service_name,
                            'spanName': span_name,
                            'duration': duration_ns,
                            'hasError': 1 if has_error else 0,
                            'statusCode': status_code,
                            'statusMessage': status_message,
                            'attributes': json.dumps(span_attrs),
                            'httpMethod': http_method,
                            'httpUrl': http_url,
                            'httpStatusCode': http_status_code
                        }])

                        spans_inserted += 1

                    except Exception as e:
                        logger.error(f"Error processing span: {e}")
                        continue

        logger.info(f"✅ Inserted {spans_inserted} spans")
        return {"status": "success", "spans_received": spans_inserted}

    except Exception as e:
        logger.error(f"❌ Error processing traces: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

if __name__ == "__main__":
    import multiprocessing as mp
    
    # Run two servers: one for OTLP (4318) and one for health checks (8001)
    def run_otlp_server():
        uvicorn.run(app, host="0.0.0.0", port=4318, log_level="info")
    
    def run_health_server():
        uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
    
    # Start both servers
    p1 = mp.Process(target=run_otlp_server)
    p2 = mp.Process(target=run_health_server)
    
    p1.start()
    p2.start()
    
    p1.join()
    p2.join()