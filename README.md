# Municipal Budget ETL - Docker Setup

Complete ETL pipeline for processing municipal budget data using Apache Airflow, PostgreSQL, and pgAdmin.

## 🚀 Quick Start

### Prerequisites
- Docker Desktop installed and running
- Git installed
- At least 4GB RAM allocated to Docker

### One-Command Setup

**Windows:**
```cmd
git clone <YOUR_REPO_URL>
cd bi_demo_project/airflow_docker
setup.bat
```

**Linux/Mac:**
```bash
git clone <YOUR_REPO_URL>
cd bi_demo_project/airflow_docker
chmod +x setup.sh && ./setup.sh
```

### Manual Setup
```bash
git clone <YOUR_REPO_URL>
cd bi_demo_project/airflow_docker
cp .env.example .env
docker-compose up -d
```

## 🌐 Access Points
- **Airflow UI**: http://localhost:8090 (airflow/airflow)
- **pgAdmin**: http://localhost:8081 (admin@admin.com/admin) 
- **PostgreSQL**: localhost:5432 (airflow/airflow)

## 📊 ETL Pipeline
The `budget_municipal_etl` DAG processes Excel files through:
1. **Extract** - Read Excel sheets
2. **Transform** - Clean and standardize data
3. **Load** - Store in PostgreSQL with `budget` schema
4. **Validate** - Data quality checks

## 🔧 Integration Options

### As Microservice
```yaml
# In your docker-compose.yaml
services:
  your-app:
    depends_on:
      - budget-etl-postgres
    networks:
      - budget-etl-network

networks:
  budget-etl-network:
    external: true
    name: airflow_docker_default
```

### API Access
- Airflow REST API: `http://localhost:8090/api/v1/`
- Direct DB access: `postgresql://airflow:airflow@localhost:5432/airflow`

## 📁 Project Structure
```
airflow_docker/
├── dags/                   # Airflow DAGs
├── data/                   # Input Excel files
├── docker-compose.yaml     # Main services
├── setup.bat/.sh          # Quick setup scripts
└── README.md              # This file
```

## 🛠️ Development
- Place Excel files in `data/` directory
- Edit DAGs in `dags/` directory (auto-reloaded)
- Use `budget_data_queries.sql` for database exploration

## 📋 Useful Commands
```bash
# View all logs
docker-compose logs -f

# Restart specific service
docker-compose restart airflow-scheduler

# Stop everything
docker-compose down

# Clean restart
docker-compose down -v && docker-compose up -d
```

For detailed setup instructions, see [TEAM_SETUP.md](TEAM_SETUP.md)