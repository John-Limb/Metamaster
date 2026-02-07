# Cloud Deployment Guide (AWS/GCP/Azure)

## Table of Contents
1. [Overview](#overview)
2. [AWS Deployment](#aws-deployment)
3. [GCP Deployment](#gcp-deployment)
4. [Azure Deployment](#azure-deployment)
5. [Database Setup](#database-setup)
6. [Cache Setup](#cache-setup)
7. [Load Balancer Configuration](#load-balancer-configuration)
8. [Auto-Scaling Groups](#auto-scaling-groups)
9. [CDN Configuration](#cdn-configuration)
10. [Monitoring and Logging](#monitoring-and-logging)

## Overview

This guide covers deploying the Metamaster application to major cloud providers: AWS, GCP, and Azure.

### Cloud Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Cloud Provider                            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                  CDN / Edge                          │   │
│  │            (CloudFront / Cloud CDN / CDN)           │   │
│  └────────────────────────┬─────────────────────────────┘   │
│                           │                                   │
│  ┌────────────────────────▼─────────────────────────────┐   │
│  │              Load Balancer                           │   │
│  │         (ALB / Cloud LB / App Gateway)              │   │
│  └────────────────────────┬─────────────────────────────┘   │
│                           │                                   │
│  ┌────────────────────────▼─────────────────────────────┐   │
│  │         Auto-Scaling Group / Instance Group         │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐           │   │
│  │  │Instance 1│  │Instance 2│  │Instance N│           │   │
│  │  │(API)     │  │(API)     │  │(API)     │           │   │
│  │  └──────────┘  └──────────┘  └──────────┘           │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         Managed Services                             │   │
│  │  ┌──────────────┐  ┌──────────────┐                 │   │
│  │  │ RDS/Cloud SQL│  │ ElastiCache/ │                 │   │
│  │  │ (Database)   │  │ Memorystore  │                 │   │
│  │  │              │  │ (Cache)      │                 │   │
│  │  └──────────────┘  └──────────────┘                 │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## AWS Deployment

### 1. Prerequisites

```bash
# Install AWS CLI
brew install awscli  # macOS
# or
sudo apt-get install awscli  # Linux

# Configure AWS credentials
aws configure
# Enter: AWS Access Key ID, Secret Access Key, Region, Output format

# Verify configuration
aws sts get-caller-identity
```

### 2. Create VPC and Networking

```bash
# Create VPC
aws ec2 create-vpc --cidr-block 10.0.0.0/16

# Create subnets
aws ec2 create-subnet \
  --vpc-id vpc-xxxxx \
  --cidr-block 10.0.1.0/24 \
  --availability-zone us-east-1a

aws ec2 create-subnet \
  --vpc-id vpc-xxxxx \
  --cidr-block 10.0.2.0/24 \
  --availability-zone us-east-1b

# Create Internet Gateway
aws ec2 create-internet-gateway

# Attach to VPC
aws ec2 attach-internet-gateway \
  --internet-gateway-id igw-xxxxx \
  --vpc-id vpc-xxxxx

# Create Route Table
aws ec2 create-route-table --vpc-id vpc-xxxxx

# Add route
aws ec2 create-route \
  --route-table-id rtb-xxxxx \
  --destination-cidr-block 0.0.0.0/0 \
  --gateway-id igw-xxxxx
```

### 3. RDS Database Setup

```bash
# Create RDS instance
aws rds create-db-instance \
  --db-instance-identifier metamaster-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 14.7 \
  --master-username metamaster \
  --master-user-password 'YourSecurePassword123!' \
  --allocated-storage 100 \
  --storage-type gp3 \
  --vpc-security-group-ids sg-xxxxx \
  --db-subnet-group-name default \
  --backup-retention-period 30 \
  --multi-az \
  --enable-cloudwatch-logs-exports postgresql

# Wait for instance to be available
aws rds describe-db-instances \
  --db-instance-identifier metamaster-db \
  --query 'DBInstances[0].DBInstanceStatus'

# Get endpoint
aws rds describe-db-instances \
  --db-instance-identifier metamaster-db \
  --query 'DBInstances[0].Endpoint.Address'
```

### 4. ElastiCache Setup

```bash
# Create Redis cluster
aws elasticache create-cache-cluster \
  --cache-cluster-id metamaster-redis \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --engine-version 7.0 \
  --num-cache-nodes 1 \
  --security-group-ids sg-xxxxx \
  --cache-subnet-group-name default \
  --auto-failover-enabled

# Get endpoint
aws elasticache describe-cache-clusters \
  --cache-cluster-id metamaster-redis \
  --show-cache-node-info \
  --query 'CacheClusters[0].CacheNodes[0].Endpoint'
```

### 5. EC2 Auto-Scaling Group

```bash
# Create launch template
aws ec2 create-launch-template \
  --launch-template-name metamaster-template \
  --version-description "Metamaster API" \
  --launch-template-data '{
    "ImageId": "ami-0c55b159cbfafe1f0",
    "InstanceType": "t3.small",
    "KeyName": "your-key-pair",
    "SecurityGroupIds": ["sg-xxxxx"],
    "UserData": "IyEvYmluL2Jhc2gKY2QgL2FwcApkb2NrZXIgcHVsbCBteXJlZ2lzdHJ5LmF6dXJlY3IuaW8vbWV0YW1hc3RlcjpsYXRlc3QKZG9ja2VyIHJ1biAtZCAtcCAiODAwMDo4MDAwIiBteXJlZ2lzdHJ5LmF6dXJlY3IuaW8vbWV0YW1hc3RlcjpsYXRlc3Q="
  }'

# Create Auto-Scaling Group
aws autoscaling create-auto-scaling-group \
  --auto-scaling-group-name metamaster-asg \
  --launch-template LaunchTemplateName=metamaster-template,Version='$Latest' \
  --min-size 3 \
  --max-size 10 \
  --desired-capacity 3 \
  --vpc-zone-identifier "subnet-xxxxx,subnet-yyyyy" \
  --target-group-arns arn:aws:elasticloadbalancing:...

# Create scaling policy
aws autoscaling put-scaling-policy \
  --auto-scaling-group-name metamaster-asg \
  --policy-name scale-up \
  --policy-type TargetTrackingScaling \
  --target-tracking-configuration '{
    "TargetValue": 70.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ASGAverageCPUUtilization"
    }
  }'
```

### 6. Application Load Balancer

```bash
# Create ALB
aws elbv2 create-load-balancer \
  --name metamaster-alb \
  --subnets subnet-xxxxx subnet-yyyyy \
  --security-groups sg-xxxxx \
  --scheme internet-facing \
  --type application

# Create target group
aws elbv2 create-target-group \
  --name metamaster-targets \
  --protocol HTTP \
  --port 8000 \
  --vpc-id vpc-xxxxx \
  --health-check-path /health \
  --health-check-interval-seconds 30 \
  --health-check-timeout-seconds 5 \
  --healthy-threshold-count 2 \
  --unhealthy-threshold-count 3

# Create listener
aws elbv2 create-listener \
  --load-balancer-arn arn:aws:elasticloadbalancing:... \
  --protocol HTTP \
  --port 80 \
  --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:...
```

### 7. CloudFront CDN

```bash
# Create CloudFront distribution
aws cloudfront create-distribution \
  --distribution-config '{
    "CallerReference": "metamaster-'$(date +%s)'",
    "Comment": "Metamaster CDN",
    "DefaultRootObject": "index.html",
    "Origins": {
      "Quantity": 1,
      "Items": [{
        "Id": "myALB",
        "DomainName": "metamaster-alb-xxxxx.us-east-1.elb.amazonaws.com",
        "CustomOriginConfig": {
          "HTTPPort": 80,
          "OriginProtocolPolicy": "http-only"
        }
      }]
    },
    "DefaultCacheBehavior": {
      "TargetOriginId": "myALB",
      "ViewerProtocolPolicy": "redirect-to-https",
      "TrustedSigners": {
        "Enabled": false,
        "Quantity": 0
      },
      "ForwardedValues": {
        "QueryString": true,
        "Cookies": {"Forward": "all"}
      },
      "MinTTL": 0
    },
    "Enabled": true
  }'
```

## GCP Deployment

### 1. Prerequisites

```bash
# Install Google Cloud SDK
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Initialize
gcloud init

# Set project
gcloud config set project PROJECT_ID

# Verify
gcloud config list
```

### 2. Cloud SQL Setup

```bash
# Create Cloud SQL instance
gcloud sql instances create metamaster-db \
  --database-version=POSTGRES_14 \
  --tier=db-f1-micro \
  --region=us-central1 \
  --backup-start-time=03:00 \
  --enable-bin-log \
  --retained-backups-count=30

# Create database
gcloud sql databases create metamaster \
  --instance=metamaster-db

# Create user
gcloud sql users create metamaster \
  --instance=metamaster-db \
  --password=YourSecurePassword123!

# Get connection string
gcloud sql instances describe metamaster-db \
  --format='value(ipAddresses[0].ipAddress)'
```

### 3. Memorystore Setup

```bash
# Create Redis instance
gcloud redis instances create metamaster-redis \
  --size=1 \
  --region=us-central1 \
  --redis-version=7.0 \
  --tier=basic

# Get connection details
gcloud redis instances describe metamaster-redis \
  --region=us-central1 \
  --format='value(host,port)'
```

### 4. Compute Engine Instance Group

```bash
# Create instance template
gcloud compute instance-templates create metamaster-template \
  --machine-type=e2-medium \
  --image-family=debian-11 \
  --image-project=debian-cloud \
  --boot-disk-size=50GB \
  --metadata-from-file startup-script=startup.sh

# Create instance group
gcloud compute instance-groups managed create metamaster-ig \
  --base-instance-name=metamaster \
  --template=metamaster-template \
  --size=3 \
  --zone=us-central1-a

# Set autoscaling
gcloud compute instance-groups managed set-autoscaling metamaster-ig \
  --max-num-replicas=10 \
  --min-num-replicas=3 \
  --target-cpu-utilization=0.7 \
  --zone=us-central1-a
```

### 5. Cloud Load Balancing

```bash
# Create health check
gcloud compute health-checks create http metamaster-health-check \
  --request-path=/health \
  --port=8000

# Create backend service
gcloud compute backend-services create metamaster-backend \
  --protocol=HTTP \
  --health-checks=metamaster-health-check \
  --global

# Add backend
gcloud compute backend-services add-backend metamaster-backend \
  --instance-group=metamaster-ig \
  --instance-group-zone=us-central1-a \
  --global

# Create URL map
gcloud compute url-maps create metamaster-lb \
  --default-service=metamaster-backend

# Create HTTP proxy
gcloud compute target-http-proxies create metamaster-proxy \
  --url-map=metamaster-lb

# Create forwarding rule
gcloud compute forwarding-rules create metamaster-forwarding-rule \
  --global \
  --target-http-proxy=metamaster-proxy \
  --address-region=us-central1 \
  --ports=80
```

### 6. Cloud CDN

```bash
# Enable Cloud CDN on backend service
gcloud compute backend-services update metamaster-backend \
  --enable-cdn \
  --cache-mode=CACHE_ALL_STATIC \
  --default-ttl=3600 \
  --max-ttl=86400 \
  --global
```

## Azure Deployment

### 1. Prerequisites

```bash
# Install Azure CLI
brew install azure-cli  # macOS
# or
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash  # Linux

# Login
az login

# Set subscription
az account set --subscription "SUBSCRIPTION_ID"

# Verify
az account show
```

### 2. Resource Group

```bash
# Create resource group
az group create \
  --name metamaster-rg \
  --location eastus

# List resource groups
az group list --output table
```

### 3. Azure Database for PostgreSQL

```bash
# Create PostgreSQL server
az postgres server create \
  --resource-group metamaster-rg \
  --name metamaster-db \
  --location eastus \
  --admin-user metamaster \
  --admin-password 'YourSecurePassword123!' \
  --sku-name B_Gen5_1 \
  --storage-size 51200 \
  --backup-retention 30 \
  --geo-redundant-backup Enabled

# Create database
az postgres db create \
  --resource-group metamaster-rg \
  --server-name metamaster-db \
  --name metamaster

# Get connection string
az postgres server show \
  --resource-group metamaster-rg \
  --name metamaster-db \
  --query fullyQualifiedDomainName
```

### 4. Azure Cache for Redis

```bash
# Create Redis cache
az redis create \
  --resource-group metamaster-rg \
  --name metamaster-redis \
  --location eastus \
  --sku Basic \
  --vm-size c0

# Get connection string
az redis show-connection-string \
  --resource-group metamaster-rg \
  --name metamaster-redis
```

### 5. Virtual Machine Scale Set

```bash
# Create scale set
az vmss create \
  --resource-group metamaster-rg \
  --name metamaster-vmss \
  --image UbuntuLTS \
  --vm-sku Standard_B2s \
  --instance-count 3 \
  --admin-username azureuser \
  --generate-ssh-keys \
  --custom-data startup.sh

# Create autoscale settings
az monitor autoscale create \
  --resource-group metamaster-rg \
  --resource metamaster-vmss \
  --resource-type "Microsoft.Compute/virtualMachineScaleSets" \
  --name metamaster-autoscale \
  --min-count 3 \
  --max-count 10 \
  --count 3
```

### 6. Application Gateway

```bash
# Create public IP
az network public-ip create \
  --resource-group metamaster-rg \
  --name metamaster-pip

# Create Application Gateway
az network application-gateway create \
  --resource-group metamaster-rg \
  --name metamaster-appgw \
  --location eastus \
  --public-ip-address metamaster-pip \
  --http-settings-cookie-based-affinity Disabled \
  --frontend-port 80 \
  --http-settings-port 8000 \
  --http-settings-protocol Http \
  --sku Standard_Small \
  --capacity 2
```

### 7. Azure CDN

```bash
# Create CDN profile
az cdn profile create \
  --resource-group metamaster-rg \
  --name metamaster-cdn \
  --sku Standard_Microsoft

# Create CDN endpoint
az cdn endpoint create \
  --resource-group metamaster-rg \
  --profile-name metamaster-cdn \
  --name metamaster \
  --origin metamaster-appgw.eastus.cloudapp.azure.com \
  --origin-host-header metamaster-appgw.eastus.cloudapp.azure.com
```

## Database Setup

### 1. Database Initialization

```bash
# Connect to database
psql -h <db-host> -U metamaster -d metamaster

# Run migrations
alembic upgrade head

# Seed data
python -m app.init_db
```

### 2. Backup Strategy

```bash
# AWS RDS Backup
aws rds create-db-snapshot \
  --db-instance-identifier metamaster-db \
  --db-snapshot-identifier metamaster-backup-$(date +%Y%m%d)

# GCP Cloud SQL Backup
gcloud sql backups create \
  --instance=metamaster-db

# Azure Database Backup
az postgres server backup create \
  --resource-group metamaster-rg \
  --server-name metamaster-db \
  --backup-name metamaster-backup-$(date +%Y%m%d)
```

## Cache Setup

### 1. Redis Configuration

```bash
# AWS ElastiCache
aws elasticache modify-cache-cluster \
  --cache-cluster-id metamaster-redis \
  --parameter-group-name custom-redis-params

# GCP Memorystore
gcloud redis instances update metamaster-redis \
  --region=us-central1 \
  --update-redis-config maxmemory-policy=allkeys-lru

# Azure Cache for Redis
az redis update \
  --resource-group metamaster-rg \
  --name metamaster-redis \
  --set minimumTlsVersion=1.2
```

## Load Balancer Configuration

### 1. Health Checks

```bash
# AWS ALB Health Check
aws elbv2 modify-target-group \
  --target-group-arn arn:aws:elasticloadbalancing:... \
  --health-check-path /health \
  --health-check-interval-seconds 30 \
  --health-check-timeout-seconds 5 \
  --healthy-threshold-count 2 \
  --unhealthy-threshold-count 3

# GCP Health Check
gcloud compute health-checks update http metamaster-health-check \
  --request-path=/health \
  --port=8000 \
  --check-interval=30s \
  --timeout=5s

# Azure Application Gateway Health Probe
az network application-gateway probe create \
  --resource-group metamaster-rg \
  --gateway-name metamaster-appgw \
  --name metamaster-probe \
  --protocol http \
  --path /health \
  --host-name-from-http-settings true
```

## Auto-Scaling Groups

### 1. Scaling Policies

```bash
# AWS Target Tracking Scaling
aws autoscaling put-scaling-policy \
  --auto-scaling-group-name metamaster-asg \
  --policy-name cpu-scaling \
  --policy-type TargetTrackingScaling \
  --target-tracking-configuration '{
    "TargetValue": 70.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ASGAverageCPUUtilization"
    },
    "ScaleOutCooldown": 60,
    "ScaleInCooldown": 300
  }'

# GCP Autoscaling
gcloud compute instance-groups managed set-autoscaling metamaster-ig \
  --max-num-replicas=10 \
  --min-num-replicas=3 \
  --target-cpu-utilization=0.7 \
  --zone=us-central1-a

# Azure VMSS Autoscale
az monitor autoscale rule create \
  --resource-group metamaster-rg \
  --autoscale-name metamaster-autoscale \
  --condition "Percentage CPU > 70 avg 5m" \
  --scale out 1
```

## CDN Configuration

### 1. Cache Rules

```bash
# AWS CloudFront Cache Behavior
aws cloudfront create-distribution \
  --distribution-config '{
    "CacheBehaviors": [{
      "PathPattern": "/api/*",
      "ViewerProtocolPolicy": "https-only",
      "CachePolicyId": "658327ea-f89d-4fab-a63d-7e88639e58f6",
      "OriginRequestPolicyId": "216adef5-5c7f-47e4-b989-5492eafa07d3"
    }]
  }'

# GCP Cloud CDN Cache Policy
gcloud compute backend-services update metamaster-backend \
  --cache-mode=CACHE_ALL_STATIC \
  --default-ttl=3600 \
  --max-ttl=86400 \
  --global

# Azure CDN Caching Rules
az cdn endpoint rule create \
  --resource-group metamaster-rg \
  --profile-name metamaster-cdn \
  --endpoint-name metamaster \
  --name cache-api \
  --order 1 \
  --action-name CacheExpiration \
  --action-parameters cache-behavior=Override cache-duration=1:0:0
```

## Monitoring and Logging

### 1. CloudWatch (AWS)

```bash
# Create log group
aws logs create-log-group --log-group-name /metamaster/api

# Create metric alarm
aws cloudwatch put-metric-alarm \
  --alarm-name metamaster-high-cpu \
  --alarm-description "Alert when CPU exceeds 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/EC2 \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2
```

### 2. Cloud Logging (GCP)

```bash
# View logs
gcloud logging read "resource.type=gce_instance" --limit 50

# Create log sink
gcloud logging sinks create metamaster-sink \
  logging.googleapis.com/projects/PROJECT_ID/logs/metamaster
```

### 3. Azure Monitor

```bash
# Create action group
az monitor action-group create \
  --resource-group metamaster-rg \
  --name metamaster-action-group

# Create metric alert
az monitor metrics alert create \
  --resource-group metamaster-rg \
  --name metamaster-cpu-alert \
  --scopes /subscriptions/SUBSCRIPTION_ID/resourceGroups/metamaster-rg \
  --condition "avg Percentage CPU > 80" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --action metamaster-action-group
```

## Next Steps

1. [Local Development](DEPLOYMENT_LOCAL.md)
2. [Docker Deployment](DEPLOYMENT_DOCKER.md)
3. [Kubernetes Deployment](DEPLOYMENT_KUBERNETES.md)
4. [Database Management](DEPLOYMENT_DATABASE.md)
5. [Security Configuration](DEPLOYMENT_SECURITY.md)
