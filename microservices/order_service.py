from fastapi import FastAPI, HTTPException
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
import httpx
import os
import time
import random

# OpenTelemetry Setup
resource = Resource(attributes={
    "service.name": os.getenv("OTEL_SERVICE_NAME", "order-service"),
    "service.version": "1.0.0",
    "deployment.environment": "production"
})

trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer(__name__)

otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://collector:4318")
span_processor = BatchSpanProcessor(
    OTLPSpanExporter(endpoint=f"{otlp_endpoint}/v1/traces")
)
trace.get_tracer_provider().add_span_processor(span_processor)

app = FastAPI()
FastAPIInstrumentor.instrument_app(app)
HTTPXClientInstrumentor().instrument()

@app.get("/")
async def health():
    return {"status": "ok", "service": "order-service"}

@app.post("/orders")
async def create_order(order_id: str):
    with tracer.start_as_current_span("order.create") as span:
        span.set_attribute("order.id", order_id)
        
        try:
            # Call auth service
            with tracer.start_as_current_span("call.auth-service"):
                async with httpx.AsyncClient(timeout=5.0) as client:
                    auth_resp = await client.post(
                        "http://auth-service:8003/login",
                        params={"user_id": "user123"}
                    )
                    if auth_resp.status_code != 200:
                        raise HTTPException(500, "Auth service failed")
            
            # Call inventory
            with tracer.start_as_current_span("call.inventory-service"):
                async with httpx.AsyncClient(timeout=5.0) as client:
                    inv_resp = await client.post(
                        "http://inventory-service:8006/check",
                        params={"order_id": order_id}
                    )
                    if inv_resp.status_code != 200:
                        raise HTTPException(409, "Inventory check failed")
            
            # Simulate order processing
            time.sleep(random.uniform(0.1, 0.5))
            
            # Random errors
            if random.random() < 0.05:
                span.set_attribute("error", True)
                raise HTTPException(500, "Order processing error")
            
            span.set_attribute("order.status", "created")
            return {"order_id": order_id, "status": "created"}
            
        except HTTPException:
            raise
        except Exception as e:
            span.set_attribute("error", True)
            span.set_attribute("error.message", str(e))
            raise HTTPException(500, f"Order service error: {str(e)}")