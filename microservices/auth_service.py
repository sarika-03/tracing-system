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

# OpenTelemetry Setup
resource = Resource(attributes={
    "service.name": os.getenv("OTEL_SERVICE_NAME", "auth-service"),
    "service.version": "1.0.0",
    "deployment.environment": "production"
})

trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer(__name__)

otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")
span_processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{otlp_endpoint}/v1/traces"))
trace.get_tracer_provider().add_span_processor(span_processor)

app = FastAPI()
FastAPIInstrumentor.instrument_app(app)

@app.get("/")
async def health():
    return {"status": "ok", "service": "auth-service"}

@app.post("/login")
async def login(user_id: str):
    with tracer.start_as_current_span("user.login"):
        if random.random() < 0.1:
            raise HTTPException(500, "Auth failure")
        time.sleep(random.uniform(0.05, 0.3))
        return {"user_id": user_id, "token": "jwt-token"}

@app.get("/error")
async def force_error():
    raise HTTPException(500, "Forced error for testing")
