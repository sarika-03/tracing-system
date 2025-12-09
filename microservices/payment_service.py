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
    "service.name": os.getenv("OTEL_SERVICE_NAME", "payment-service"),
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
    return {"status": "ok", "service": "payment-service"}

@app.post("/pay")
async def make_payment(order_id: str):
    with tracer.start_as_current_span("payment.process") as span:
        span.set_attribute("order.id", order_id)
        span.set_attribute("payment.method", "credit_card")
        
        # Simulate payment processing
        time.sleep(random.uniform(0.1, 0.4))
        
        # Random payment errors
        if random.random() < 0.1:
            span.set_attribute("error", True)
            span.set_attribute("error.type", "PaymentProcessingError")
            raise HTTPException(500, "Payment processing error")
        
        span.set_attribute("payment.status", "completed")
        return {"order_id": order_id, "status": "paid", "amount": random.randint(50, 500)}

@app.get("/error")
async def force_error():
    with tracer.start_as_current_span("forced.error") as span:
        span.set_attribute("error", True)
        span.set_attribute("test", True)
        raise HTTPException(500, "Forced error for testing")