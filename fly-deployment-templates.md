# Fly.io Deployment Templates for ME_CORE_Backend_mar_spar

## Template Files for Immediate Deployment

### 1. Dockerfile Template

**File: `Dockerfile`**
```dockerfile
# syntax = docker/dockerfile:1

# Build arguments
ARG NODE_VERSION=18.15.0

# Base stage
FROM node:${NODE_VERSION}-slim as base
LABEL fly_launch_runtime="NodeJS"

# Set working directory
WORKDIR /app

# Set production environment
ENV NODE_ENV=production

# Install system dependencies
RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Build stage
FROM base as build

# Install build dependencies
RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends \
    python-is-python3 \
    pkg-config \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy package files
COPY --link package*.json ./

# Install all dependencies (including dev)
RUN npm ci --production=false

# Copy application code
COPY --link . .

# Remove dev dependencies
RUN npm prune --production

# Production stage
FROM base

# Copy built application from build stage
COPY --from=build /app /app

# Create non-root user
RUN groupadd --system --gid 1001 nodejs
RUN useradd --system --uid 1001 --gid nodejs nodejs

# Change ownership to nodejs user
RUN chown -R nodejs:nodejs /app
USER nodejs

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Start the application
CMD ["npm", "run", "start"]
```

### 2. fly.toml Configuration Template

**File: `fly.toml`**
```toml
# Fly.io Configuration for ME_CORE_Backend_mar_spar
app = "me-core-backend-mar-spar"
primary_region = "sin"

# Kill signal and timeout
kill_signal = "SIGINT"
kill_timeout = "5s"

# Environment variables (non-sensitive)
[env]
  PORT = "8080"
  NODE_ENV = "production"

# Build configuration
[build]

# HTTP service configuration
[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 1

  # HTTP health checks
  [[http_service.checks]]
    grace_period = "10s"
    interval = "30s"
    method = "GET"
    timeout = "5s"
    path = "/health"
    headers = {}

  [[http_service.checks]]
    grace_period = "15s"
    interval = "60s"
    method = "GET"
    timeout = "10s"
    path = "/health/detailed"
    headers = {}

# Service configuration for TCP checks
[[services]]
  protocol = "tcp"
  internal_port = 8080

  # TCP health checks
  [[services.tcp_checks]]
    grace_period = "1s"
    interval = "15s"
    timeout = "2s"

  # Port configuration
  [[services.ports]]
    port = 80
    handlers = ["http"]
    force_https = true

  [[services.ports]]
    port = 443
    handlers = ["tls", "http"]

  # Concurrency settings
  [services.concurrency]
    type = "requests"
    hard_limit = 25
    soft_limit = 20

# Machine configuration
[[vm]]
  cpu_kind = "shared"
  cpus = 1
  memory_mb = 512
```

### 3. Package.json Modifications Template

**Add/Update in `package.json`:**
```json
{
  "engines": {
    "node": "18.x",
    "npm": ">=8.0.0"
  },
  "scripts": {
    "start": "node server.js",
    "dev": "nodemon server.js",
    "build": "echo 'No build step required'",
    "test": "jest",
    "lint": "eslint .",
    "health-check": "curl -f http://localhost:8080/health || exit 1"
  },
  "dependencies": {
    "express": "^4.18.2",
    "mongoose": "^7.0.0",
    "helmet": "^6.0.0",
    "cors": "^2.8.5",
    "express-rate-limit": "^6.7.0",
    "dotenv": "^16.0.3",
    "compression": "^1.7.4"
  },
  "devDependencies": {
    "nodemon": "^2.0.20",
    "jest": "^29.0.0",
    "eslint": "^8.0.0"
  }
}
```

### 4. Server.js Template with Fly.io Optimizations

