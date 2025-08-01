# ME_CORE_Backend_mar_spar - Fly.io Deployment Guide

Production deployment configuration for the HiveMemory Dashboard FastAPI backend.

## 🚀 Quick Deployment

### Prerequisites

1. **Install Fly.io CLI**:
   ```bash
   # macOS
   brew install flyctl
   
   # Linux/WSL
   curl -L https://fly.io/install.sh | sh
   
   # Windows
   iwr https://fly.io/install.ps1 -useb | iex
   ```

2. **Authenticate with Fly.io**:
   ```bash
   flyctl auth login
   ```

3. **Create Fly.io App** (first time only):
   ```bash
   flyctl apps create me-core-backend-mar-spar
   ```

### Deploy

```bash
# Run the automated deployment script
./deploy.sh
```

**Or deploy manually:**

```bash
# Create persistent volume (first time only)
flyctl volumes create me_core_memory_vol --region dfw --size 1 --app me-core-backend-mar-spar

# Set environment variables
flyctl secrets set ENVIRONMENT=production LOG_LEVEL=INFO --app me-core-backend-mar-spar

# Deploy
flyctl deploy --ha=false
```

## 📋 Configuration Overview

### Application Configuration (`fly.toml`)

- **App Name**: `me-core-backend-mar-spar`
- **Primary Region**: `dfw` (Dallas)
- **Port**: 8000 (internal)
- **Scaling**: Auto-start/stop enabled for cost efficiency
- **Health Checks**: HTTP health check at `/health`
- **Persistent Storage**: 1GB volume mounted at `/mnt/memory`

### Docker Configuration

- **Base Image**: `python:3.11-slim`
- **Multi-stage Build**: Optimized production image
- **Security**: Non-root user execution
- **Health Check**: Built-in container health checking
- **Port**: 8000 (configurable via PORT env var)

### Resource Allocation

- **CPU**: 1 shared vCPU
- **Memory**: 512MB RAM
- **Storage**: 1GB persistent volume
- **Scaling**: 1 instance (can be increased)

## 🔧 Environment Variables

### Production Secrets

Set via `flyctl secrets set`:

```bash
flyctl secrets set \
  ENVIRONMENT=production \
  LOG_LEVEL=INFO \
  --app me-core-backend-mar-spar
```

### Environment Configuration

Built into `fly.toml`:
- `PYTHONUNBUFFERED=1`
- `PYTHONDONTWRITEBYTECODE=1`
- `PORT=8000`

## 🏥 Health Monitoring

### Health Check Endpoint

- **URL**: `GET /health`
- **Response**: `{"status": "healthy", "timestamp": "..."}`
- **Interval**: 30 seconds
- **Timeout**: 5 seconds

### Monitoring Commands

```bash
# Check application status
flyctl status --app me-core-backend-mar-spar

# View real-time logs
flyctl logs --app me-core-backend-mar-spar

# SSH into container
flyctl ssh console --app me-core-backend-mar-spar

# Check resource usage
flyctl scale show --app me-core-backend-mar-spar
```

## 🗂️ File Structure After Deployment

```
/app/
├── main.py              # FastAPI application
├── production.py        # Production configuration
├── requirements.txt     # Python dependencies
├── agents/              # Agent configuration files
├── logs/               # Application logs
└── ...                 # Other application files

/mnt/memory/            # Persistent volume (agent memory)
├── {agent_id}/
│   ├── observer_stream/
│   └── core_memory/
```

## 🔐 Security Features

### Docker Security
- Non-root user execution
- Minimal base image (python:3.11-slim)
- Multi-stage build reduces attack surface
- Health checks for container monitoring

### Network Security
- HTTPS enforcement
- Configurable CORS origins
- Security headers in health checks

### Access Control
- Environment-based configuration
- Secrets management via Fly.io
- Isolated file system permissions

## 📊 API Endpoints

### Base URL
- **Production**: `https://me-core-backend-mar-spar.fly.dev`
- **API Docs**: `https://me-core-backend-mar-spar.fly.dev/docs`

### Key Endpoints
- `GET /health` - Health check
- `GET /api/agents` - List all agents
- `POST /api/agents/control` - Control agents
- `GET /api/memory/files` - Memory file management
- `WS /ws` - WebSocket for real-time updates

## 🧪 Testing Deployment

### Health Check
```bash
curl https://me-core-backend-mar-spar.fly.dev/health
```

### WebSocket Connection
```javascript
const ws = new WebSocket('wss://me-core-backend-mar-spar.fly.dev/ws');
ws.onmessage = (event) => console.log(JSON.parse(event.data));
```

### API Documentation
Visit: `https://me-core-backend-mar-spar.fly.dev/docs`

## 🔄 Scaling & Updates

### Scale Resources
```bash
# Scale memory
flyctl scale memory 1024 --app me-core-backend-mar-spar

# Scale CPU
flyctl scale vm shared-cpu-2x --app me-core-backend-mar-spar

# Scale instances
flyctl scale count 2 --app me-core-backend-mar-spar
```

### Update Application
```bash
# Deploy changes
flyctl deploy --app me-core-backend-mar-spar

# Rolling restart (zero downtime)
flyctl apps restart me-core-backend-mar-spar
```

## 🐛 Troubleshooting

### Common Issues

1. **App won't start**:
   ```bash
   flyctl logs --app me-core-backend-mar-spar
   ```

2. **Health check failing**:
   ```bash
   flyctl ssh console --app me-core-backend-mar-spar
   curl localhost:8000/health
   ```

3. **Memory issues**:
   ```bash
   flyctl scale memory 1024 --app me-core-backend-mar-spar
   ```

4. **Volume mount issues**:
   ```bash
   flyctl volumes list --app me-core-backend-mar-spar
   flyctl ssh console --app me-core-backend-mar-spar
   ls -la /mnt/memory
   ```

### Debug Commands
```bash
# SSH into container
flyctl ssh console --app me-core-backend-mar-spar

# Check file permissions
ls -la /app /mnt/memory

# Check Python environment
python --version
pip list

# Test endpoints locally
curl localhost:8000/health
```

## 💰 Cost Optimization

### Current Configuration
- **Shared CPU**: ~$1.94/month
- **512MB RAM**: ~$2.32/month  
- **1GB Storage**: ~$0.15/month
- **Total**: ~$4.41/month (when running 24/7)

### Cost Savings
- **Auto-stop/start**: Reduces costs when idle
- **Single instance**: Minimal for development/testing
- **Shared CPU**: Most cost-effective option

### Production Scaling
For production loads, consider:
- Dedicated CPU for better performance
- Multiple instances for high availability
- Larger memory allocation for heavy workloads

## 🎯 Production Recommendations

### Before Production
1. **Configure CORS**: Update allowed origins in production
2. **SSL Certificates**: Fly.io provides automatic HTTPS
3. **Monitoring**: Set up application monitoring
4. **Backups**: Regular volume snapshots
5. **Secrets**: Audit and rotate secrets regularly

### Security Checklist
- [ ] Configure proper CORS origins
- [ ] Review and set appropriate secrets
- [ ] Enable logging and monitoring
- [ ] Test health checks and endpoints
- [ ] Verify volume permissions and access
- [ ] Set up backup strategy

## 📞 Support

- **Fly.io Documentation**: https://fly.io/docs/
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **Application Logs**: `flyctl logs --app me-core-backend-mar-spar`
- **Status Page**: `flyctl status --app me-core-backend-mar-spar`