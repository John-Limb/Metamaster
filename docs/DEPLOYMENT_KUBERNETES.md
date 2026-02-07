# Kubernetes Deployment Guide

## Table of Contents
1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Kubernetes Manifests](#kubernetes-manifests)
4. [Helm Charts](#helm-charts)
5. [Service Configuration](#service-configuration)
6. [Ingress Setup](#ingress-setup)
7. [Persistent Volumes](#persistent-volumes)
8. [ConfigMaps and Secrets](#configmaps-and-secrets)
9. [Scaling and Auto-Scaling](#scaling-and-auto-scaling)
10. [Deployment and Management](#deployment-and-management)

## Overview

This guide covers deploying the Metamaster application to Kubernetes, including manifests, Helm charts, and production configurations.

### Kubernetes Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                  Ingress Controller                   │   │
│  │              (nginx-ingress / traefik)               │   │
│  └────────────────────────┬─────────────────────────────┘   │
│                           │                                   │
│  ┌────────────────────────▼─────────────────────────────┐   │
│  │                  Service (LoadBalancer)              │   │
│  └────────────────────────┬─────────────────────────────┘   │
│                           │                                   │
│  ┌────────────────────────▼─────────────────────────────┐   │
│  │              Deployment (API Pods)                   │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐           │   │
│  │  │ Pod 1    │  │ Pod 2    │  │ Pod N    │           │   │
│  │  │ (API)    │  │ (API)    │  │ (API)    │           │   │
│  │  └──────────┘  └──────────┘  └──────────┘           │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         StatefulSet (Database & Cache)               │   │
│  │  ┌──────────────┐  ┌──────────────┐                 │   │
│  │  │ PostgreSQL   │  │ Redis        │                 │   │
│  │  │ (Persistent) │  │ (Persistent) │                 │   │
│  │  └──────────────┘  └──────────────┘                 │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         Deployment (Celery Workers)                  │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐           │   │
│  │  │ Worker 1 │  │ Worker 2 │  │ Worker N │           │   │
│  │  └──────────┘  └──────────┘  └──────────┘           │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

### Kubernetes Cluster
- Kubernetes 1.20+
- kubectl 1.20+
- Helm 3.0+

### Cluster Setup

```bash
# Verify cluster access
kubectl cluster-info

# Check nodes
kubectl get nodes

# Check cluster version
kubectl version

# Create namespace
kubectl create namespace metamaster
kubectl config set-context --current --namespace=metamaster
```

## Kubernetes Manifests

### 1. Namespace

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: metamaster
  labels:
    name: metamaster
```

### 2. ConfigMap

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: metamaster-config
  namespace: metamaster
data:
  APP_ENV: "production"
  DEBUG: "false"
  LOG_LEVEL: "INFO"
  DATABASE_POOL_SIZE: "20"
  DATABASE_MAX_OVERFLOW: "40"
  REDIS_CACHE_DB: "1"
  CELERY_RESULT_BACKEND: "redis://redis:6379/1"
  PROMETHEUS_ENABLED: "true"
```

### 3. Secret

```yaml
# secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: metamaster-secrets
  namespace: metamaster
type: Opaque
stringData:
  DATABASE_URL: "postgresql://metamaster:password@postgres:5432/metamaster"
  REDIS_URL: "redis://:password@redis:6379/0"
  CELERY_BROKER_URL: "redis://:password@redis:6379/0"
  SECRET_KEY: "your-secret-key-here"
  OMDB_API_KEY: "your_omdb_key"
  TVDB_API_KEY: "your_tvdb_key"
  SENTRY_DSN: "https://your-sentry-dsn"
```

### 4. PostgreSQL StatefulSet

```yaml
# postgres-statefulset.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: metamaster
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:14-alpine
        ports:
        - containerPort: 5432
          name: postgres
        env:
        - name: POSTGRES_USER
          value: metamaster
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: metamaster-secrets
              key: DATABASE_URL
        - name: POSTGRES_DB
          value: metamaster
        - name: PGDATA
          value: /var/lib/postgresql/data/pgdata
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          exec:
            command:
            - /bin/sh
            - -c
            - pg_isready -U metamaster
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - /bin/sh
            - -c
            - pg_isready -U metamaster
          initialDelaySeconds: 5
          periodSeconds: 10
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 10Gi
```

### 5. Redis StatefulSet

```yaml
# redis-statefulset.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis
  namespace: metamaster
spec:
  serviceName: redis
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        command:
        - redis-server
        - "--appendonly"
        - "yes"
        - "--requirepass"
        - "$(REDIS_PASSWORD)"
        ports:
        - containerPort: 6379
          name: redis
        env:
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: metamaster-secrets
              key: REDIS_URL
        volumeMounts:
        - name: redis-storage
          mountPath: /data
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          exec:
            command:
            - redis-cli
            - ping
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - redis-cli
            - ping
          initialDelaySeconds: 5
          periodSeconds: 10
  volumeClaimTemplates:
  - metadata:
      name: redis-storage
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 5Gi
```

### 6. API Deployment

```yaml
# api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: metamaster-api
  namespace: metamaster
spec:
  replicas: 3
  selector:
    matchLabels:
      app: metamaster-api
  template:
    metadata:
      labels:
        app: metamaster-api
    spec:
      containers:
      - name: api
        image: myregistry.azurecr.io/metamaster:latest
        imagePullPolicy: Always
        ports:
        - containerPort: 8000
          name: http
        env:
        - name: APP_ENV
          valueFrom:
            configMapKeyRef:
              name: metamaster-config
              key: APP_ENV
        - name: DEBUG
          valueFrom:
            configMapKeyRef:
              name: metamaster-config
              key: DEBUG
        - name: LOG_LEVEL
          valueFrom:
            configMapKeyRef:
              name: metamaster-config
              key: LOG_LEVEL
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: metamaster-secrets
              key: DATABASE_URL
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: metamaster-secrets
              key: REDIS_URL
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: metamaster-secrets
              key: SECRET_KEY
        - name: OMDB_API_KEY
          valueFrom:
            secretKeyRef:
              name: metamaster-secrets
              key: OMDB_API_KEY
        - name: TVDB_API_KEY
          valueFrom:
            secretKeyRef:
              name: metamaster-secrets
              key: TVDB_API_KEY
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### 7. Celery Worker Deployment

```yaml
# celery-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: metamaster-celery
  namespace: metamaster
spec:
  replicas: 2
  selector:
    matchLabels:
      app: metamaster-celery
  template:
    metadata:
      labels:
        app: metamaster-celery
    spec:
      containers:
      - name: celery
        image: myregistry.azurecr.io/metamaster:latest
        imagePullPolicy: Always
        command: ["celery", "-A", "app.celery_app", "worker", "-l", "info", "--concurrency=4"]
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: metamaster-secrets
              key: DATABASE_URL
        - name: CELERY_BROKER_URL
          valueFrom:
            secretKeyRef:
              name: metamaster-secrets
              key: CELERY_BROKER_URL
        - name: CELERY_RESULT_BACKEND
          valueFrom:
            configMapKeyRef:
              name: metamaster-config
              key: CELERY_RESULT_BACKEND
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

### 8. Celery Beat Deployment

```yaml
# celery-beat-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: metamaster-celery-beat
  namespace: metamaster
spec:
  replicas: 1
  selector:
    matchLabels:
      app: metamaster-celery-beat
  template:
    metadata:
      labels:
        app: metamaster-celery-beat
    spec:
      containers:
      - name: celery-beat
        image: myregistry.azurecr.io/metamaster:latest
        imagePullPolicy: Always
        command: ["celery", "-A", "app.celery_app", "beat", "-l", "info", "--scheduler", "django_celery_beat.schedulers:DatabaseScheduler"]
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: metamaster-secrets
              key: DATABASE_URL
        - name: CELERY_BROKER_URL
          valueFrom:
            secretKeyRef:
              name: metamaster-secrets
              key: CELERY_BROKER_URL
        - name: CELERY_RESULT_BACKEND
          valueFrom:
            configMapKeyRef:
              name: metamaster-config
              key: CELERY_RESULT_BACKEND
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

## Helm Charts

### 1. Helm Chart Structure

```
helm/metamaster/
├── Chart.yaml
├── values.yaml
├── values-dev.yaml
├── values-staging.yaml
├── values-prod.yaml
├── templates/
│   ├── namespace.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── postgres-statefulset.yaml
│   ├── redis-statefulset.yaml
│   ├── api-deployment.yaml
│   ├── celery-deployment.yaml
│   ├── celery-beat-deployment.yaml
│   ├── api-service.yaml
│   ├── postgres-service.yaml
│   ├── redis-service.yaml
│   ├── ingress.yaml
│   └── hpa.yaml
```

### 2. Chart.yaml

```yaml
# helm/metamaster/Chart.yaml
apiVersion: v2
name: metamaster
description: A Helm chart for Metamaster application
type: application
version: 1.0.0
appVersion: "1.0.0"
keywords:
  - metamaster
  - fastapi
  - celery
maintainers:
  - name: Your Name
    email: your.email@example.com
```

### 3. values.yaml

```yaml
# helm/metamaster/values.yaml
replicaCount: 3

image:
  repository: myregistry.azurecr.io/metamaster
  tag: latest
  pullPolicy: Always

imagePullSecrets: []

nameOverride: ""
fullnameOverride: ""

serviceAccount:
  create: true
  name: ""

podAnnotations: {}

podSecurityContext:
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 1000

securityContext:
  allowPrivilegeEscalation: false
  capabilities:
    drop:
    - ALL
  readOnlyRootFilesystem: true

service:
  type: LoadBalancer
  port: 80
  targetPort: 8000

ingress:
  enabled: true
  className: "nginx"
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
  hosts:
    - host: metamaster.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: metamaster-tls
      hosts:
        - metamaster.example.com

resources:
  limits:
    cpu: 1000m
    memory: 1Gi
  requests:
    cpu: 250m
    memory: 512Mi

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 10
  targetCPUUtilizationPercentage: 80
  targetMemoryUtilizationPercentage: 80

nodeSelector: {}

tolerations: []

affinity: {}

# Database
postgres:
  enabled: true
  replicas: 1
  storage: 10Gi
  resources:
    limits:
      cpu: 1000m
      memory: 1Gi
    requests:
      cpu: 250m
      memory: 256Mi

# Redis
redis:
  enabled: true
  replicas: 1
  storage: 5Gi
  resources:
    limits:
      cpu: 500m
      memory: 512Mi
    requests:
      cpu: 100m
      memory: 128Mi

# Celery
celery:
  enabled: true
  replicas: 2
  concurrency: 4
  resources:
    limits:
      cpu: 1000m
      memory: 1Gi
    requests:
      cpu: 500m
      memory: 512Mi

# Celery Beat
celeryBeat:
  enabled: true
  replicas: 1
  resources:
    limits:
      cpu: 500m
      memory: 512Mi
    requests:
      cpu: 100m
      memory: 256Mi

# Configuration
config:
  APP_ENV: production
  DEBUG: "false"
  LOG_LEVEL: INFO
  DATABASE_POOL_SIZE: "20"
  DATABASE_MAX_OVERFLOW: "40"
  PROMETHEUS_ENABLED: "true"

# Secrets (use external secret management in production)
secrets:
  DATABASE_URL: ""
  REDIS_URL: ""
  SECRET_KEY: ""
  OMDB_API_KEY: ""
  TVDB_API_KEY: ""
  SENTRY_DSN: ""
```

### 4. Deploy with Helm

```bash
# Add Helm repository
helm repo add metamaster https://your-helm-repo.com
helm repo update

# Install release
helm install metamaster ./helm/metamaster \
  -f helm/values-prod.yaml \
  -n metamaster \
  --create-namespace

# Upgrade release
helm upgrade metamaster ./helm/metamaster \
  -f helm/values-prod.yaml \
  -n metamaster

# Rollback release
helm rollback metamaster 1 -n metamaster

# Uninstall release
helm uninstall metamaster -n metamaster

# View release history
helm history metamaster -n metamaster

# Get values
helm get values metamaster -n metamaster
```

## Service Configuration

### 1. Service Manifest

```yaml
# api-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: metamaster-api
  namespace: metamaster
  labels:
    app: metamaster-api
spec:
  type: LoadBalancer
  selector:
    app: metamaster-api
  ports:
  - name: http
    port: 80
    targetPort: 8000
    protocol: TCP
```

### 2. Service Discovery

```bash
# Get service
kubectl get svc -n metamaster

# Describe service
kubectl describe svc metamaster-api -n metamaster

# Port forward
kubectl port-forward svc/metamaster-api 8000:8000 -n metamaster

# Access service
curl http://localhost:8000/health
```

## Ingress Setup

### 1. Ingress Manifest

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: metamaster-ingress
  namespace: metamaster
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - metamaster.example.com
    secretName: metamaster-tls
  rules:
  - host: metamaster.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: metamaster-api
            port:
              number: 80
```

### 2. Install Ingress Controller

```bash
# Install nginx-ingress
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install nginx-ingress ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace

# Verify installation
kubectl get pods -n ingress-nginx
```

### 3. SSL/TLS with cert-manager

```bash
# Install cert-manager
helm repo add jetstack https://charts.jetstack.io
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --set installCRDs=true

# Create ClusterIssuer
kubectl apply -f - <<EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

## Persistent Volumes

### 1. PersistentVolumeClaim

```yaml
# pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
  namespace: metamaster
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: standard
  resources:
    requests:
      storage: 10Gi
```

### 2. Storage Classes

```yaml
# storage-class.yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
provisioner: kubernetes.io/aws-ebs
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
  encrypted: "true"
allowVolumeExpansion: true
```

### 3. Backup PersistentVolumes

```bash
# Backup PostgreSQL PVC
kubectl exec -it postgres-0 -n metamaster -- \
  pg_dump -U metamaster metamaster > backup.sql

# Restore PostgreSQL PVC
kubectl exec -it postgres-0 -n metamaster -- \
  psql -U metamaster metamaster < backup.sql
```

## ConfigMaps and Secrets

### 1. Create ConfigMap

```bash
# From literal
kubectl create configmap metamaster-config \
  --from-literal=APP_ENV=production \
  --from-literal=DEBUG=false \
  -n metamaster

# From file
kubectl create configmap metamaster-config \
  --from-file=config.yaml \
  -n metamaster

# View ConfigMap
kubectl get configmap -n metamaster
kubectl describe configmap metamaster-config -n metamaster
```

### 2. Create Secret

```bash
# From literal
kubectl create secret generic metamaster-secrets \
  --from-literal=DATABASE_URL=postgresql://... \
  --from-literal=SECRET_KEY=... \
  -n metamaster

# From file
kubectl create secret generic metamaster-secrets \
  --from-file=secrets.yaml \
  -n metamaster

# View Secret
kubectl get secret -n metamaster
kubectl describe secret metamaster-secrets -n metamaster
```

### 3. External Secrets Operator

```yaml
# external-secret.yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: aws-secrets
  namespace: metamaster
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-east-1
      auth:
        jwt:
          serviceAccountRef:
            name: external-secrets-sa
---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: metamaster-secrets
  namespace: metamaster
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets
    kind: SecretStore
  target:
    name: metamaster-secrets
    creationPolicy: Owner
  data:
  - secretKey: DATABASE_URL
    remoteRef:
      key: metamaster/database-url
  - secretKey: SECRET_KEY
    remoteRef:
      key: metamaster/secret-key
```

## Scaling and Auto-Scaling

### 1. Horizontal Pod Autoscaler

```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: metamaster-api-hpa
  namespace: metamaster
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: metamaster-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 80
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 30
      - type: Pods
        value: 2
        periodSeconds: 30
      selectPolicy: Max
```

### 2. Vertical Pod Autoscaler

```yaml
# vpa.yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: metamaster-api-vpa
  namespace: metamaster
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: metamaster-api
  updatePolicy:
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
    - containerName: api
      minAllowed:
        cpu: 100m
        memory: 128Mi
      maxAllowed:
        cpu: 2
        memory: 2Gi
```

### 3. Manual Scaling

```bash
# Scale deployment
kubectl scale deployment metamaster-api --replicas=5 -n metamaster

# View replicas
kubectl get deployment metamaster-api -n metamaster

# Watch scaling
kubectl rollout status deployment/metamaster-api -n metamaster
```

## Deployment and Management

### 1. Deploy All Manifests

```bash
# Apply all manifests
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f secret.yaml
kubectl apply -f postgres-statefulset.yaml
kubectl apply -f redis-statefulset.yaml
kubectl apply -f api-deployment.yaml
kubectl apply -f celery-deployment.yaml
kubectl apply -f celery-beat-deployment.yaml
kubectl apply -f api-service.yaml
kubectl apply -f ingress.yaml
kubectl apply -f hpa.yaml

# Or apply directory
kubectl apply -f k8s/ -n metamaster
```

### 2. Monitor Deployment

```bash
# Get pods
kubectl get pods -n metamaster

# Describe pod
kubectl describe pod metamaster-api-xxx -n metamaster

# View logs
kubectl logs -f deployment/metamaster-api -n metamaster

# View logs from specific container
kubectl logs -f pod/metamaster-api-xxx -c api -n metamaster

# Previous logs (if crashed)
kubectl logs pod/metamaster-api-xxx --previous -n metamaster
```

### 3. Troubleshooting

```bash
# Check events
kubectl get events -n metamaster

# Describe deployment
kubectl describe deployment metamaster-api -n metamaster

# Check resource usage
kubectl top pods -n metamaster
kubectl top nodes

# Debug pod
kubectl debug pod/metamaster-api-xxx -n metamaster -it

# Execute command in pod
kubectl exec -it pod/metamaster-api-xxx -n metamaster -- bash
```

### 4. Update Deployment

```bash
# Update image
kubectl set image deployment/metamaster-api \
  api=myregistry.azurecr.io/metamaster:v1.1.0 \
  -n metamaster

# Rollout status
kubectl rollout status deployment/metamaster-api -n metamaster

# Rollback
kubectl rollout undo deployment/metamaster-api -n metamaster

# Rollback to specific revision
kubectl rollout undo deployment/metamaster-api --to-revision=2 -n metamaster
```

## Next Steps

1. [Local Development](DEPLOYMENT_LOCAL.md)
2. [Docker Deployment](DEPLOYMENT_DOCKER.md)
3. [Cloud Deployment](DEPLOYMENT_CLOUD.md)
4. [Database Management](DEPLOYMENT_DATABASE.md)
5. [Security Configuration](DEPLOYMENT_SECURITY.md)
