import os
import sys
import uvicorn
from pathlib import Path

# Dynamic service loading based on OTEL_SERVICE_NAME
service_name = os.getenv("OTEL_SERVICE_NAME", "unknown-service")
service_file = service_name.replace('-', '_') + '.py'

# Import the correct service module
if service_name == "auth-service":
    from auth_service import app
elif service_name == "order-service":
    from order_service import app
elif service_name == "payment-service":
    from payment_service import app
elif service_name == "inventory-service":
    from inventory_service import app
else:
    print(f" Unknown service: {service_name}")
    sys.exit(1)

if __name__ == "__main__":
    port = int(os.getenv("SERVICE_PORT", "8000"))
    print(f"🚀 Starting {service_name} on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)