**File: `server.js`**
```javascript
require('dotenv').config();
const express = require('express');
const mongoose = require('mongoose');
const helmet = require('helmet');
const cors = require('cors');
const rateLimit = require('express-rate-limit');
const compression = require('compression');

const app = express();

// Configuration
const PORT = process.env.PORT || 8080;
const HOST = '0.0.0.0'; // Critical for Fly.io
const MONGODB_URI = process.env.MONGODB_URI;

// Security middleware
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      scriptSrc: ["'self'"],
      imgSrc: ["'self'", "data:", "https:"],
      connectSrc: ["'self'"]
    }
  },
  crossOriginEmbedderPolicy: false
}));

// CORS configuration
app.use(cors({
  origin: process.env.ALLOWED_ORIGINS?.split(',') || [
    'http://localhost:3000',
    'https://your-frontend-domain.com'
  ],
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization']
}));

// Compression middleware
app.use(compression());

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per windowMs
  message: {
    error: 'Too many requests from this IP, please try again later.'
  },
  standardHeaders: true,
  legacyHeaders: false
});

app.use('/api/', limiter);

// Body parsing middleware
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// MongoDB connection with retry logic
const connectDB = async () => {
  try {
    const conn = await mongoose.connect(MONGODB_URI, {
      useNewUrlParser: true,
      useUnifiedTopology: true,
      maxPoolSize: 10,
      serverSelectionTimeoutMS: 5000,
      socketTimeoutMS: 45000,
      bufferCommands: false,
      bufferMaxEntries: 0
    });

    console.log(`MongoDB Connected: ${conn.connection.host}`);

    // Handle connection events
    mongoose.connection.on('error', (err) => {
      console.error('MongoDB connection error:', err);
    });

    mongoose.connection.on('disconnected', () => {
      console.warn('MongoDB disconnected');
    });

    // Graceful shutdown
    process.on('SIGINT', async () => {
      try {
        await mongoose.connection.close();
        console.log('MongoDB connection closed through app termination');
        process.exit(0);
      } catch (err) {
        console.error('Error during graceful shutdown:', err);
        process.exit(1);
      }
    });

  } catch (error) {
    console.error('Database connection failed:', error);
    process.exit(1);
  }
};

// Health check endpoints
app.get('/health', (req, res) => {
  res.status(200).json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    version: process.env.npm_package_version || '1.0.0',
    environment: process.env.NODE_ENV
  });
});

app.get('/health/detailed', async (req, res) => {
  try {
    // Test database connectivity
    await mongoose.connection.db.admin().ping();
    
    const dbState = mongoose.connection.readyState;
    const dbStateMap = {
      0: 'disconnected',
      1: 'connected',
      2: 'connecting',
      3: 'disconnecting'
    };

    res.status(200).json({
      status: 'healthy',
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
      memory: process.memoryUsage(),
      database: {
        status: dbStateMap[dbState],
        host: mongoose.connection.host,
        name: mongoose.connection.name
      },
      environment: process.env.NODE_ENV,
      version: process.env.npm_package_version || '1.0.0'
    });
  } catch (error) {
    console.error('Health check failed:', error);
    res.status(503).json({
      status: 'unhealthy',
      timestamp: new Date().toISOString(),
      database: {
        status: 'error',
        error: error.message
      },
      environment: process.env.NODE_ENV
    });
  }
});

// Ready check for Kubernetes/orchestration
app.get('/ready', async (req, res) => {
  try {
    if (mongoose.connection.readyState === 1) {
      res.status(200).json({ status: 'ready' });
    } else {
      res.status(503).json({ status: 'not ready' });
    }
  } catch (error) {
    res.status(503).json({ status: 'not ready', error: error.message });
  }
});

// API routes placeholder
app.get('/api/status', (req, res) => {
  res.json({
    message: 'ME_CORE Backend API is running',
    timestamp: new Date().toISOString(),
    version: '1.0.0'
  });
});

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({
    error: 'Route not found',
    path: req.originalUrl,
    method: req.method
  });
});

// Global error handler
app.use((err, req, res, next) => {
  console.error('Global error handler:', err);
  
  res.status(err.status || 500).json({
    error: process.env.NODE_ENV === 'production' 
      ? 'Internal server error' 
      : err.message,
    timestamp: new Date().toISOString()
  });
});

// Initialize database and start server
const startServer = async () => {
  try {
    await connectDB();
    
    const server = app.listen(PORT, HOST, () => {
      console.log(`🚀 Server running on http://${HOST}:${PORT}`);
      console.log(`📊 Environment: ${process.env.NODE_ENV}`);
      console.log(`🔍 Health check: http://${HOST}:${PORT}/health`);
    });

    // Graceful shutdown
    const gracefulShutdown = (signal) => {
      console.log(`\n${signal} received. Shutting down gracefully...`);
      server.close(async (err) => {
        if (err) {
          console.error('Error during server shutdown:', err);
          process.exit(1);
        }
        
        try {
          await mongoose.connection.close();
          console.log('MongoDB connection closed.');
          console.log('Server shut down successfully.');
          process.exit(0);
        } catch (error) {
          console.error('Error closing MongoDB connection:', error);
          process.exit(1);
        }
      });
    };

    process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
    process.on('SIGINT', () => gracefulShutdown('SIGINT'));

  } catch (error) {
    console.error('Failed to start server:', error);
    process.exit(1);
  }
};

