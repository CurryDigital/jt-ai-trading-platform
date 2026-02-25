#!/bin/bash
# check-ports.sh - Verify port availability before starting containers

echo "🔍 Checking port availability for Tang Inventory System..."
echo ""

# Ports to check
PORTS=("5433" "3001" "8081")
PORT_NAMES=("PostgreSQL" "Backend API" "Frontend")
ALL_CLEAR=true

for i in "${!PORTS[@]}"; do
    PORT="${PORTS[$i]}"
    NAME="${PORT_NAMES[$i]}"
    
    # Check if port is in use
    if ss -tlnp 2>/dev/null | grep -q ":$PORT "; then
        echo "❌ $NAME port $PORT is ALREADY IN USE:"
        ss -tlnp | grep ":$PORT "
        ALL_CLEAR=false
    elif netstat -tlnp 2>/dev/null | grep -q ":$PORT "; then
        echo "❌ $NAME port $PORT is ALREADY IN USE:"
        netstat -tlnp | grep ":$PORT "
        ALL_CLEAR=false
    else
        echo "✅ $NAME port $PORT is available"
    fi
done

echo ""
echo "---"
echo ""

# Check existing services that might conflict
echo "🔍 Checking for known conflicting services..."
if ss -tlnp 2>/dev/null | grep -q ":80 " || netstat -tlnp 2>/dev/null | grep -q ":80 "; then
    echo "⚠️  Port 80 (nginx) is in use - expected, no conflict"
fi
if ss -tlnp 2>/dev/null | grep -q ":443 " || netstat -tlnp 2>/dev/null | grep -q ":443 "; then
    echo "⚠️  Port 443 (nginx SSL) is in use - expected, no conflict"
fi
if ss -tlnp 2>/dev/null | grep -q ":18789 " || netstat -tlnp 2>/dev/null | grep -q ":18789 "; then
    echo "⚠️  Port 18789 (openclaw-gateway) is in use - expected, no conflict"
fi

echo ""
if [ "$ALL_CLEAR" = true ]; then
    echo "✅ All ports clear! You can start with: docker-compose up -d"
    exit 0
else
    echo "❌ Some ports are in use. Edit .env to change ports before starting."
    exit 1
fi
