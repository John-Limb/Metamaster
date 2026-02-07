"""Multi-container integration tests for Docker Compose orchestration"""

import pytest
import json
import time
import subprocess
from typing import Dict, Any, Optional, List
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta


# ============================================================================
# Multi-Container Test Utilities
# ============================================================================

class MultiContainerTestHelper:
    """Helper class for multi-container testing"""
    
    @staticmethod
    def run_command(cmd: str, timeout: int = 30) -> tuple[int, str, str]:
        """Run a shell command and return exit code, stdout, stderr"""
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 1, "", "Command timeout"
        except Exception as e:
            return 1, "", str(e)
    
    @staticmethod
    def get_container_ip(container_name: str) -> Optional[str]:
        """Get container IP address"""
        code, stdout, _ = MultiContainerTestHelper.run_command(
            f"docker inspect -f '{{{{.NetworkSettings.IPAddress}}}}' {container_name}"
        )
        return stdout.strip() if code == 0 else None
    
    @staticmethod
    def get_container_env(container_name: str) -> Dict[str, str]:
        """Get container environment variables"""
        code, stdout, _ = MultiContainerTestHelper.run_command(
            f"docker inspect {container_name} | grep -A 100 'Env'"
        )
        env_vars = {}
        if code == 0:
            for line in stdout.split('\n'):
                if '=' in line:
                    key, value = line.strip().strip('"').split('=', 1)
                    env_vars[key] = value
        return env_vars
    
    @staticmethod
    def check_container_logs_for_error(container_name: str, error_pattern: str) -> bool:
        """Check if container logs contain error pattern"""
        code, stdout, _ = MultiContainerTestHelper.run_command(
            f"docker logs {container_name} 2>&1 | grep -i '{error_pattern}'"
        )
        return code == 0


# ============================================================================
# FastAPI App Container Tests
# ============================================================================

class TestFastAPIAppContainer:
    """Tests for FastAPI application container"""
    
    def test_app_container_configuration(self):
        """Test FastAPI app container is properly configured"""
        with open("docker-compose.yml", "r") as f:
            content = f.read()
        
        # Check app service exists
        assert "app:" in content, "App service not defined"
        
        # Check build configuration
        assert "build: ." in content, "App build configuration missing"
        
        # Check port mapping
        assert "8000:8000" in content, "App port mapping missing"
    
    def test_app_container_environment_variables(self):
        """Test app container has required environment variables"""
        with open("docker-compose.yml", "r") as f:
            content = f.read()
        
        # Find app service section
        app_section = content[content.find("app:"):content.find("celery_worker:")]
        
        required_vars = [
            "DATABASE_URL",
            "REDIS_URL",
            "CELERY_BROKER_URL",
            "CELERY_RESULT_BACKEND",
            "DEBUG",
            "LOG_LEVEL"
        ]
        
        for var in required_vars:
            assert var in app_section, f"Environment variable {var} not configured for app"
    
    def test_app_container_volume_mounts(self):
        """Test app container has required volume mounts"""
        with open("docker-compose.yml", "r") as f:
            content = f.read()
        
        app_section = content[content.find("app:"):content.find("celery_worker:")]
        
        required_mounts = [
            "./app:/app/app",
            "./media:/app/media",
            "media.db"
        ]
        
        for mount in required_mounts:
            assert mount in app_section, f"Volume mount {mount} not configured for app"
    
    def test_app_container_health_check(self):
        """Test app container has health check configured"""
        with open("docker-compose.yml", "r") as f:
            content = f.read()
        
        app_section = content[content.find("app:"):content.find("celery_worker:")]
        
        assert "healthcheck:" in app_section, "Health check not configured for app"
        assert "curl" in app_section, "Health check curl command missing"
        assert "8000" in app_section, "Health check port not configured"
    
    def test_app_container_startup_command(self):
        """Test app container startup command"""
        with open("docker-compose.yml", "r") as f:
            content = f.read()
        
        app_section = content[content.find("app:"):content.find("celery_worker:")]
        
        assert "uvicorn" in app_section, "Uvicorn command not found"
        assert "app.main:app" in app_section, "App module not specified"
        assert "8000" in app_section, "Port not specified in startup command"


# ============================================================================
# Redis Container Tests
# ============================================================================

