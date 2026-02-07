# Infrastructure as Code Documentation

## Table of Contents
1. [Overview](#overview)
2. [Terraform Templates](#terraform-templates)
3. [CloudFormation Templates](#cloudformation-templates)
4. [Docker Compose Files](#docker-compose-files)
5. [Kubernetes Manifests](#kubernetes-manifests)
6. [Configuration Management](#configuration-management)
7. [Best Practices](#best-practices)
8. [Deployment Automation](#deployment-automation)
9. [Version Control](#version-control)
10. [Maintenance](#maintenance)

## Overview

This guide covers Infrastructure as Code (IaC) templates and configurations for deploying the Metamaster application across different environments.

### IaC Benefits

- **Reproducibility**: Consistent infrastructure across environments
- **Version Control**: Track infrastructure changes
- **Automation**: Reduce manual configuration
- **Documentation**: Infrastructure defined in code
- **Scalability**: Easy to scale resources
- **Disaster Recovery**: Quick infrastructure recreation

### IaC Tools

| Tool | Use Case | Cloud |
|------|----------|-------|
| Terraform | Multi-cloud IaC | AWS, GCP, Azure |
| CloudFormation | AWS-native IaC | AWS |
| Helm | Kubernetes package manager | Kubernetes |
| Docker Compose | Local/single-host | Docker |
| Ansible | Configuration management | Multi-cloud |

## Terraform Templates

### 1. Terraform Project Structure

```
terraform/
├── main.tf                 # Main configuration
├── variables.tf            # Variable definitions
├── outputs.tf              # Output definitions
├── terraform.tfvars        # Variable values
├── terraform.tfvars.example # Example values
├── modules/
│   ├── vpc/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── rds/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── elasticache/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── ecs/
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
├── environments/
│   ├── dev/
│   │   ├── terraform.tfvars
│   │   └── backend.tf
│   ├── staging/
│   │   ├── terraform.tfvars
│   │   └── backend.tf
│   └── prod/
│       ├── terraform.tfvars
│       └── backend.tf
└── .gitignore
```

### 2. Main Terraform Configuration

```hcl
# terraform/main.tf
terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  backend "s3" {
    bucket         = "metamaster-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Environment = var.environment
      Project     = "metamaster"
      ManagedBy   = "terraform"
    }
  }
}

# VPC Module
module "vpc" {
  source = "./modules/vpc"
  
  vpc_cidr            = var.vpc_cidr
  availability_zones  = var.availability_zones
  private_subnets    = var.private_subnets
  public_subnets     = var.public_subnets
  environment         = var.environment
}

# RDS Module
module "rds" {
  source = "./modules/rds"
  
  db_name             = var.db_name
  db_username         = var.db_username
  db_password         = var.db_password
  db_instance_class   = var.db_instance_class
  allocated_storage   = var.allocated_storage
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name = aws_db_subnet_group.default.name
  environment         = var.environment
}

# ElastiCache Module
module "elasticache" {
  source = "./modules/elasticache"
  
  cluster_id          = "metamaster-redis"
  engine              = "redis"
  engine_version      = "7.0"
  node_type           = var.redis_node_type
  num_cache_nodes     = var.redis_num_nodes
  parameter_group_name = "default.redis7"
  security_group_ids  = [aws_security_group.redis.id]
  subnet_group_name   = aws_elasticache_subnet_group.default.name
  environment         = var.environment
}

# ECS Cluster
module "ecs" {
  source = "./modules/ecs"
  
  cluster_name        = "metamaster"
  task_family         = "metamaster-api"
  container_image     = var.container_image
  container_port      = 8000
  desired_count       = var.desired_count
  cpu                 = var.task_cpu
  memory              = var.task_memory
  vpc_id              = module.vpc.vpc_id
  private_subnets    = module.vpc.private_subnets
  environment         = var.environment
}
```

### 3. Variables Configuration

```hcl
# terraform/variables.tf
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "Availability zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "metamaster"
}

variable "db_username" {
  description = "Database username"
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "redis_node_type" {
  description = "Redis node type"
  type        = string
  default     = "cache.t3.micro"
}

variable "container_image" {
  description = "Docker image URI"
  type        = string
}

variable "desired_count" {
  description = "Desired number of tasks"
  type        = number
  default     = 3
}

variable "task_cpu" {
  description = "Task CPU units"
  type        = number
  default     = 256
}

variable "task_memory" {
  description = "Task memory in MB"
  type        = number
  default     = 512
}
```

### 4. Outputs Configuration

```hcl
# terraform/outputs.tf
output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "rds_endpoint" {
  description = "RDS endpoint"
  value       = module.rds.endpoint
  sensitive   = true
}

output "redis_endpoint" {
  description = "Redis endpoint"
  value       = module.elasticache.endpoint
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = module.ecs.cluster_name
}

output "alb_dns_name" {
  description = "ALB DNS name"
  value       = module.ecs.alb_dns_name
}
```

### 5. Environment-Specific Configuration

```hcl
# terraform/environments/prod/terraform.tfvars
aws_region         = "us-east-1"
environment         = "prod"
vpc_cidr            = "10.0.0.0/16"
availability_zones  = ["us-east-1a", "us-east-1b", "us-east-1c"]

db_instance_class   = "db.t3.small"
allocated_storage   = 100
redis_node_type     = "cache.t3.small"
redis_num_nodes     = 3

container_image     = "myregistry.azurecr.io/metamaster:latest"
desired_count       = 5
task_cpu            = 512
task_memory         = 1024
```

### 6. Terraform Commands

```bash
# Initialize Terraform
terraform init

# Validate configuration
terraform validate

# Format code
terraform fmt -recursive

# Plan changes
terraform plan -out=tfplan

# Apply changes
terraform apply tfplan

# Destroy infrastructure
terraform destroy

# Show state
terraform show

# List resources
terraform state list

# Show specific resource
terraform state show aws_instance.example

# Refresh state
terraform refresh

# Taint resource (force recreation)
terraform taint aws_instance.example

# Untaint resource
terraform untaint aws_instance.example
```

## CloudFormation Templates

### 1. CloudFormation Template Structure

```yaml
# cloudformation/metamaster-stack.yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Metamaster Application CloudFormation Template'

Parameters:
  Environment:
    Type: String
    Default: prod
    AllowedValues:
      - dev
      - staging
      - prod
  
  DBUsername:
    Type: String
    NoEcho: true
  
  DBPassword:
    Type: String
    NoEcho: true

Mappings:
  EnvironmentConfig:
    dev:
      DBInstanceClass: db.t3.micro
      DesiredCount: 1
    staging:
      DBInstanceClass: db.t3.small
      DesiredCount: 2
    prod:
      DBInstanceClass: db.t3.medium
      DesiredCount: 3

Resources:
  # VPC
  MetamasterVPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: 10.0.0.0/16
      EnableDnsHostnames: true
      EnableDnsSupport: true
      Tags:
        - Key: Name
          Value: !Sub 'metamaster-vpc-${Environment}'

  # RDS Database
  MetamasterDB:
    Type: AWS::RDS::DBInstance
    Properties:
      DBInstanceIdentifier: !Sub 'metamaster-db-${Environment}'
      DBInstanceClass: !FindInMap [EnvironmentConfig, !Ref Environment, DBInstanceClass]
      Engine: postgres
      EngineVersion: '14.7'
      MasterUsername: !Ref DBUsername
      MasterUserPassword: !Ref DBPassword
      AllocatedStorage: 100
      StorageType: gp3
      VPCSecurityGroups:
        - !Ref DBSecurityGroup
      DBSubnetGroupName: !Ref DBSubnetGroup
      BackupRetentionPeriod: 30
      MultiAZ: true
      Tags:
        - Key: Name
          Value: !Sub 'metamaster-db-${Environment}'

  # ElastiCache Redis
  MetamasterRedis:
    Type: AWS::ElastiCache::CacheCluster
    Properties:
      CacheClusterId: !Sub 'metamaster-redis-${Environment}'
      CacheNodeType: cache.t3.micro
      Engine: redis
      EngineVersion: '7.0'
      NumCacheNodes: 1
      VpcSecurityGroupIds:
        - !Ref RedisSecurityGroup
      CacheSubnetGroupName: !Ref RedisSubnetGroup
      Tags:
        - Key: Name
          Value: !Sub 'metamaster-redis-${Environment}'

  # ECS Cluster
  MetamasterCluster:
    Type: AWS::ECS::Cluster
    Properties:
      ClusterName: !Sub 'metamaster-${Environment}'
      ClusterSettings:
        - Name: containerInsights
          Value: enabled

  # ECS Task Definition
  MetamasterTaskDefinition:
    Type: AWS::ECS::TaskDefinition
    Properties:
      Family: !Sub 'metamaster-${Environment}'
      NetworkMode: awsvpc
      RequiresCompatibilities:
        - FARGATE
      Cpu: '256'
      Memory: '512'
      ExecutionRoleArn: !GetAtt ECSTaskExecutionRole.Arn
      TaskRoleArn: !GetAtt ECSTaskRole.Arn
      ContainerDefinitions:
        - Name: metamaster-api
          Image: !Sub 'myregistry.azurecr.io/metamaster:latest'
          PortMappings:
            - ContainerPort: 8000
              Protocol: tcp
          Environment:
            - Name: APP_ENV
              Value: !Ref Environment
            - Name: DATABASE_URL
              Value: !Sub 'postgresql://${DBUsername}:${DBPassword}@${MetamasterDB.Endpoint.Address}:5432/metamaster'
          LogConfiguration:
            LogDriver: awslogs
            Options:
              awslogs-group: !Ref ECSLogGroup
              awslogs-region: !Ref AWS::Region
              awslogs-stream-prefix: ecs

  # ECS Service
  MetamasterService:
    Type: AWS::ECS::Service
    DependsOn: LoadBalancerListener
    Properties:
      ServiceName: !Sub 'metamaster-${Environment}'
      Cluster: !Ref MetamasterCluster
      TaskDefinition: !Ref MetamasterTaskDefinition
      DesiredCount: !FindInMap [EnvironmentConfig, !Ref Environment, DesiredCount]
      LaunchType: FARGATE
      NetworkConfiguration:
        AwsvpcConfiguration:
          AssignPublicIp: DISABLED
          Subnets:
            - !Ref PrivateSubnet1
            - !Ref PrivateSubnet2
          SecurityGroups:
            - !Ref ECSSecurityGroup
      LoadBalancers:
        - ContainerName: metamaster-api
          ContainerPort: 8000
          TargetGroupArn: !Ref TargetGroup

  # Application Load Balancer
  LoadBalancer:
    Type: AWS::ElasticLoadBalancingV2::LoadBalancer
    Properties:
      Name: !Sub 'metamaster-alb-${Environment}'
      Type: application
      Scheme: internet-facing
      Subnets:
        - !Ref PublicSubnet1
        - !Ref PublicSubnet2
      SecurityGroups:
        - !Ref ALBSecurityGroup

  # Target Group
  TargetGroup:
    Type: AWS::ElasticLoadBalancingV2::TargetGroup
    Properties:
      Name: !Sub 'metamaster-tg-${Environment}'
      Port: 8000
      Protocol: HTTP
      VpcId: !Ref MetamasterVPC
      TargetType: ip
      HealthCheckEnabled: true
      HealthCheckPath: /health
      HealthCheckProtocol: HTTP
      HealthCheckIntervalSeconds: 30
      HealthCheckTimeoutSeconds: 5
      HealthyThresholdCount: 2
      UnhealthyThresholdCount: 3

  # Load Balancer Listener
  LoadBalancerListener:
    Type: AWS::ElasticLoadBalancingV2::Listener
    Properties:
      LoadBalancerArn: !Ref LoadBalancer
      Port: 80
      Protocol: HTTP
      DefaultActions:
        - Type: forward
          TargetGroupArn: !Ref TargetGroup

Outputs:
  LoadBalancerDNS:
    Description: Load Balancer DNS Name
    Value: !GetAtt LoadBalancer.DNSName
  
  DatabaseEndpoint:
    Description: RDS Database Endpoint
    Value: !GetAtt MetamasterDB.Endpoint.Address
  
  RedisEndpoint:
    Description: Redis Endpoint
    Value: !GetAtt MetamasterRedis.RedisEndpoint.Address
```

### 2. CloudFormation Commands

```bash
# Create stack
aws cloudformation create-stack \
  --stack-name metamaster-prod \
  --template-body file://cloudformation/metamaster-stack.yaml \
  --parameters ParameterKey=Environment,ParameterValue=prod \
              ParameterKey=DBUsername,ParameterValue=metamaster \
              ParameterKey=DBPassword,ParameterValue=SecurePassword123!

# Update stack
aws cloudformation update-stack \
  --stack-name metamaster-prod \
  --template-body file://cloudformation/metamaster-stack.yaml

# Describe stack
aws cloudformation describe-stacks --stack-name metamaster-prod

# List stack resources
aws cloudformation list-stack-resources --stack-name metamaster-prod

# Delete stack
aws cloudformation delete-stack --stack-name metamaster-prod

# Wait for stack creation
aws cloudformation wait stack-create-complete --stack-name metamaster-prod
```

## Docker Compose Files

### 1. Production Docker Compose

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  postgres:
    image: postgres:14-alpine
    container_name: metamaster-postgres
    restart: always
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ${DB_NAME}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: metamaster-redis
    restart: always
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  api:
    build:
      context: .
      dockerfile: Dockerfile.prod
    container_name: metamaster-api
    restart: always
    environment:
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - APP_ENV=production
      - DEBUG=false
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  celery:
    build:
      context: .
      dockerfile: Dockerfile.prod
    container_name: metamaster-celery
    restart: always
    command: celery -A app.celery_app worker -l info
    environment:
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - APP_ENV=production
    depends_on:
      - postgres
      - redis

volumes:
  postgres_data:
  redis_data:
```

## Kubernetes Manifests

### 1. Kustomization Structure

```
k8s/
├── base/
│   ├── kustomization.yaml
│   ├── namespace.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   └── ingress.yaml
└── overlays/
    ├── dev/
    │   ├── kustomization.yaml
    │   └── patches/
    ├── staging/
    │   ├── kustomization.yaml
    │   └── patches/
    └── prod/
        ├── kustomization.yaml
        └── patches/
```

### 2. Kustomization Base

```yaml
# k8s/base/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: metamaster

resources:
  - namespace.yaml
  - configmap.yaml
  - secret.yaml
  - deployment.yaml
  - service.yaml
  - ingress.yaml

commonLabels:
  app: metamaster
  managed-by: kustomize

commonAnnotations:
  description: "Metamaster Application"
```

### 3. Kustomization Overlay

```yaml
# k8s/overlays/prod/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

bases:
  - ../../base

replicas:
  - name: metamaster-api
    count: 3

images:
  - name: metamaster
    newTag: v1.0.0

patchesStrategicMerge:
  - patches/deployment.yaml
  - patches/service.yaml

configMapGenerator:
  - name: metamaster-config
    behavior: merge
    literals:
      - APP_ENV=production
      - LOG_LEVEL=WARNING

secretGenerator:
  - name: metamaster-secrets
    behavior: merge
    envs:
      - secrets.env
```

## Configuration Management

### 1. Ansible Playbook

```yaml
# ansible/playbooks/deploy.yml
---
- name: Deploy Metamaster Application
  hosts: all
  become: yes
  
  vars:
    app_user: metamaster
    app_home: /opt/metamaster
    app_version: "{{ version | default('latest') }}"
  
  tasks:
    - name: Create application user
      user:
        name: "{{ app_user }}"
        home: "{{ app_home }}"
        shell: /bin/bash
    
    - name: Clone repository
      git:
        repo: https://github.com/your-org/metamaster.git
        dest: "{{ app_home }}"
        version: "{{ app_version }}"
      become_user: "{{ app_user }}"
    
    - name: Install dependencies
      pip:
        requirements: "{{ app_home }}/requirements.txt"
        virtualenv: "{{ app_home }}/venv"
    
    - name: Copy environment file
      template:
        src: .env.j2
        dest: "{{ app_home }}/.env"
        owner: "{{ app_user }}"
        mode: '0600'
    
    - name: Run migrations
      command: "{{ app_home }}/venv/bin/alembic upgrade head"
      environment:
        DATABASE_URL: "{{ database_url }}"
    
    - name: Start application
      systemd:
        name: metamaster-api
        state: started
        enabled: yes
```

## Best Practices

### 1. Code Organization

```
infrastructure/
├── README.md
├── .gitignore
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── modules/
│   └── environments/
├── cloudformation/
│   ├── templates/
│   └── parameters/
├── kubernetes/
│   ├── base/
│   └── overlays/
├── ansible/
│   ├── playbooks/
│   ├── roles/
│   └── inventory/
└── scripts/
    ├── deploy.sh
    ├── destroy.sh
    └── validate.sh
```

### 2. Version Control

```bash
# .gitignore
# Terraform
*.tfstate
*.tfstate.*
.terraform/
.terraform.lock.hcl
terraform.tfvars
!terraform.tfvars.example

# Ansible
*.retry
vault_password

# Kubernetes
secrets.yaml
kustomization.yaml.bak

# General
.env
.env.local
*.log
```

### 3. Documentation

```markdown
# Infrastructure as Code Documentation

## Prerequisites
- Terraform 1.0+
- AWS CLI configured
- kubectl 1.20+

## Deployment

### Development
```bash
terraform apply -var-file=environments/dev/terraform.tfvars
```

### Production
```bash
terraform apply -var-file=environments/prod/terraform.tfvars
```

## Maintenance
- Review and update dependencies monthly
- Test disaster recovery quarterly
- Document all changes
```

## Deployment Automation

### 1. CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml
name: Deploy Infrastructure

on:
  push:
    branches:
      - main
    paths:
      - 'infrastructure/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v2
      
      - name: Terraform Init
        run: terraform init
        working-directory: terraform
      
      - name: Terraform Plan
        run: terraform plan -out=tfplan
        working-directory: terraform
      
      - name: Terraform Apply
        run: terraform apply tfplan
        working-directory: terraform
```

## Version Control

### 1. Git Workflow

```bash
# Create feature branch
git checkout -b feature/add-monitoring

# Make changes
git add infrastructure/

# Commit changes
git commit -m "Add monitoring infrastructure"

# Push to remote
git push origin feature/add-monitoring

# Create pull request
# Review and merge
```

## Maintenance

### 1. Regular Updates

```bash
# Update Terraform providers
terraform init -upgrade

# Update Kubernetes manifests
kubectl apply -f k8s/

# Update Ansible playbooks
ansible-playbook ansible/playbooks/update.yml
```

### 2. Backup and Recovery

```bash
# Backup Terraform state
aws s3 cp terraform.tfstate s3://backups/terraform/

# Backup Kubernetes resources
kubectl get all -A -o yaml > k8s_backup.yaml

# Restore from backup
kubectl apply -f k8s_backup.yaml
```

## Next Steps

1. [Main Deployment Guide](DEPLOYMENT.md)
2. [Kubernetes Deployment](DEPLOYMENT_KUBERNETES.md)
3. [Cloud Deployment](DEPLOYMENT_CLOUD.md)
4. [Security Configuration](DEPLOYMENT_SECURITY.md)
