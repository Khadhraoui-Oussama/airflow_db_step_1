# 🚀 Sharing Your Budget ETL Pipeline

## GitHub Setup Instructions

### 1. Create GitHub Repository
```bash
# If you don't have a GitHub repo yet:
# 1. Go to GitHub.com
# 2. Click "New Repository"
# 3. Name it: "municipal-budget-etl" or similar
# 4. Make it Public (for sharing) or Private (for team only)
# 5. Don't initialize with README (you already have files)
```

### 2. Push to GitHub
```bash
# Add GitHub remote (replace with your actual repo URL)
git remote add origin https://github.com/YOUR_USERNAME/municipal-budget-etl.git

# Push your code
git branch -M main
git push -u origin main
```

### 3. Share Repository URL
Send team members this link:
```
https://github.com/YOUR_USERNAME/municipal-budget-etl
```

## 🤝 For Team Members

### Quick Start
1. Clone the repository
2. Run setup script (`setup.bat` on Windows or `setup.sh` on Linux/Mac)  
3. Access Airflow UI at http://localhost:8090
4. Enable and trigger the ETL DAG

### Detailed Instructions
See [TEAM_SETUP.md](TEAM_SETUP.md) for comprehensive setup guide

## 🔗 Integration with Other Projects

### As a Submodule
```bash
# Add to existing project as submodule
git submodule add https://github.com/YOUR_USERNAME/municipal-budget-etl.git etl

# Initialize submodule
git submodule update --init --recursive
```

### Docker Compose Integration
```yaml
# In your main project's docker-compose.yaml
services:
  your-app:
    # ... your app config
    depends_on:
      - etl-postgres
    networks:
      - etl-network

  etl-postgres:
    extends:
      file: etl/docker-compose.yaml
      service: postgres
    networks:
      - etl-network

networks:
  etl-network:
    driver: bridge
```

### Via Docker Networks
```bash
# Start ETL services
cd etl && docker-compose up -d

# Connect your app to ETL network
docker run --network etl_default your-app:latest
```

## 📦 Distribution Options

### 1. GitHub Releases
- Tag versions: `git tag v1.0.0 && git push origin v1.0.0`
- Create releases with change logs
- Attach compiled assets if needed

### 2. Docker Hub
```bash
# Build and push custom image
docker build -t your-username/budget-etl:latest .
docker push your-username/budget-etl:latest
```

### 3. Package as Docker Image
```dockerfile
# Create distribution Dockerfile
FROM docker:latest
COPY . /app
WORKDIR /app
CMD ["docker-compose", "up", "-d"]
```

## 🔒 Security for Sharing

### Public Repositories
- ✅ Include `.env.example` with safe defaults
- ❌ Never commit `.env` with real secrets
- ✅ Document security considerations
- ✅ Use placeholder values in examples

### Private Team Repositories  
- ✅ Share real configurations via secure channels
- ✅ Use organization secrets in CI/CD
- ✅ Implement proper access controls

## 📊 Monitoring Shared Deployments

### Health Check Endpoint
```bash
# Check if services are healthy
curl http://localhost:8090/health
curl http://localhost:8081/
```

### Automated Testing
```yaml
# GitHub Actions example (.github/workflows/test.yml)
name: Test ETL Pipeline

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Start services
        run: |
          cp .env.example .env
          docker-compose up -d
          sleep 60
      - name: Test services
        run: |
          curl -f http://localhost:8090/health
          docker-compose exec -T postgres psql -U airflow -d airflow -c "\dt"
```

## 📋 Support for Team Members

### Common Issues & Solutions

**Port Conflicts:**
- Edit `docker-compose.yaml` ports section
- Or use: `docker-compose up -d --scale postgres=0` to skip conflicting services

**Permission Issues:**
- Windows: Run Docker Desktop as Administrator
- Linux: Add user to docker group: `sudo usermod -aG docker $USER`

**Memory Issues:**
- Increase Docker Desktop memory allocation to 4GB+
- Or reduce services: `docker-compose up postgres pgladmin` (minimal setup)

### Getting Help
1. Check [TEAM_SETUP.md](TEAM_SETUP.md) for detailed troubleshooting
2. Review [INTEGRATION.md](INTEGRATION.md) for integration examples  
3. Check Docker Compose logs: `docker-compose logs`
4. Create GitHub issue for bugs or questions

## 🎯 Next Steps After Sharing

1. **Documentation**: Add project-specific details to README
2. **CI/CD**: Set up automated testing and deployment
3. **Monitoring**: Add logging and alerting for production use
4. **Security**: Implement proper authentication and secrets management
5. **Scaling**: Consider Kubernetes deployment for production