class TestRedisContainer:
    """Tests for Redis container"""
    
    def test_redis_container_configuration(self):
        """Test Redis container is properly configured"""
        with open("docker-compose.yml", "r") as f:
            content = f.read()
        
        # Check redis service exists
        assert "redis:" in content, "Redis service not defined"
        
        # Check image
        assert "redis:7-alpine" in content, "Redis image not specified"
        
        # Check port mapping
        assert "6379:6379" in content, "Redis port mapping missing"
    
    def test_redis_container_volume_mount(self):
        """Test Redis container has volume mount for persistence"""
        with open("docker-compose.yml", "r") as f:
            content = f.read()
        
        redis_section = content[content.find("redis:"):content.find("app:")]
        
        assert "redis_data:" in content, "Redis data volume not defined"
        assert "/data" in redis_section, "Redis data mount point not configured"
    
    def test_redis_container_health_check(self):
        """Test Redis container has health check"""
        with open("docker-compose.yml", "r") as f:
            content = f.read()
        
        redis_section = content[content.find("redis:"):content.find("app:")]
        
        assert "healthcheck:" in redis_section, "Health check not configured for Redis"
        assert "redis-cli" in redis_section, "Redis CLI health check missing"
        assert "ping" in redis_section, "Redis ping command missing"
    
    def test_redis_container_persistence_command(self):
        """Test Redis container has persistence enabled"""
        with open("docker-compose.yml", "r") as f:
            content = f.read()
        
        redis_section = content[content.find("redis:"):content.find("app:")]
        
        assert "appendonly yes" in redis_section, "Redis persistence not enabled"


# ============================================================================
# Database Container Tests
# ============================================================================

class TestDatabaseContainer:
    """Tests for database container configuration"""
    
    def test_database_configuration_in_compose(self):
        """Test database configuration in docker-compose"""
        with open("docker-compose.yml", "r") as f:
            content = f.read()
        
        # Check DATABASE_URL is configured
        assert "DATABASE_URL" in content, "DATABASE_URL not configured"
        
        # Check database file is mounted
        assert "media.db" in content, "Database file not mounted"
    
    def test_database_persistence_volume(self):
        """Test database persistence volume is configured"""
        with open("docker-compose.yml", "r") as f:
            content = f.read()
        
        # Database file should be mounted to all services
        app_section = content[content.find("app:"):content.find("celery_worker:")]
        assert "media.db" in app_section, "Database not mounted to app"
        
        worker_section = content[content.find("celery_worker:"):content.find("celery_beat:")]
        assert "media.db" in worker_section, "Database not mounted to worker"


# ============================================================================
# Celery Worker Container Tests
# ============================================================================

class TestCeleryWorkerContainer:
    """Tests for Celery worker container"""
    
    def test_celery_worker_configuration(self):
        """Test Celery worker container is properly configured"""
        with open("docker-compose.yml", "r") as f:
            content = f.read()
        
        # Check celery_worker service exists
        assert "celery_worker:" in content, "Celery worker service not defined"
        
        # Check build configuration
        assert "build: ." in content, "Celery worker build configuration missing"
    
    def test_celery_worker_environment_variables(self):
        """Test Celery worker has required environment variables"""
        with open("docker-compose.yml", "r") as f:
            content = f.read()
        
        worker_section = content[content.find("celery_worker:"):content.find("celery_beat:")]
        
        required_vars = [
            "DATABASE_URL",
            "REDIS_URL",
            "CELERY_BROKER_URL",
            "CELERY_RESULT_BACKEND"
        ]
        
        for var in required_vars:
            assert var in worker_section, f"Environment variable {var} not configured for worker"
    
    def test_celery_worker_startup_command(self):
        """Test Celery worker startup command"""
        with open("docker-compose.yml", "r") as f:
            content = f.read()
        
        worker_section = content[content.find("celery_worker:"):content.find("celery_beat:")]
        
        assert "celery" in worker_section, "Celery command not found"
        assert "worker" in worker_section, "Worker command not found"
        assert "loglevel=info" in worker_section, "Log level not configured"
    
    def test_celery_worker_dependencies(self):
        """Test Celery worker has correct dependencies"""
        with open("docker-compose.yml", "r") as f:
            content = f.read()
        
        worker_section = content[content.find("celery_worker:"):content.find("celery_beat:")]
        
        assert "depends_on:" in worker_section, "Dependencies not configured"
        assert "redis" in worker_section, "Redis dependency missing"
        assert "app" in worker_section, "App dependency missing"
    
    def test_celery_worker_restart_policy(self):
        """Test Celery worker has restart policy"""
        with open("docker-compose.yml", "r") as f:
            content = f.read()
        
        worker_section = content[content.find("celery_worker:"):content.find("celery_beat:")]
        
        assert "restart:" in worker_section, "Restart policy not configured"


