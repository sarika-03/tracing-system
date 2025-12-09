#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 Testing Distributed Tracing System${NC}\n"

# Check if services are running
echo -e "${YELLOW}0️⃣ Checking if services are running...${NC}"
if ! docker-compose ps | grep -q "Up"; then
    echo -e "${RED}❌ Services not running. Please start with: docker-compose up -d${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Services are running${NC}\n"

# Test 1: Health checks
echo -e "${YELLOW}1️⃣ Testing health endpoints...${NC}"
for service in "backend:8002" "collector:8001" "auth-service:8003" "order-service:8004" "payment-service:8005" "inventory-service:8006"; do
    name=$(echo $service | cut -d: -f1)
    port=$(echo $service | cut -d: -f2)
    
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$port/)
    if [ $response -eq 200 ]; then
        echo -e "${GREEN}✅ $name is healthy${NC}"
    else
        echo -e "${RED}❌ $name failed (HTTP $response)${NC}"
    fi
done
echo ""

# Test 2: Generate traces
echo -e "${YELLOW}2️⃣ Generating test traces...${NC}"
success_count=0
error_count=0

for i in {1..10}; do
    echo -n "Creating order $i... "
    response=$(curl -s -o /dev/null -w "%{http_code}" -X POST "http://localhost:8004/orders?order_id=order_$i")
    
    if [ $response -eq 200 ]; then
        echo -e "${GREEN}✅${NC}"
        ((success_count++))
    else
        echo -e "${RED}❌ (HTTP $response)${NC}"
        ((error_count++))
    fi
    
    sleep 0.5
done
echo -e "Success: ${GREEN}$success_count${NC} | Errors: ${RED}$error_count${NC}\n"

# Wait for traces to be processed
echo -e "${YELLOW}⏳ Waiting for traces to be processed (3 seconds)...${NC}"
sleep 3
echo ""

# Test 3: Query traces
echo -e "${YELLOW}3️⃣ Querying traces from backend...${NC}"
traces=$(curl -s "http://localhost:8002/search?limit=5")
trace_count=$(echo $traces | jq '. | length')

if [ "$trace_count" -gt 0 ]; then
    echo -e "${GREEN}✅ Found $trace_count traces${NC}"
    echo "$traces" | jq -r '.[] | "  📊 Trace: \(.traceId[0:12])... | Service: \(.rootService) | Duration: \(.totalDuration/1000)ms | Error: \(.hasError)"'
else
    echo -e "${RED}❌ No traces found${NC}"
fi
echo ""

# Test 4: Get services
echo -e "${YELLOW}4️⃣ Listing services...${NC}"
services=$(curl -s http://localhost:8002/services)
service_count=$(echo $services | jq '. | length')

if [ "$service_count" -gt 0 ]; then
    echo -e "${GREEN}✅ Found $service_count services${NC}"
    echo "$services" | jq -r '.[] | "  🔧 \(.name): \(.spanCount) spans"'
else
    echo -e "${RED}❌ No services found${NC}"
fi
echo ""

# Test 5: Generate some errors
echo -e "${YELLOW}5️⃣ Testing error handling...${NC}"
for service in "auth-service:8003" "payment-service:8005" "inventory-service:8006"; do
    name=$(echo $service | cut -d: -f1)
    port=$(echo $service | cut -d: -f2)
    
    curl -s -o /dev/null "http://localhost:$port/error"
    echo -e "${GREEN}✅ Triggered error on $name${NC}"
done
echo ""

# Test 6: ClickHouse verification
echo -e "${YELLOW}6️⃣ Verifying ClickHouse data...${NC}"
span_count=$(docker exec clickhouse clickhouse-client --query "SELECT count() FROM spans" 2>/dev/null)
if [ ! -z "$span_count" ]; then
    echo -e "${GREEN}✅ ClickHouse has $span_count spans stored${NC}"
else
    echo -e "${RED}❌ Could not query ClickHouse${NC}"
fi
echo ""

# Summary
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Tests Complete!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo ""
echo -e "📊 ${YELLOW}View traces in your browser:${NC}"
echo -e "   ${BLUE}http://localhost:3000${NC}"
echo ""
echo -e "🔍 ${YELLOW}API Endpoints:${NC}"
echo -e "   Backend:    ${BLUE}http://localhost:8002${NC}"
echo -e "   Collector:  ${BLUE}http://localhost:8001${NC}"
echo ""
echo -e "🐛 ${YELLOW}Troubleshooting:${NC}"
echo -e "   Logs:     ${BLUE}docker-compose logs -f${NC}"
echo -e "   Restart:  ${BLUE}docker-compose restart${NC}"
echo -e "   Clean:    ${BLUE}docker-compose down -v && docker-compose up -d${NC}"
echo ""