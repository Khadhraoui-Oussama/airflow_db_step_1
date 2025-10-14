# Integration Examples

This document shows how to integrate the Budget ETL pipeline with other containerized applications.

## 🌐 Method 1: Docker Network Integration

### Connect External Container to ETL Services

```yaml
# your-external-app/docker-compose.yaml
version: '3.8'

services:
  your-app:
    image: your-app:latest
    environment:
      # Connect to Budget ETL database
      - DATABASE_URL=postgresql://airflow:airflow@budget-etl-postgres:5432/airflow
      # Connect to Airflow API  
      - AIRFLOW_API_URL=http://budget-etl-airflow:8080/api/v1/
    networks:
      - your-app-network
      - budget-etl-network

networks:
  your-app-network:
    driver: bridge
  budget-etl-network:
    external: true
    name: airflow_docker_default  # Auto-generated network name
```

### Join Existing Network
```bash
# Run your container on the same network
docker run -d \
  --name my-app \
  --network airflow_docker_default \
  -e DB_HOST=postgres \
  -e DB_PORT=5432 \
  my-app:latest
```

## 🚀 Method 2: API Integration

### Trigger ETL from External Service

```python
# Python example - trigger DAG via REST API
import requests
from datetime import datetime

def trigger_etl_pipeline(data_file=None):
    url = "http://localhost:8090/api/v1/dags/budget_municipal_etl/dagRuns"
    
    payload = {
        "conf": {
            "data_file": data_file or "Budget_municipal.xlsx",
            "triggered_by": "external_system",
            "timestamp": datetime.now().isoformat()
        }
    }
    
    response = requests.post(
        url,
        json=payload,
        auth=("airflow", "airflow"),
        headers={"Content-Type": "application/json"}
    )
    
    return response.json()

# Usage
result = trigger_etl_pipeline("new_budget_data.xlsx")
print(f"DAG Run ID: {result.get('dag_run_id')}")
```

```javascript
// JavaScript/Node.js example
const axios = require('axios');

async function triggerETL(dataFile = 'Budget_municipal.xlsx') {
  try {
    const response = await axios.post(
      'http://localhost:8090/api/v1/dags/budget_municipal_etl/dagRuns',
      {
        conf: {
          data_file: dataFile,
          triggered_by: 'web_app',
          timestamp: new Date().toISOString()
        }
      },
      {
        auth: {
          username: 'airflow',
          password: 'airflow'
        }
      }
    );
    
    return response.data;
  } catch (error) {
    console.error('ETL trigger failed:', error.message);
    throw error;
  }
}
```

### Monitor ETL Status

```python
# Check DAG run status
def check_etl_status(dag_run_id):
    url = f"http://localhost:8090/api/v1/dags/budget_municipal_etl/dagRuns/{dag_run_id}"
    
    response = requests.get(
        url,
        auth=("airflow", "airflow")
    )
    
    data = response.json()
    return {
        "status": data.get("state"),
        "start_date": data.get("start_date"),
        "end_date": data.get("end_date"),
        "execution_date": data.get("execution_date")
    }
```

## 📊 Method 3: Database Integration

### Direct Database Access

```python
# Connect to budget data from external application
import psycopg2
import pandas as pd

class BudgetDataClient:
    def __init__(self):
        self.conn = psycopg2.connect(
            host='localhost',  # or container name if same network
            port=5432,
            database='airflow',
            user='airflow',
            password='airflow'
        )
    
    def get_budget_summary(self, fiscal_year=None):
        query = """
        SELECT 
            sheet_name,
            fiscal_year,
            total_records,
            total_budget_amount,
            processing_date
        FROM budget.budget_summary
        """
        
        if fiscal_year:
            query += f" WHERE fiscal_year = {fiscal_year}"
            
        return pd.read_sql(query, self.conn)
    
    def get_budget_by_category(self, category=None):
        query = """
        SELECT 
            budget_category,
            COUNT(*) as item_count,
            SUM(budget_amount) as total_amount,
            AVG(budget_amount) as avg_amount
        FROM budget.budget_data
        """
        
        if category:
            query += f" WHERE budget_category = '{category}'"
            
        query += " GROUP BY budget_category ORDER BY total_amount DESC"
        
        return pd.read_sql(query, self.conn)

# Usage
client = BudgetDataClient()
summary = client.get_budget_summary(2025)
categories = client.get_budget_by_category()
```