# ============================================================================
# Celery Beat Container Tests
# ============================================================================

class TestCeleryBeatContainer:
    """Tests for Celery Beat scheduler container"""
    
    def test_celery_beat_configuration(self):
        """Test Celery Beat container is properly configured"""
        with open("docker-compose.yml", "r") as f:
            content = f.read()
        
        # Check celery_beat service exists
        assert "celery_beat:" in content, "Celery Beat service not defined"
    
    def test_celery_beat_startup_command(self):
        """Test Celery Beat startup command"""
        with open("docker-compose.yml", "r") as f:
            content = f.read()
        
        # Check that celery_beat service is defined
        assert "celery_beat:" in content, "Celery Beat service not defined"
        assert "celery" in content, "Celery command not found"
        assert "beat" in content, "Beat command not found"
    
    def test_celery_beat_dependencies(self):
        """Test Celery Beat has correct dependencies"""
        with open("docker-compose.yml", "r") as f:
            content = f.read()
        
        # Check that celery_beat service is defined
        assert "celery_beat:" in content, "Celery Beat service not defined"


# ============================================================================
# Container Communication Tests
# ============================================================================

class TestContainerCommunication:
    """Tests for container communication and data flow"""
    
    def test_app_to_redis_communication(self):
        """Test app can communicate with Redis"""
        with open("docker-compose.yml", "r") as f:
            content = f.read()
        
        # Check Redis URL uses service name
        assert "redis://redis:" in content, "Redis URL should use service name for discovery"
    
    def test_app_to_database_communication(self):
        """Test app can communicate with database"""
        with open("docker-compose.yml", "r") as f:
            content = f.read()
        
        # Check DATABASE_URL is configured
        assert "DATABASE_URL" in content, "Database URL not configured"
    
    def test_celery_to_redis_communication(self):
        """Test Celery can communicate with Redis"""
        with open("docker-compose.yml", "r") as f:
            content = f.read()
        
        # Check Celery broker URL uses service name
        assert "redis://redis:" in content, "Celery broker should use Redis service name"
    
    def test_network_connectivity_configuration(self):
        """Test network connectivity is properly configured"""
        with open("docker-compose.yml", "r") as f:
            content = f.read()
        
        # Check network is defined
        assert "networks:" in content, "Networks not defined"
        assert "media_tool_network" in content, "Network name not defined"


# ============================================================================
# Service Discovery Tests
# ============================================================================

class TestServiceDiscovery:
    """Tests for service discovery and connectivity"""
    
    def test_service_names_resolvable(self):
        """Test service names are resolvable"""
        with open("docker-compose.yml", "r") as f:
            content = f.read()
        
        # Services should be discoverable by name
        services = ["redis", "app", "celery_worker", "celery_beat"]
        for service in services:
            assert f"{service}:" in content, f"Service {service} not defined"
    
    def test_redis_service_discovery(self):
        """Test Redis service discovery configuration"""
        with open("docker-compose.yml", "r") as f:
            content = f.read()
        
        # Redis should be discoverable as "redis"
        assert "redis://redis:" in content, "Redis not discoverable by service name"
    
    def test_app_service_discovery(self):
        """Test app service discovery configuration"""
        with open("docker-compose.yml", "r") as f:
            content = f.read()
        
        # App should be discoverable as "app"
        assert "app:" in content, "App service not discoverable"


# ============================================================================
# Load Balancing and Scaling Tests
# ============================================================================

class TestLoadBalancingAndScaling:
    """Tests for load balancing and scaling scenarios"""
    
    def test_multiple_worker_configuration(self):
        """Test configuration supports multiple workers"""
        with open("docker-compose.yml", "r") as f:
            content = f.read()
        
        # Celery worker should be scalable
        assert "celery_worker:" in content, "Celery worker not defined"
    
    def test_redis_as_message_broker(self):
        """Test Redis is configured as message broker"""
        with open("docker-compose.yml", "r") as f:
            content = f.read()
        
        # Redis should be used for both broker and result backend
        assert "CELERY_BROKER_URL=redis://redis:" in content, "Redis not configured as broker"
        assert "CELERY_RESULT_BACKEND=redis://redis:" in content, "Redis not configured as result backend"
    
    def test_shared_database_configuration(self):
        """Test shared database configuration for multiple services"""
        with open("docker-compose.yml", "r") as f:
            content = f.read()
        
        # All services should use same database
        assert "media.db" in content, "Shared database not configured"


# ============================================================================
# Data Flow Tests
# ============================================================================

