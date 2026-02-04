# Media Management Web Tool - Frontend Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the React frontend application alongside the Python backend.

---

## 1. Development Setup

### 1.1 Prerequisites

- Node.js 18+ and npm/yarn
- Git
- Code editor (VS Code recommended)

### 1.2 Local Development

```bash
# Clone repository
git clone <repository-url>
cd media-management-tool/frontend

# Install dependencies
npm install

# Create .env file
cp .env.example .env

# Start development server
npm run dev
```

### 1.3 Environment Variables

```env
# .env
VITE_API_URL=http://localhost:8000/api
VITE_APP_NAME=Media Management
VITE_APP_VERSION=1.0.0
VITE_LOG_LEVEL=debug
```

### 1.4 Development Server

- Frontend: http://localhost:5173 (Vite default)
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## 2. Production Build

### 2.1 Build Process

```bash
# Install dependencies
npm install

# Build for production
npm run build

# Output directory: dist/
```

### 2.2 Build Optimization

```bash
# Analyze bundle size
npm run build -- --analyze

# Preview production build locally
npm run preview
```

### 2.3 Build Configuration

**vite.config.ts:**
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
    sourcemap: false,
    minify: 'terser',
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'query-vendor': ['@tanstack/react-query'],
          'ui-vendor': ['@radix-ui/react-dialog', '@radix-ui/react-dropdown-menu'],
        },
      },
    },
  },
})
```

---

## 3. Docker Deployment

### 3.1 Dockerfile

```dockerfile
# Build stage
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build application
RUN npm run build

# Production stage
FROM node:18-alpine

WORKDIR /app

# Install serve to run the app
RUN npm install -g serve

# Copy built application from builder
COPY --from=builder /app/dist ./dist

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost:3000/ || exit 1

# Start application
CMD ["serve", "-s", "dist", "-l", "3000"]
```

### 3.2 Docker Compose Integration

**docker-compose.yml (updated):**
```yaml
version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: media-management-frontend
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://app:8000/api
    depends_on:
      - app
    networks:
      - media-network
    restart: unless-stopped

  app:
    build:
      context: .
      dockerfile: docker/Dockerfile
    container_name: media-management-app
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./data/media.db
      - OMDB_API_KEY=${OMDB_API_KEY}
      - TVDB_API_KEY=${TVDB_API_KEY}
      - TVDB_PIN=${TVDB_PIN}
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
      - REDIS_URL=redis://redis:6379/2
      - MEDIA_WATCH_PATHS=["/media/movies", "/media/tv_shows"]
      - LOG_LEVEL=INFO
    volumes:
      - ./data:/app/data
      - /media/movies:/media/movies
      - /media/tv_shows:/media/tv_shows
    depends_on:
      - redis
    networks:
      - media-network
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: media-management-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    networks:
      - media-network
    restart: unless-stopped

  celery-worker:
    build:
      context: .
      dockerfile: docker/Dockerfile
    container_name: media-management-celery
    command: celery -A app.tasks.celery_app worker --loglevel=info
    environment:
      - DATABASE_URL=sqlite:///./data/media.db
      - OMDB_API_KEY=${OMDB_API_KEY}
      - TVDB_API_KEY=${TVDB_API_KEY}
      - TVDB_PIN=${TVDB_PIN}
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
      - REDIS_URL=redis://redis:6379/2
      - MEDIA_WATCH_PATHS=["/media/movies", "/media/tv_shows"]
      - LOG_LEVEL=INFO
    volumes:
      - ./data:/app/data
      - /media/movies:/media/movies
      - /media/tv_shows:/media/tv_shows
    depends_on:
      - redis
      - app
    networks:
      - media-network
    restart: unless-stopped

volumes:
  redis-data:

networks:
  media-network:
    driver: bridge
```

### 3.3 Build and Run

```bash
# Build all services
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f frontend

# Stop services
docker-compose down
```

---

## 4. Nginx Configuration

### 4.1 Reverse Proxy Setup

**nginx.conf:**
```nginx
upstream frontend {
    server frontend:3000;
}

upstream backend {
    server app:8000;
}

