# Fly.io Deployment Research for ME_CORE_Backend_mar_spar

## Executive Summary

This document provides comprehensive deployment requirements and best practices for deploying a Node.js backend with MongoDB to fly.io. The research covers all essential aspects from Docker configuration to production security.

## 1. Core Deployment Requirements

### 1.1 Dockerfile Requirements

**Critical Requirements:**
- Dockerfile must be named exactly `Dockerfile` or `dockerfile`
- Must use Node.js slim base image for production
- Multi-stage build pattern recommended for optimization
- Must bind to `0.0.0.0` (not localhost) and use PORT environment variable

**Recommended Dockerfile Structure:**
```dockerfile
# syntax = docker/dockerfile:1
ARG NODE_VERSION=18.15.0
FROM node:${NODE_VERSION}-slim as base
LABEL fly_launch_runtime="NodeJS"
WORKDIR /app
ENV NODE_ENV=production

FROM base as build
RUN apt-get update -qq && \
    apt-get install -y python-is-python3 pkg-config build-essential
COPY --link package.json package-lock.json .
RUN npm install --production=false
COPY --link . .
RUN npm prune --production

FROM base
COPY --from=build /app /app
EXPOSE 8080
CMD [ "npm", "run", "start" ]
```

### 1.2 Package.json Configuration

**Essential Requirements:**
```json
{
  "engines": {
    "node": "18.x"
  },
  "scripts": {
    "start": "node server.js"
  }
}
```

### 1.3 Server Configuration

**Critical Server Setup:**
```javascript
const hostname = "0.0.0.0";  // Must bind to all interfaces
const port = process.env.PORT || 8080;  // Use Fly.io's PORT env var

app.listen(port, hostname, () => {
  console.log(`Server running at http://${hostname}:${port}/`);
});
```

## 2. MongoDB Connection Best Practices

### 2.1 Connection Strategy

**Recommended Approach:**
- Use MongoDB Atlas (managed service)
- Store connection string in Fly.io secrets
- Never hardcode credentials
- Use environment variables exclusively

### 2.2 Connection String Management

**Setup Commands:**
```bash
# Set MongoDB connection string as a Fly secret
flyctl secrets set MONGODB_URI="mongodb+srv://username:password@cluster.mongodb.net/database?retryWrites=true&w=majority"

# Verify secrets are set
flyctl secrets list
```

**Application Code:**
```javascript
require('dotenv').config();
const mongoose = require('mongoose');

// Use environment variable for connection
const mongoUri = process.env.MONGODB_URI;
mongoose.connect(mongoUri, {
  useNewUrlParser: true,
  useUnifiedTopology: true
});
```

### 2.3 MongoDB Atlas Network Configuration

**Critical Security Steps:**
1. Configure IP whitelist in MongoDB Atlas
2. For Fly.io deployment, you may need to "Allow access from anywhere" due to dynamic IPs
3. Ensure strong authentication is configured
4. Use VPC peering if available for enhanced security

## 3. Environment Variables and Secrets

### 3.1 Essential Environment Variables

**Required Variables:**
```bash
# Production essentials
NODE_ENV=production
PORT=8080

# Database connection
MONGODB_URI=mongodb+srv://...  # Set as secret

# Security
JWT_SECRET=your-jwt-secret     # Set as secret
API_KEY=your-api-key          # Set as secret
```

### 3.2 Secrets Management

**Security Best Practices:**
- Use `flyctl secrets set` for sensitive data
- Secrets are encrypted in Fly.io's vault
- Available as environment variables at runtime
- Never logged or exposed in build process
- Use `--stage` option to deploy secrets later

**Commands:**
```bash
# Set individual secrets
flyctl secrets set JWT_SECRET="your-jwt-secret"
flyctl secrets set API_KEY="your-api-key"

# Import multiple secrets from file
flyctl secrets import < secrets.env
```

## 4. Health Check Configuration

### 4.1 Health Check Endpoint

**Recommended Implementation:**
```javascript
// Add health check endpoint
app.get('/health', (req, res) => {
  res.status(200).json({ 
    status: 'ok',
    timestamp: new Date().toISOString(),
    uptime: process.uptime()
  });
});

