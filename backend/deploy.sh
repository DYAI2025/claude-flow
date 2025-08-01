#!/bin/bash

# Deployment script for ME_CORE_Backend_mar_spar to fly.io

set -e  # Exit on error

echo "🚀 Starting deployment for ME_CORE_Backend_mar_spar..."

# Check prerequisites
check_prerequisites() {
    echo "📋 Checking prerequisites..."
    
    if ! command -v fly &> /dev/null; then
        echo "❌ Fly CLI not found. Installing..."
        curl -L https://fly.io/install.sh | sh
        export PATH="$HOME/.fly/bin:$PATH"
    fi
    
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker not found. Please install Docker first."
        exit 1
    fi
    
    echo "✅ Prerequisites checked"
}

# Set up environment
setup_environment() {
    echo "🔧 Setting up environment..."
    
    if [ ! -f .env ]; then
        echo "📝 Creating .env from .env.example..."
        cp .env.example .env
        echo "⚠️  Please update .env with your actual values before deploying!"
        echo "Press Enter to continue after updating .env..."
        read
    fi
}

# Test locally
test_local() {
    echo "🧪 Testing local build..."
    
    # Build Docker image
    echo "🐳 Building Docker image..."
    docker build -t me-core-backend-test .
    
    # Test container
    echo "🏃 Running test container..."
    docker run -d --name test-backend -p 8000:8000 me-core-backend-test
    
    # Wait for startup
    echo "⏳ Waiting for container to start..."
    sleep 5
    
    # Test health endpoint
    echo "🏥 Testing health endpoint..."
    if curl -f http://localhost:8000/health; then
        echo "✅ Health check passed!"
    else
        echo "❌ Health check failed!"
        docker logs test-backend
        docker stop test-backend
        docker rm test-backend
        exit 1
    fi
    
    # Clean up
    docker stop test-backend
    docker rm test-backend
    echo "✅ Local tests passed!"
}

# Deploy to fly.io
deploy_to_fly() {
    echo "☁️  Deploying to fly.io..."
    
    # Check if app exists
    if ! fly status &> /dev/null; then
        echo "🆕 Creating new fly.io app..."
        fly launch --no-deploy
    fi
    
    # Set secrets
    echo "🔐 Setting production secrets..."
    echo "Enter your MongoDB URL (or press Enter to skip):"
    read -s MONGODB_URL
    if [ ! -z "$MONGODB_URL" ]; then
        fly secrets set MONGODB_URL="$MONGODB_URL"
    fi
    
    echo "Enter your SECRET_KEY (or press Enter to generate):"
    read -s SECRET_KEY
    if [ -z "$SECRET_KEY" ]; then
        SECRET_KEY=$(openssl rand -hex 32)
        echo "Generated SECRET_KEY"
    fi
    fly secrets set SECRET_KEY="$SECRET_KEY"
    
    # Deploy
    echo "🚀 Deploying application..."
    fly deploy
    
    # Check status
    echo "📊 Checking deployment status..."
    fly status
}

# Post-deployment verification
verify_deployment() {
    echo "🔍 Verifying deployment..."
    
    APP_URL=$(fly info -j | jq -r '.Hostname')
    
    echo "🏥 Testing production health endpoint..."
    if curl -f "https://${APP_URL}/health"; then
        echo "✅ Production health check passed!"
    else
        echo "⚠️  Health check failed. Checking logs..."
        fly logs
    fi
    
    echo "📝 Deployment summary:"
    echo "- App URL: https://${APP_URL}"
    echo "- Logs: fly logs"
    echo "- SSH: fly ssh console"
    echo "- Status: fly status"
    echo "- Scale: fly scale show"
}

# Main deployment flow
main() {
    echo "🎯 ME_CORE_Backend_mar_spar Deployment Script"
    echo "============================================"
    
    check_prerequisites
    setup_environment
    
    echo "Choose deployment option:"
    echo "1) Test locally only"
    echo "2) Deploy to production"
    echo "3) Full deployment (test + deploy)"
    read -p "Enter option (1-3): " option
    
    case $option in
        1)
            test_local
            ;;
        2)
            deploy_to_fly
            verify_deployment
            ;;
        3)
            test_local
            deploy_to_fly
            verify_deployment
            ;;
        *)
            echo "Invalid option"
            exit 1
            ;;
    esac
    
    echo "✅ Deployment script completed!"
}

# Run main function
main