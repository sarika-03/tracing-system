from fastapi import FastAPI, HTTPException
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
import httpx
import os
import time
import random

resource = Resource(attributes={
    "service.name": os.getenv("OTEL_SERVICE_NAME", "order-service"),
    "service.version": "1.0.0",
    "deployment.environment": "production"
})

trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer(__name__)

otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{otlp_endpoint}/v1/traces")))

app = FastAPI()
FastAPIInstrumentor.instrument_app(app)

@app.get("/")
async def health():
    return {"status": "ok", "service": "order-service"}

@app.post("/orders")
async def create_order(order_id: str):
    with tracer.start_as_current_span("order.create"):
        # Call auth service
        async with httpx.AsyncClient() as client:
            auth_resp = await client.post("http://auth-service:8003/login", json={"user_id": "user123"})
        
        # Call inventory
        async with httpx.AsyncClient() as client:
            inv_resp = await client.post("http://inventory-service:8006/check", json={"order_id": order_id})
        
        time.sleep(random.uniform(0.1, 0.5))
        return {"order_id": order_id, "status": "created"}