// More comprehensive health check
app.get('/health/detailed', async (req, res) => {
  try {
    // Test database connection
    await mongoose.connection.db.admin().ping();
    res.status(200).json({
      status: 'healthy',
      database: 'connected',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    res.status(503).json({
      status: 'unhealthy',
      database: 'disconnected',
      error: error.message
    });
  }
});
```

### 4.2 fly.toml Health Check Configuration

**Recommended Configuration:**
```toml
app = "me-core-backend"
primary_region = "sin"  # Singapore for optimal performance

[env]
  PORT = "8080"
  NODE_ENV = "production"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 1
  
  [[http_service.checks]]
    grace_period = "10s"
    interval = "30s"
    method = "GET"
    timeout = "5s"
    path = "/health"
    
  [[http_service.checks]]
    grace_period = "15s"
    interval = "60s"
    method = "GET"
    timeout = "10s"
    path = "/health/detailed"

[[services]]
  internal_port = 8080
  protocol = "tcp"
  
  [[services.tcp_checks]]
    grace_period = "1s"
    interval = "15s"
    timeout = "2s"
```

## 5. Optimal Regions and Performance

### 5.1 Region Selection

**Recommended Regions for Global Coverage:**
- **Primary**: `sin` (Singapore) - Asia-Pacific hub
- **Secondary**: `fra` (Frankfurt) - Europe
- **Tertiary**: `iad` (Virginia) - North America East
- **Optional**: `syd` (Sydney) - Australia/Oceania

### 5.2 Scaling Configuration

**Auto-scaling Setup:**
```toml
[http_service]
  min_machines_running = 1
  max_machines_running = 10
  auto_stop_machines = true
  auto_start_machines = true

[[services]]
  concurrency.type = "requests"
  concurrency.hard_limit = 25
  concurrency.soft_limit = 20
```

### 5.3 Performance Optimization

**Node.js Specific Optimizations:**
```bash
# For applications needing more memory
flyctl machine update --vm-memory 512  # or 1024, 2048

# For CPU-intensive applications
flyctl machine update --vm-cpus 2

# Scale to multiple regions
flyctl scale count 2 --region sin,fra
```

## 6. Security Configuration

### 6.1 Essential Security Headers

**Middleware Configuration:**
```javascript
const helmet = require('helmet');
const cors = require('cors');

app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      scriptSrc: ["'self'"],
      imgSrc: ["'self'", "data:", "https:"]
    }
  }
}));

app.use(cors({
  origin: process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:3000'],
  credentials: true
}));
```

### 6.2 Rate Limiting

```javascript
const rateLimit = require('express-rate-limit');

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100 // limit each IP to 100 requests per windowMs
});

app.use('/api/', limiter);
```

## 7. Deployment Commands and Workflow

### 7.1 Initial Deployment

```bash
# Initialize fly.io app
flyctl apps create me-core-backend --region sin

# Set secrets before first deployment
flyctl secrets set MONGODB_URI="your-connection-string"
flyctl secrets set JWT_SECRET="your-jwt-secret"

# Deploy application
flyctl deploy

# Check deployment status
flyctl status
flyctl logs
```

### 7.2 Production Deployment Checklist

**Pre-deployment:**
- [ ] Dockerfile optimized for production
- [ ] All secrets configured via flyctl
- [ ] Health check endpoints implemented
- [ ] MongoDB Atlas network access configured
- [ ] Environment variables set in fly.toml
- [ ] Rate limiting implemented
- [ ] Security headers configured

**Post-deployment:**
- [ ] Health checks passing
- [ ] Database connectivity verified
- [ ] SSL certificates active
- [ ] Logs monitoring configured
- [ ] Scaling parameters tested

## 8. Monitoring and Maintenance

### 8.1 Essential Monitoring

```bash
# Monitor application health
flyctl status
flyctl logs --follow

# Check machine status
flyctl machines list
flyctl machines status <machine-id>

# Monitor health checks
flyctl checks list
```

### 8.2 Scaling Commands

```bash
# Scale machines in specific regions
flyctl scale count 3 --region sin
flyctl scale count 2 --region fra

# Update machine specifications
flyctl machine update --vm-memory 1024 --vm-cpus 2

# Auto-scaling configuration
flyctl autoscale set min=1 max=5
```

## 9. Common Issues and Solutions

### 9.1 Connection Issues

**Problem**: "app is not listening on the expected address"
**Solution**: Ensure server binds to `0.0.0.0` and uses `process.env.PORT`

**Problem**: MongoDB connection failures
**Solution**: Check MongoDB Atlas IP whitelist and connection string format

### 9.2 Build Issues

**Problem**: Native dependencies failing to compile
**Solution**: Use `npm install --legacy-peer-deps` in Dockerfile

**Problem**: Build stage secrets not available
**Solution**: Use build-time secrets or move secret-dependent operations to runtime

## 10. Action Items for ME_CORE_Backend_mar_spar

### Immediate Actions:
1. **Create Dockerfile** with multi-stage build configuration
2. **Configure fly.toml** with health checks and scaling parameters
3. **Set up MongoDB connection** using environment variables
4. **Implement health check endpoints** for monitoring
5. **Configure secrets management** for sensitive data

### Pre-deployment Actions:
1. **Test Docker build locally** to ensure compatibility
2. **Set up MongoDB Atlas** with appropriate network access
3. **Configure all environment variables** and secrets
4. **Implement security middleware** (helmet, cors, rate limiting)
5. **Create monitoring endpoints** for application health

### Post-deployment Actions:
1. **Monitor deployment logs** for any issues
2. **Test all API endpoints** in production environment
3. **Verify database connectivity** and performance
4. **Configure scaling parameters** based on load testing
5. **Set up alerting** for health check failures

## Conclusion

This research provides a comprehensive foundation for deploying ME_CORE_Backend_mar_spar to fly.io with production-ready configuration, security, and scalability. The key success factors are proper Docker configuration, secure secrets management, comprehensive health checks, and strategic regional deployment.