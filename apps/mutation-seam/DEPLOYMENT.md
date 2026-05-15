# Mutation Seam — Deployment Guide

## Local Development

### Prerequisites
- Python 3.10+
- pip or uv
- curl or Postman (for testing)

### Setup
```bash
cd apps/mutation-seam
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

Visit `http://localhost:8000/health` to verify.

Public-host note:

1. the repository now carries a bounded app-local Render blueprint at `apps/mutation-seam/render.yaml`
2. the intended public host contract is `https://mutation-seam.apexpowerops.com`
3. `apps/operations-web` now proxies PM-facing same-origin `/api/v1/{reads,schedule,mutations}` traffic to that hosted seam through `MUTATION_SEAM_BASE_URL`

---

## Running Tests

### Full Suite
```bash
pytest tests/ -v
```

### With Coverage
```bash
pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html
```

### Single Test
```bash
pytest tests/test_envelope_validation.py::test_valid_apparatus_status_update_succeeds -v
```

---

## Docker Deployment (Future)

When ready to containerize:

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml
```yaml
version: '3.9'

services:
  mutation-seam:
    build: .
    ports:
      - "8000:8000"
    environment:
      - PORT=8000
      - LOG_LEVEL=INFO
      - JWT_SECRET=your-secret-key
    volumes:
      - ./app:/app/app  # For development only
```

### Build & Run
```bash
docker build -t apex-mutation-seam .
docker run -p 8000:8000 apex-mutation-seam
```

---

## Kubernetes Deployment (Future)

### ConfigMap
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: mutation-seam-config
data:
  PORT: "8000"
  LOG_LEVEL: "INFO"
```

### Secret
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: mutation-seam-secrets
type: Opaque
stringData:
  JWT_SECRET: "your-production-secret-key"
```

### Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mutation-seam
spec:
  replicas: 2
  selector:
    matchLabels:
      app: mutation-seam
  template:
    metadata:
      labels:
        app: mutation-seam
    spec:
      containers:
      - name: mutation-seam
        image: apex-mutation-seam:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: mutation-seam-config
        - secretRef:
            name: mutation-seam-secrets
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
```

### Service
```yaml
apiVersion: v1
kind: Service
metadata:
  name: mutation-seam
spec:
  selector:
    app: mutation-seam
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 8000 | Server port |
| `LOG_LEVEL` | INFO | Logging level |
| `JWT_SECRET` | dev-secret-key-change-in-production | JWT signing key |
| `CORS_ORIGINS` | See config.py | Allowed CORS origins |

### Production Setup
```bash
export PORT=8000
export LOG_LEVEL=INFO
export JWT_SECRET=$(openssl rand -base64 32)
```

Hosted ingress setup:

```bash
export CORS_ORIGINS=https://operations.apexpowerops.com,https://mutation-seam.apexpowerops.com
export SEAM_STORE_BACKEND=postgres
export SEAM_DATABASE_URL=<hosted database dsn>
```

---

## Monitoring & Logging

### Health Checks
- **Endpoint:** `GET /health`
- **Interval:** 30 seconds
- **Timeout:** 10 seconds

Hosted route validation:

```bash
python scripts/smoke_deployed_mutation_seam.py --base-url https://mutation-seam.apexpowerops.com
```

### Metrics (Future)
Will expose Prometheus metrics at `/metrics`:
```
mutation_requests_total{action_type="...",status="..."}
mutation_request_duration_seconds{action_type="..."}
mutation_errors_total{code="..."}
```

### Logging
Structured JSON logs to stdout:
```json
{
  "timestamp": "2026-04-16T14:30:05Z",
  "level": "INFO",
  "message": "Mutation accepted",
  "mutation_id": "mut-abc123",
  "entity_id": "app-001",
  "action_type": "update_apparatus_status",
  "actor_id": "tech-001"
}
```

---

## Scaling Strategy

### Stateless Design
- No session state (each request is independent)
- In-memory store (will be replaced by Supabase)
- Safe to run multiple instances behind load balancer

### Load Balancing
```nginx
upstream mutation_seam {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}

server {
    listen 80;
    location /api {
        proxy_pass http://mutation_seam;
        proxy_set_header X-Forwarded-For $remote_addr;
    }
}
```

