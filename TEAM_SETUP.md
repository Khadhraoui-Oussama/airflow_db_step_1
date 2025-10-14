# Team Setup Guide

## 🚀 Quick Start for Team Members

### Prerequisites
- Docker Desktop (with 4GB+ RAM allocation)
- Git

### Automated Setup

**Windows:**
```cmd
git clone <REPO_URL>
cd bi_demo_project/airflow_docker
setup.bat
```

**Linux/Mac:**
```bash
git clone <REPO_URL>
cd bi_demo_project/airflow_docker  
chmod +x setup.sh && ./setup.sh
```

### Manual Setup
1. Clone repository and navigate to airflow_docker folder
2. Copy `.env.example` to `.env` (customize if needed)
3. Run: `docker-compose up -d`
4. Wait 2-3 minutes for services to start

## 🌐 Access Services

### Airflow Web UI
- **URL**: http://localhost:8090
- **Login**: airflow / airflow
- **Actions**: Enable and trigger the `budget_municipal_etl` DAG

### pgAdmin (Database Management)
- **URL**: http://localhost:8081
- **Login**: admin@admin.com / admin
- **Database Connection**:
  - Host: `postgres`
  - Port: 5432
  - Database: `airflow`  
  - Username: `airflow`
  - Password: `airflow`

## 🔄 Running the ETL

1. Access Airflow UI (http://localhost:8090)
2. Find `budget_municipal_etl` DAG
3. Toggle ON to enable it
4. Click "Trigger DAG" button
5. Monitor progress in Graph/Grid view
6. Check results in pgAdmin under `budget` schema

## 📁 Working with Data

### Input Files
- Place Excel files in `data/` directory
- Default file: `Budget_municipal.xlsx`

### Output Location
- **Raw data**: `output/` directory
- **Processed data**: `processed/` directory
- **Database**: PostgreSQL `budget` schema

### Database Tables
- `budget.budget_data` - Main processed records
- `budget.budget_summary` - Aggregated summaries
- `budget.etl_audit` - Pipeline execution logs

## 🛠️ Development Workflow

### Making Changes
```bash
# Edit DAGs (auto-reloaded)
nano dags/budget_municipal_etl.py

# View logs
docker-compose logs -f airflow-scheduler

# Restart services after config changes
docker-compose restart
```

### Common Commands
```bash
# Check status
docker-compose ps

# View specific service logs
docker-compose logs postgres
docker-compose logs airflow-worker

# Shell access
docker-compose exec postgres psql -U airflow
docker-compose exec airflow-scheduler bash

# Clean restart (loses data!)
docker-compose down -v && docker-compose up -d
```

## 🔧 Troubleshooting

### Port Conflicts
Edit `docker-compose.yaml` and change port mappings:
- Airflow: `"8090:8080"` → `"XXXX:8080"`
- pgAdmin: `"8081:80"` → `"XXXX:80"`
- PostgreSQL: `"5432:5432"` → `"XXXX:5432"`

### Services Won't Start
1. Ensure Docker Desktop is running
2. Check available RAM (need 4GB+)
3. Verify ports aren't in use: `netstat -an | findstr :8090`

### DAG Issues
1. Check Python syntax in DAG files
2. View scheduler logs: `docker-compose logs airflow-scheduler`
3. Wait 1-2 minutes for DAG refresh

### Database Connection Issues
1. Ensure all services are running: `docker-compose ps`
2. Check PostgreSQL logs: `docker-compose logs postgres`
3. Verify credentials in pgAdmin setup

## 🔗 Integration Examples

### Connect External App
```yaml
# your-app's docker-compose.yaml
services:
  your-app:
    networks:
      - airflow_docker_default
    environment:
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_NAME=airflow
      - DB_USER=airflow
      - DB_PASS=airflow

networks:
  airflow_docker_default:
    external: true
```

### API Access
```python
# Access Airflow REST API
import requests

# Trigger DAG
response = requests.post(
    'http://localhost:8090/api/v1/dags/budget_municipal_etl/dagRuns',
    json={'conf': {}},
    auth=('airflow', 'airflow')
)
```

### Direct Database Access
```python
# Connect to PostgreSQL from external app
import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='airflow', 
    user='airflow',
    password='airflow'
)

# Query budget data
cursor = conn.cursor()
cursor.execute("SELECT * FROM budget.budget_data LIMIT 10")
```

## 📊 Useful Queries

Use `budget_data_queries.sql` in pgAdmin for:
- Budget summaries by category
- ETL execution status
- Data quality checks
- Top budget items

## 🔐 Production Notes

For production deployment:
1. Change default passwords
2. Use environment variables for secrets
3. Set up proper authentication
4. Configure data backups
5. Monitor resource usage

## 💬 Support

- Check main README.md for architecture details
- Review Docker Compose logs for errors
- Ensure all prerequisites are met
- Verify firewall/antivirus isn't blocking Docker