from fastapi import FastAPI, HTTPException
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
import os
import time
import random

resource = Resource(attributes={
    "service.name": os.getenv("OTEL_SERVICE_NAME", "inventory-service"),
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

@app.get("/")
async def health():
    return {"status": "ok", "service": "inventory-service"}

@app.post("/check")
async def check_inventory(order_id: str):
    with tracer.start_as_current_span("inventory.check") as span:
        span.set_attribute("order.id", order_id)
        
        # Simulate inventory check
        time.sleep(random.uniform(0.05, 0.2))
        
        # Random inventory issues
        if random.random() < 0.15:
            span.set_attribute("error", True)
            span.set_attribute("error.type", "InventoryShortage")
            raise HTTPException(409, "Inventory shortage")
        
        available_qty = random.randint(1, 100)
        span.set_attribute("inventory.available", available_qty)
        span.set_attribute("inventory.status", "available")
        
        return {
            "order_id": order_id, 
            "available": True,
            "quantity": available_qty
        }

@app.get("/error")
async def force_error():
    with tracer.start_as_current_span("forced.error") as span:
        span.set_attribute("error", True)
        span.set_attribute("test", True)
        raise HTTPException(500, "Forced error for testing")