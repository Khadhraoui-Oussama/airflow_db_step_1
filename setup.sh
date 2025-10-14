#!/bin/bash
set -e

echo "🏗️ Setting up Municipal Budget ETL Pipeline..."
echo

# Check Docker
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker not running. Please start Docker and try again."
    exit 1
fi
echo "✅ Docker is running"

# Setup environment
if [ ! -f .env ]; then
    echo "📝 Creating .env from template..."
    cp .env.example .env
    echo "✅ Environment file created"
else
    echo "✅ Environment file exists"
fi

# Create directories
echo "📁 Creating directories..."
mkdir -p logs data output processed reports scripts config dags

# Start services
echo "🐳 Starting Docker services..."
docker-compose up -d

echo "⏳ Waiting for services to initialize..."
sleep 30

echo
echo "🎉 Setup complete!"
echo
echo "📊 Access your services:"
echo "   Airflow UI:  http://localhost:8090 (airflow/airflow)"
echo "   pgAdmin:     http://localhost:8081 (admin@admin.com/admin)"
echo
echo "📚 Next steps:"
echo "   1. Wait 2-3 minutes for full startup"
echo "   2. Open Airflow UI and enable the ETL DAG"  
echo "   3. Trigger the DAG to process budget data"
echo "   4. View results in pgAdmin"
echo
echo "🔧 Commands:"
echo "   Stop:     docker-compose down"
echo "   Logs:     docker-compose logs -f"
echo "   Restart:  docker-compose restart"
echo