// Start the server
startServer();

module.exports = app;
```

### 5. Environment Variables Template

**File: `.env.example`**
```env
# Server Configuration
NODE_ENV=production
PORT=8080

# Database Configuration (set via Fly.io secrets)
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/database?retryWrites=true&w=majority

# Security Configuration (set via Fly.io secrets)
JWT_SECRET=your-super-secret-jwt-key-here
API_KEY=your-api-key-here

# CORS Configuration
ALLOWED_ORIGINS=https://your-frontend-domain.com,https://another-domain.com

# Application Configuration
APP_NAME=ME_CORE_Backend_mar_spar
APP_VERSION=1.0.0

# Logging
LOG_LEVEL=info
```

### 6. Deployment Scripts Template

**File: `deploy.sh`**
```bash
#!/bin/bash

# Fly.io Deployment Script for ME_CORE_Backend_mar_spar
set -e

echo "🚀 Starting deployment to Fly.io..."

# Check if flyctl is installed
if ! command -v flyctl &> /dev/null; then
    echo "❌ flyctl is not installed. Please install it first."
    exit 1
fi

# Check if logged in to Fly.io
if ! flyctl auth whoami &> /dev/null; then
    echo "❌ Not logged in to Fly.io. Please run 'flyctl auth login' first."
    exit 1
fi

# Set secrets if they don't exist
echo "🔐 Setting up secrets..."
flyctl secrets set MONGODB_URI="${MONGODB_URI}" --stage
flyctl secrets set JWT_SECRET="${JWT_SECRET}" --stage
flyctl secrets set API_KEY="${API_KEY}" --stage

# Deploy the application
echo "📦 Deploying application..."
flyctl deploy --build-only --push

echo "🏥 Checking health after deployment..."
sleep 30  # Wait for deployment to stabilize

# Verify deployment
if flyctl status | grep -q "running"; then
    echo "✅ Deployment successful!"
    echo "🌐 Application URL: https://$(flyctl info | grep Hostname | awk '{print $2}')"
    echo "🏥 Health check: https://$(flyctl info | grep Hostname | awk '{print $2}')/health"
else
    echo "❌ Deployment failed. Check logs with 'flyctl logs'"
    exit 1
fi
```

**File: `setup.sh`**
```bash
#!/bin/bash

# Initial setup script for Fly.io deployment
set -e

echo "🔧 Setting up ME_CORE_Backend_mar_spar for Fly.io deployment..."

# Create Fly.io app
echo "📱 Creating Fly.io app..."
flyctl apps create me-core-backend-mar-spar --region sin