server {
    listen 80;
    server_name yourdomain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Gzip compression
    gzip on;
    gzip_types text/plain text/css text/javascript application/json application/javascript;
    gzip_min_length 1000;
    
    # Frontend routes
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # API routes
    location /api {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # API timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # API documentation
    location /docs {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 4.2 Docker Compose with Nginx

```yaml
nginx:
  image: nginx:alpine
  container_name: media-management-nginx
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./nginx.conf:/etc/nginx/nginx.conf:ro
    - ./ssl:/etc/letsencrypt:ro
  depends_on:
    - frontend
    - app
  networks:
    - media-network
  restart: unless-stopped
```

---

## 5. Production Deployment

### 5.1 Pre-Deployment Checklist

- [ ] Environment variables configured
- [ ] SSL certificates obtained
- [ ] Database backups configured
- [ ] Monitoring set up
- [ ] Logging configured
- [ ] Security headers configured
- [ ] CORS properly configured
- [ ] Rate limiting enabled

### 5.2 Deployment Steps

```bash
# 1. SSH into production server
ssh user@production-server

# 2. Clone repository
git clone <repository-url>
cd media-management-tool

# 3. Create .env file
nano .env
# Add production configuration

# 4. Build Docker images
docker-compose build

# 5. Start services
docker-compose up -d

# 6. Verify deployment
docker-compose ps
curl https://yourdomain.com/health
```

### 5.3 Environment Configuration

**Production .env:**
```env
# Backend
DATABASE_URL=sqlite:///./data/media.db
OMDB_API_KEY=<production-key>
TVDB_API_KEY=<production-key>
TVDB_PIN=<production-pin>
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
REDIS_URL=redis://redis:6379/2
MEDIA_WATCH_PATHS=["/media/movies", "/media/tv_shows"]
LOG_LEVEL=WARNING

# Frontend
VITE_API_URL=https://yourdomain.com/api
VITE_APP_NAME=Media Management
VITE_LOG_LEVEL=error
```

---

## 6. Kubernetes Deployment

### 6.1 Frontend Deployment

**frontend-deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: media-management-frontend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: media-management-frontend
  template:
    metadata:
      labels:
        app: media-management-frontend
    spec:
      containers:
      - name: frontend
        image: media-management-frontend:latest
        ports:
        - containerPort: 3000
        env:
        - name: VITE_API_URL
          value: "https://yourdomain.com/api"
        livenessProbe:
          httpGet:
            path: /
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /
            port: 3000
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "500m"
```

### 6.2 Frontend Service

**frontend-service.yaml:**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: media-management-frontend-service
spec:
  selector:
    app: media-management-frontend
  ports:
  - protocol: TCP
    port: 80
    targetPort: 3000
  type: ClusterIP
```

### 6.3 Ingress Configuration

**ingress.yaml:**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: media-management-ingress
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - yourdomain.com
    secretName: media-management-tls
  rules:
  - host: yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: media-management-frontend-service
            port:
              number: 80
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: media-management-backend-service
            port:
              number: 8000
```

### 6.4 Deploy to Kubernetes

```bash
# Create namespace
kubectl create namespace media-management

# Deploy frontend
kubectl apply -f frontend-deployment.yaml -n media-management
kubectl apply -f frontend-service.yaml -n media-management

# Deploy ingress
kubectl apply -f ingress.yaml -n media-management

# Verify deployment
kubectl get pods -n media-management
kubectl get svc -n media-management
kubectl get ingress -n media-management
```

---

## 7. Performance Optimization

### 7.1 Static Asset Caching

**nginx.conf (caching section):**
```nginx
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
    add_header ETag "";
}

location ~* index\.html$ {
    expires 1h;
    add_header Cache-Control "public, must-revalidate";
}
```

### 7.2 CDN Integration

```nginx
# Serve static assets from CDN
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
    rewrite ^/(.*)$ https://cdn.yourdomain.com/$1 permanent;
}
```

### 7.3 Compression

```nginx
gzip on;
gzip_vary on;
gzip_min_length 1000;
gzip_types text/plain text/css text/xml text/javascript 
           application/x-javascript application/xml+rss 
           application/javascript application/json;
```

---

## 8. Monitoring & Logging

### 8.1 Frontend Monitoring

```typescript
// src/utils/monitoring.ts
import * as Sentry from "@sentry/react";

Sentry.init({
  dsn: import.meta.env.VITE_SENTRY_DSN,
  environment: import.meta.env.MODE,
  tracesSampleRate: 1.0,
});
```

### 8.2 Error Tracking

```typescript
// Automatic error tracking
Sentry.captureException(error);

// Manual error tracking
Sentry.captureMessage("User action completed", "info");
```

### 8.3 Performance Monitoring

```typescript
// Web Vitals
import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals';

getCLS(console.log);
getFID(console.log);
getFCP(console.log);
getLCP(console.log);
getTTFB(console.log);
```

### 8.4 Container Logs

```bash
# View frontend logs
docker-compose logs -f frontend

# View logs from specific time
docker-compose logs --since 2024-01-01 frontend

# Export logs
docker-compose logs frontend > frontend.log
```

---

## 9. Troubleshooting

### 9.1 Common Issues

**Issue: Frontend can't connect to API**
```bash
# Check API URL in .env
cat .env | grep VITE_API_URL

# Test API connectivity
curl http://localhost:8000/health

# Check network connectivity
docker-compose exec frontend curl http://app:8000/health
```

**Issue: Build fails**
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Check Node version
node --version  # Should be 18+

# Check build output
npm run build -- --verbose
```

**Issue: Slow performance**
```bash
# Analyze bundle size
npm run build -- --analyze

# Check network tab in browser DevTools
# Look for large assets or slow API calls

# Check frontend container resources
docker stats media-management-frontend
```

**Issue: CORS errors**
```bash
# Check backend CORS configuration
# Verify VITE_API_URL matches backend domain

# Test CORS headers
curl -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS http://localhost:8000/api/movies -v
```

---

## 10. Security Hardening

### 10.1 Content Security Policy

```nginx
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self' https://yourdomain.com;" always;
```

### 10.2 Security Headers

```nginx
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "DENY" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;
```

### 10.3 HTTPS Configuration

```bash
# Generate SSL certificate with Let's Encrypt
certbot certonly --standalone -d yourdomain.com

# Auto-renewal
certbot renew --dry-run
```

---

## 11. Backup & Recovery

### 11.1 Frontend Backup

```bash
# Backup built application
tar -czf frontend-backup-$(date +%Y%m%d).tar.gz dist/

# Store backup
scp frontend-backup-*.tar.gz backup-server:/backups/
```

### 11.2 Restore from Backup

```bash
# Extract backup
tar -xzf frontend-backup-20240101.tar.gz

# Restart frontend
docker-compose restart frontend
```

---

## 12. Scaling Considerations

### 12.1 Horizontal Scaling

```yaml
# Multiple frontend replicas
frontend:
  deploy:
    replicas: 3
```

### 12.2 Load Balancing

```nginx
upstream frontend_cluster {
    server frontend1:3000;
    server frontend2:3000;
    server frontend3:3000;
}

location / {
    proxy_pass http://frontend_cluster;
}
```

---

## 13. Maintenance

### 13.1 Regular Tasks

- **Daily:** Check logs for errors, verify backups
- **Weekly:** Review performance metrics, update dependencies
- **Monthly:** Security audit, SSL certificate check
- **Quarterly:** Full system audit, capacity planning

### 13.2 Updates

```bash
# Update dependencies
npm update

# Update Docker images
docker-compose pull
docker-compose up -d

# Rebuild frontend
npm run build
docker-compose build frontend
docker-compose up -d frontend
```

---

## 14. Support & Documentation

- **Frontend Docs:** http://yourdomain.com/docs
- **API Docs:** http://yourdomain.com/api/docs
- **GitHub Issues:** Report bugs and feature requests
- **Email Support:** support@yourdomain.com

---

## Conclusion

This deployment guide provides comprehensive instructions for deploying the React frontend alongside the Python backend. Follow the appropriate section based on your deployment environment (Docker, Kubernetes, or traditional server).
