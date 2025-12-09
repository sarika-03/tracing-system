import os
import sys
import uvicorn
from pathlib import Path

# Dynamic service loading
service_name = os.getenv("OTEL_SERVICE_NAME", "unknown-service")
service_file = Path(f"{service_name.replace('-', '_')}.py")

if service_file.exists():
    sys.path.insert(0, str(Path.cwd()))
    module = __import__(service_name.replace('-', '_'))
    app = module.app
else:
    print(f"Service file {service_file} not found!")
    sys.exit(1)

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