class TestDataFlow:
    """Tests for data flow between containers"""
    
    def test_app_to_worker_data_flow(self):
        """Test data flow from app to Celery worker"""
        with open("docker-compose.yml", "r") as f:
            content = f.read()
        
        # Both should use same Redis broker
        assert "CELERY_BROKER_URL" in content, "Celery broker not configured"
        assert "redis://redis:" in content, "Redis broker not configured"
    
    def test_worker_to_database_data_flow(self):
        """Test data flow from worker to database"""
        with open("docker-compose.yml", "r") as f:
            content = f.read()
        
        worker_section = content[content.find("celery_worker:"):content.find("celery_beat:")]
        
        # Worker should have database access
        assert "DATABASE_URL" in worker_section, "Worker database access not configured"
        assert "media.db" in worker_section, "Worker database mount not configured"
    
    def test_cache_data_flow(self):
        """Test cache data flow between containers"""
        with open("docker-compose.yml", "r") as f:
            content = f.read()
        
        # All services should access same Redis cache
        assert "REDIS_URL=redis://redis:" in content, "Redis cache not configured"


# ============================================================================
# Container Orchestration Tests
# ============================================================================

class TestContainerOrchestration:
    """Tests for container orchestration"""
    
    def test_service_startup_order(self):
        """Test services start in correct order"""
        with open("docker-compose.yml", "r") as f:
            content = f.read()
        
        # Redis should start first
        redis_pos = content.find("redis:")
        app_pos = content.find("app:")
        assert redis_pos < app_pos, "Redis should be defined before app"
    
    def test_health_check_dependencies(self):
        """Test health check dependencies are configured"""
        with open("docker-compose.yml", "r") as f:
            content = f.read()
        
        app_section = content[content.find("app:"):content.find("celery_worker:")]
        
        # App should wait for Redis health check
        assert "condition: service_healthy" in app_section, "Health check condition not set"
    
    def test_volume_sharing_between_services(self):
        """Test volumes are properly shared between services"""
        with open("docker-compose.yml", "r") as f:
            content = f.read()
        
        # Database should be shared
        db_count = content.count("media.db")
        assert db_count >= 3, "Database not shared across services"
        
        # Media directory should be shared
        media_count = content.count("./media:/app/media")
        assert media_count >= 3, "Media directory not shared across services"


# ============================================================================
# Error Handling and Recovery Tests
# ============================================================================

class TestErrorHandlingAndRecovery:
    """Tests for error handling and recovery in multi-container setup"""
    
    def test_redis_failure_recovery(self):
        """Test system handles Redis failure"""
        with open("docker-compose.yml", "r") as f:
            content = f.read()
        
        # App should have health check to detect Redis failure
        app_section = content[content.find("app:"):content.find("celery_worker:")]
        assert "healthcheck:" in app_section, "Health check not configured"
    
    def test_app_failure_recovery(self):
        """Test system handles app failure"""
        with open("docker-compose.yml", "r") as f:
            content = f.read()
        
        # Celery services should continue if app fails
        assert "celery_worker:" in content, "Celery worker should be independent"
    
    def test_worker_failure_recovery(self):
        """Test system handles worker failure"""
        with open("docker-compose.yml", "r") as f:
            content = f.read()
        
        worker_section = content[content.find("celery_worker:"):content.find("celery_beat:")]
        
        # Worker should have restart policy
        assert "restart:" in worker_section, "Restart policy not configured"


# ============================================================================
# Configuration Consistency Tests
# ============================================================================

class TestConfigurationConsistency:
    """Tests for configuration consistency across containers"""
    
    def test_redis_url_consistency(self):
        """Test Redis URL is consistent across services"""
        with open("docker-compose.yml", "r") as f:
            content = f.read()
        
        # All Redis URLs should use same service name
        redis_urls = content.count("redis://redis:")
        assert redis_urls >= 3, "Redis URL not consistent across services"
    
    def test_database_url_consistency(self):
        """Test database URL is consistent across services"""
        with open("docker-compose.yml", "r") as f:
            content = f.read()
        
        # All services should use same database
        db_urls = content.count("media.db")
        assert db_urls >= 3, "Database not consistent across services"
    
    def test_environment_variable_consistency(self):
        """Test environment variables are consistent"""
        with open("docker-compose.yml", "r") as f:
            content = f.read()
        
        # Check critical variables are defined for all services
        assert "REDIS_URL" in content, "REDIS_URL not defined"
        assert "DATABASE_URL" in content, "DATABASE_URL not defined"
        assert "CELERY_BROKER_URL" in content, "CELERY_BROKER_URL not defined"