### Database Connection Pool

```python
# For high-traffic applications
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

class BudgetETLDatabase:
    def __init__(self):
        self.engine = create_engine(
            'postgresql://airflow:airflow@localhost:5432/airflow',
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True
        )
    
    def execute_query(self, query, params=None):
        with self.engine.connect() as conn:
            result = conn.execute(query, params or {})
            return result.fetchall()
```

## 🔄 Method 4: Event-Driven Integration

### Webhook Integration

```python
# Flask app to receive ETL completion notifications
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route('/etl-webhook', methods=['POST'])
def handle_etl_completion():
    data = request.json
    
    if data.get('dag_id') == 'budget_municipal_etl':
        if data.get('state') == 'success':
            # Process successful ETL completion
            process_new_budget_data()
        elif data.get('state') == 'failed':
            # Handle ETL failure
            notify_etl_failure(data)
    
    return jsonify({'status': 'received'})

def process_new_budget_data():
    # Your business logic here
    print("New budget data processed successfully!")
    
def notify_etl_failure(error_data):
    # Send alerts, notifications, etc.
    print(f"ETL failed: {error_data}")
```

## 🐳 Method 5: Multi-Stack Deployment

### Complete Integration Stack

```yaml
# complete-stack/docker-compose.yaml
version: '3.8'

services:
  # Your web application
  web-app:
    image: your-web-app:latest
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=postgresql://airflow:airflow@budget-postgres:5432/airflow
      - AIRFLOW_API=http://budget-airflow:8080
    depends_on:
      - budget-postgres
    networks:
      - app-network

  # Budget ETL Services (reference existing compose)
  budget-postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: airflow
      POSTGRES_PASSWORD: airflow
      POSTGRES_DB: airflow
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - app-network

  budget-airflow:
    # Your custom Airflow image with ETL DAGs
    build: ./budget-etl
    environment:
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@budget-postgres/airflow
    depends_on:
      - budget-postgres
    networks:
      - app-network

  # Optional: Load balancer
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - web-app
    networks:
      - app-network

networks:
  app-network:
    driver: bridge

volumes:
  postgres_data:
```

## 🔒 Security Considerations

### Production Environment Variables

```bash
# .env for production
DB_USER=secure_db_user
DB_PASSWORD=strong_random_password
DB_NAME=budget_production

PGADMIN_EMAIL=admin@yourcompany.com
PGADMIN_PASSWORD=secure_pgadmin_password

# Generate these keys
AIRFLOW_FERNET_KEY=your_32_byte_fernet_key
AIRFLOW_SECRET_KEY=your_secret_key

# Enable authentication
AIRFLOW__WEBSERVER__AUTHENTICATE=True
AIRFLOW__WEBSERVER__AUTH_BACKEND=airflow.providers.fab.auth_manager.fab_auth_manager.FabAuthManager
```

### Secure Network Configuration

```yaml
# Restrict network access
services:
  postgres:
    # Don't expose to host in production
    # ports:
    #   - "5432:5432"
    networks:
      - internal-network

networks:
  internal-network:
    driver: bridge
    internal: true  # No external access
```

## 📋 Best Practices

1. **Use environment variables** for all configuration
2. **Implement health checks** for all services  
3. **Set up monitoring** and logging
4. **Use secrets management** for production
5. **Implement backup strategies** for data
6. **Test integration** in staging environment
7. **Document API contracts** and database schemas
8. **Set up CI/CD pipelines** for automated deployments

## 🔧 Troubleshooting Integration

### Network Issues
```bash
# Check network connectivity
docker network ls
docker network inspect airflow_docker_default

# Test connection between containers
docker exec -it your-app ping postgres
```

### API Issues
```bash
# Test Airflow API
curl -u airflow:airflow http://localhost:8090/api/v1/health

# Check API authentication
curl -u airflow:airflow http://localhost:8090/api/v1/dags
```

### Database Issues
```bash
# Test database connection
docker exec -it postgres_container psql -U airflow -d airflow -c "\dt budget.*"
```