# Set up secrets
echo "🔐 Please provide the following secrets:"

read -s -p "MongoDB URI: " MONGODB_URI
echo
read -s -p "JWT Secret: " JWT_SECRET
echo
read -s -p "API Key: " API_KEY
echo

flyctl secrets set MONGODB_URI="${MONGODB_URI}"
flyctl secrets set JWT_SECRET="${JWT_SECRET}"
flyctl secrets set API_KEY="${API_KEY}"

echo "✅ Setup complete! You can now deploy with 'flyctl deploy'"
```

### 7. Docker Ignore Template

**File: `.dockerignore`**
```
# Dependencies
node_modules
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Runtime data
pids
*.pid
*.seed
*.pid.lock

# Coverage directory used by tools like istanbul
coverage
*.lcov

# nyc test coverage
.nyc_output

# Grunt intermediate storage
.grunt

# Bower dependency directory
bower_components

# node-waf configuration
.lock-wscript

# Compiled binary addons
build/Release

# Dependency directories
jspm_packages/

# TypeScript cache
*.tsbuildinfo

# Optional npm cache directory
.npm

# Optional eslint cache
.eslintcache

# Microbundle cache
.rpt2_cache/
.rts2_cache_cjs/
.rts2_cache_es/
.rts2_cache_umd/

# Optional REPL history
.node_repl_history

# Output of 'npm pack'
*.tgz

# Yarn Integrity file
.yarn-integrity

# dotenv environment variables file
.env
.env.test
.env.local
.env.production

# parcel-bundler cache
.cache
.parcel-cache

# Next.js build output
.next

# Nuxt.js build / generate output
.nuxt
dist

# Gatsby files
.cache/
public

# Vuepress build output
.vuepress/dist

# Serverless directories
.serverless/

# FuseBox cache
.fusebox/

# DynamoDB Local files
.dynamodb/

# TernJS port file
.tern-port

# Stores VSCode versions used for testing VSCode extensions
.vscode-test

# Fly.io
fly.toml.bak
.fly/

# Logs
logs
*.log

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# IDE files
.vscode/
.idea/
*.swp
*.swo

# Build artifacts
build/
dist/

# Test files
test/
tests/
__tests__/
spec/
*.test.js
*.spec.js

# Documentation
docs/
README.md
CHANGELOG.md

# Git
.git/
.gitignore

# CI/CD
.github/
.gitlab-ci.yml
.travis.yml
```

## Quick Deployment Checklist

### Before Deployment:
- [ ] Copy Dockerfile to project root
- [ ] Copy fly.toml to project root  
- [ ] Update package.json with required scripts and engines
- [ ] Copy server.js template or modify existing server
- [ ] Create .dockerignore file
- [ ] Set up MongoDB Atlas with proper network access
- [ ] Install flyctl CLI tool
- [ ] Login to Fly.io account

### Deployment Commands:
```bash
# 1. Initialize app (if not already done)
flyctl apps create me-core-backend-mar-spar --region sin

# 2. Set secrets
flyctl secrets set MONGODB_URI="your-mongodb-connection-string"
flyctl secrets set JWT_SECRET="your-jwt-secret"
flyctl secrets set API_KEY="your-api-key"

# 3. Deploy
flyctl deploy

# 4. Check status
flyctl status
flyctl logs
```

### Post-Deployment Verification:
- [ ] Check application status: `flyctl status`
- [ ] Test health endpoint: `curl https://your-app.fly.dev/health`
- [ ] Verify database connection: `curl https://your-app.fly.dev/health/detailed`
- [ ] Check logs for any errors: `flyctl logs`
- [ ] Test API endpoints functionality
- [ ] Monitor resource usage and scaling

This template provides a complete, production-ready configuration for deploying ME_CORE_Backend_mar_spar to Fly.io with all necessary optimizations and best practices.