### Horizontal Scaling
```bash
# Run 3 instances on different ports
for i in 0 1 2; do
  port=$((8000 + i))
  uvicorn app.main:app --port $port &
done
```

---

## Database Migration (Phase 2)

When connecting to Supabase:

### 1. Update Dependencies
```bash
pip install supabase-py
```

### 2. Create Supabase Client
```python
# app/db/supabase_store.py
from supabase import create_client

supabase = create_client(
    url=os.getenv("SUPABASE_URL"),
    key=os.getenv("SUPABASE_ANON_KEY")
)
```

### 3. Replace Memory Store
```python
# In app/services/mutation_pipeline.py
from app.db.supabase_store import supabase

entity_store = supabase.table(entity_type).select("*").execute()
```

### 4. Add Migrations
Run Supabase migrations to create tables matching in-memory schema.

---

## CI/CD Pipeline (GitHub Actions Example)

### .github/workflows/test.yml
```yaml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - run: pip install -r requirements.txt pytest pytest-cov
    - run: pytest tests/ --cov=app --cov-report=xml
    - uses: codecov/codecov-action@v3
      with:
        files: ./coverage.xml
```

### .github/workflows/deploy.yml
```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - run: docker build -t apex-mutation-seam .
    - run: docker push ${{ secrets.REGISTRY }}/apex-mutation-seam:latest
    - run: kubectl rollout restart deployment/mutation-seam
```

---

## Performance Considerations

### Current (In-Memory)
- Sub-millisecond latency
- No persistence
- Data lost on restart

### Phase 2 (Supabase)
- Network latency: 50-200ms
- Persistent storage
- Built-in replication

### Optimization Tips
1. Add connection pooling to Supabase client
2. Cache frequently accessed entities
3. Batch mutations when possible
4. Use readonly replicas for analytics queries

---

## Security Checklist

- [ ] Change `JWT_SECRET` in production
- [ ] Enable HTTPS for all endpoints
- [ ] Restrict CORS origins to known domains
- [ ] Use environment variables for secrets (never hardcode)
- [ ] Enable database row-level security (RLS) in Supabase
- [ ] Add rate limiting to prevent abuse
- [ ] Log all mutations to audit trail (already done)
- [ ] Use secrets manager (AWS Secrets, HashiCorp Vault)
- [ ] Enable request signing for Supabase
- [ ] Rotate JWT secrets regularly

---

## Backup & Recovery

### In-Memory (Dev Only)
- No backup needed (ephemeral)

### Supabase (Production)
- Automatic backups (every 24h)
- Point-in-time recovery (30-day window)
- Manual backups via Supabase dashboard

### Disaster Recovery
1. Supabase outage → Switch to read-only fallback
2. Corrupted data → Restore from backup
3. Lost mutations → Check audit log

---

## Troubleshooting Deployment

### Port Already in Use
```bash
lsof -i :8000
kill -9 <PID>
```

### Import Errors
```bash
pip install -r requirements.txt --force-reinstall
python -c "import app.main; print('OK')"
```

### Test Failures in Production
```bash
# Run tests with production config
JWT_SECRET=your-prod-secret pytest tests/ -v
```

### Memory Leaks
```bash
# Monitor with memory profiler
pip install memory-profiler
python -m memory_profiler app/main.py
```

---

## Rollback Plan

If deployment fails:

### Code Rollback
```bash
git revert <commit-hash>
docker build -t apex-mutation-seam .
docker push ${{ secrets.REGISTRY }}/apex-mutation-seam:latest
kubectl rollout restart deployment/mutation-seam
```

### Database Rollback
```bash
# Via Supabase dashboard
# 1. Open Backups tab
# 2. Select restore point
# 3. Click "Restore"
```

---

## Maintenance Windows

Recommended:
- **Frequency:** Monthly (2nd Tuesday)
- **Duration:** 30 minutes
- **Window:** 2-3 AM UTC

Notify users 48h in advance.

---

## Support & Escalation

| Issue | Owner | Response |
|-------|-------|----------|
| API errors | DevOps | 15 min |
| Database issues | Database team | 30 min |
| Performance degradation | DevOps | 30 min |
| Security incident | Security team | 5 min |

---

_See QUICKSTART.md for local development setup._  
_See ARCHITECTURE.md for system design._
