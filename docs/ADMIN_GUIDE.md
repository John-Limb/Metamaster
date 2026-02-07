# Administrator Guide

This guide provides comprehensive instructions for system administrators managing the Media Library Management System.

## Table of Contents

1. [System Administration Overview](#system-administration-overview)
2. [User Management](#user-management)
3. [System Configuration](#system-configuration)
4. [Monitoring and Maintenance](#monitoring-and-maintenance)
5. [Backup and Recovery](#backup-and-recovery)
6. [Performance Tuning](#performance-tuning)
7. [Security Management](#security-management)
8. [Troubleshooting for Admins](#troubleshooting-for-admins)

## System Administration Overview

### Administrator Responsibilities

As a system administrator, you are responsible for:

- **User Management**: Creating, modifying, and removing user accounts
- **System Configuration**: Configuring system settings and preferences
- **Monitoring**: Monitoring system health and performance
- **Maintenance**: Performing regular maintenance tasks
- **Backup and Recovery**: Ensuring data is backed up and recoverable
- **Security**: Managing security settings and access controls
- **Performance**: Optimizing system performance
- **Support**: Providing technical support to users

### Accessing Administration Panel

1. Log in with an administrator account
2. Navigate to **Settings** → **Administration**
3. The administration panel provides access to all admin functions
4. Use the left sidebar to navigate between sections

### Administrator Roles

The system supports multiple administrator roles:

- **Super Administrator**: Full system access and control
- **User Administrator**: Manage users and permissions
- **System Administrator**: Manage system configuration and maintenance
- **Security Administrator**: Manage security settings and access control
- **Support Administrator**: Provide user support and troubleshooting

## User Management

### Creating User Accounts

1. Navigate to **Administration** → **Users**
2. Click the **"Add User"** button
3. Enter user information:
   - **Username** (required): Unique username for login
   - **Email** (required): User's email address
   - **Full Name** (optional): User's full name
   - **Password** (required): Initial password (user should change on first login)
   - **Role** (required): Select user role
   - **Department** (optional): User's department
   - **Phone** (optional): User's phone number
4. Click **"Create User"** to add the account
5. Send login credentials to the user securely

### Modifying User Accounts

1. Navigate to **Administration** → **Users**
2. Find the user in the list or search for them
3. Click on the user to open their profile
4. Click the **"Edit"** button
5. Modify user information:
   - Full name
   - Email address
   - Department
   - Phone number
   - Role
   - Status (Active/Inactive)
6. Click **"Save"** to update the user

### Resetting User Passwords

1. Navigate to **Administration** → **Users**
2. Find the user and click on their profile
3. Click the **"Reset Password"** button
4. Choose password reset method:
   - **Generate Temporary Password**: System generates a temporary password
   - **Send Reset Link**: Send email with password reset link
5. Confirm the action
6. Provide the temporary password or reset link to the user

### Disabling User Accounts

1. Navigate to **Administration** → **Users**
2. Find the user and click on their profile
3. Click the **"Disable Account"** button
4. Confirm the action
5. The user will no longer be able to log in
6. To re-enable, click **"Enable Account"**

### Deleting User Accounts

1. Navigate to **Administration** → **Users**
2. Find the user and click on their profile
3. Click the **"Delete Account"** button
4. Confirm the deletion
5. The user account will be permanently deleted
6. (Optional) Choose to archive user data before deletion

### Managing User Permissions

1. Navigate to **Administration** → **Permissions**
2. Select a user or role
3. Configure permissions:
   - **View Movies**: Can view movie library
   - **Add Movies**: Can add new movies
   - **Edit Movies**: Can modify movie information
   - **Delete Movies**: Can delete movies
   - **View TV Shows**: Can view TV show library
   - **Add TV Shows**: Can add new TV shows
   - **Edit TV Shows**: Can modify TV show information
   - **Delete TV Shows**: Can delete TV shows
   - **Batch Operations**: Can perform batch operations
   - **Metadata Sync**: Can sync metadata
   - **Export Data**: Can export library data
   - **Administration**: Can access admin panel
4. Click **"Save"** to apply permissions

### User Groups

Create groups to manage permissions for multiple users:

1. Navigate to **Administration** → **User Groups**
2. Click **"Create Group"**
3. Enter group name (e.g., "Movie Editors", "Viewers")
4. Add users to the group:
   - Click **"Add Users"**
   - Select users to add
   - Click **"Add"**
5. Configure group permissions
6. Click **"Save"** to create the group

## System Configuration

### General Settings

1. Navigate to **Administration** → **Settings** → **General**
2. Configure:
   - **System Name**: Display name for the system
   - **System Description**: Brief description
   - **Logo**: Upload system logo
   - **Favicon**: Upload favicon
   - **Theme**: Choose color theme
   - **Language**: Default system language
   - **Timezone**: System timezone
3. Click **"Save"** to apply settings

### Email Configuration

1. Navigate to **Administration** → **Settings** → **Email**
2. Configure email settings:
   - **SMTP Server**: Email server address
   - **SMTP Port**: Email server port (usually 587 or 465)
   - **SMTP Username**: Email account username
   - **SMTP Password**: Email account password
   - **From Address**: Email address to send from
   - **From Name**: Display name for emails
   - **Use TLS**: Enable TLS encryption
   - **Use SSL**: Enable SSL encryption
3. Click **"Test Email"** to verify configuration
4. Click **"Save"** to apply settings

### Metadata Sources Configuration

1. Navigate to **Administration** → **Settings** → **Metadata Sources**
2. Configure available metadata sources:
   - **OMDB API Key**: Open Movie Database API key
   - **TMDB API Key**: The Movie Database API key
   - **TVDB API Key**: The TV Database API key
3. For each source:
   - Enter API key
   - Enable/disable the source
   - Set priority (which source to use first)
4. Click **"Test Connection"** to verify
5. Click **"Save"** to apply settings

### Storage Configuration

1. Navigate to **Administration** → **Settings** → **Storage**
2. Configure storage settings:
   - **Storage Path**: Location for storing files
   - **Maximum File Size**: Maximum upload size
   - **Allowed File Types**: Types of files allowed
   - **Auto-cleanup**: Enable automatic cleanup of old files
   - **Cleanup Age**: How old files must be before cleanup
3. Click **"Save"** to apply settings

### Backup Configuration

1. Navigate to **Administration** → **Settings** → **Backup**
2. Configure backup settings:
   - **Backup Location**: Where to store backups
   - **Backup Frequency**: How often to backup (Daily, Weekly, Monthly)
   - **Backup Time**: What time to perform backups
   - **Retention Period**: How long to keep backups
   - **Backup Type**: Full or incremental backups
3. Click **"Save"** to apply settings

## Monitoring and Maintenance

### System Health Dashboard

1. Navigate to **Administration** → **Monitoring** → **Health**
2. View system health metrics:
   - **System Status**: Overall system status
   - **CPU Usage**: Current CPU usage percentage
   - **Memory Usage**: Current memory usage percentage
   - **Disk Space**: Available disk space
   - **Database Status**: Database connection status
   - **Cache Status**: Cache system status
   - **API Status**: API service status
   - **Background Jobs**: Status of background jobs

### Performance Metrics

1. Navigate to **Administration** → **Monitoring** → **Performance**
2. View performance metrics:
   - **Response Time**: Average API response time
   - **Requests Per Second**: Current request rate
   - **Database Queries**: Number of database queries
   - **Cache Hit Rate**: Percentage of cache hits
   - **Error Rate**: Percentage of failed requests
3. View historical data:
   - Select time range
   - View trends and patterns
   - Identify performance issues

### Activity Logs

1. Navigate to **Administration** → **Monitoring** → **Logs**
2. View system activity logs:
   - **User Activity**: User login/logout events
   - **Data Changes**: Modifications to data
   - **System Events**: System-level events
   - **Error Logs**: Error messages and stack traces
3. Filter logs by:
   - Date range
   - User
   - Event type
   - Severity level
4. Export logs for analysis

### Maintenance Tasks

#### Database Optimization

1. Navigate to **Administration** → **Maintenance** → **Database**
2. Click **"Optimize Database"**
3. The system will:
   - Analyze tables
   - Rebuild indexes
   - Reclaim unused space
4. Monitor progress in the status panel
5. Review results when complete

#### Cache Clearing

1. Navigate to **Administration** → **Maintenance** → **Cache**
2. Choose cache to clear:
   - **All Cache**: Clear all cached data
   - **Application Cache**: Clear application cache
   - **Search Cache**: Clear search results cache
   - **Metadata Cache**: Clear metadata cache
3. Click **"Clear Cache"**
4. Confirm the action
5. Cache will be cleared and rebuilt on next use

#### Temporary File Cleanup

1. Navigate to **Administration** → **Maintenance** → **Cleanup**
2. Click **"Clean Temporary Files"**
3. The system will:
   - Identify old temporary files
   - Remove files older than configured age
   - Free up disk space
4. Review results showing:
   - Number of files deleted
   - Space freed
   - Any errors encountered

#### Database Backup

1. Navigate to **Administration** → **Maintenance** → **Backup**
2. Click **"Create Backup"**
3. Choose backup type:
   - **Full Backup**: Complete database backup
   - **Incremental Backup**: Only changes since last backup
4. Click **"Start Backup"**
5. Monitor progress in the status panel
6. Backup will be saved to configured location

## Backup and Recovery

### Creating Backups

#### Manual Backup

1. Navigate to **Administration** → **Backup** → **Create Backup**
2. Choose backup scope:
   - **Full System**: Database and all files
   - **Database Only**: Database backup only
   - **Files Only**: File storage backup only
3. Choose backup type:
   - **Full Backup**: Complete backup
   - **Incremental**: Only changes since last backup
4. Click **"Create Backup"**
5. Monitor progress and download when complete

#### Scheduled Backups

1. Navigate to **Administration** → **Settings** → **Backup**
2. Enable **"Scheduled Backups"**
3. Configure:
   - **Frequency**: Daily, Weekly, or Monthly
   - **Time**: What time to perform backup
   - **Type**: Full or incremental
   - **Retention**: How long to keep backups
4. Click **"Save"**
5. Backups will run automatically on schedule

### Viewing Backup History

1. Navigate to **Administration** → **Backup** → **History**
2. View all backups:
   - Backup date and time
   - Backup type (Full/Incremental)
   - Backup size
   - Status (Successful/Failed)
   - Retention expiration date
3. Click on a backup to view details
4. Download or delete backups as needed

### Restoring from Backup

1. Navigate to **Administration** → **Backup** → **Restore**
2. Choose backup to restore:
   - Select from list of available backups
   - Or upload a backup file
3. Choose restore scope:
   - **Full Restore**: Restore entire system
   - **Database Only**: Restore database only
   - **Files Only**: Restore files only
4. Click **"Preview"** to see what will be restored
5. Click **"Restore"** to begin restoration
6. Monitor progress in the status panel
7. System will restart after restoration completes

### Disaster Recovery

In case of system failure:

1. **Assess Damage**: Determine what data is lost or corrupted
2. **Locate Latest Backup**: Find the most recent good backup
3. **Restore System**: Follow restoration procedure above
4. **Verify Data**: Check that data is intact and correct
5. **Resume Operations**: Bring system back online
6. **Document Incident**: Record what happened and how it was resolved

## Performance Tuning

### Database Performance

1. Navigate to **Administration** → **Performance** → **Database**
2. Configure database settings:
   - **Connection Pool Size**: Number of database connections
   - **Query Timeout**: Maximum query execution time
   - **Index Strategy**: Automatic or manual indexing
3. Monitor database performance:
   - Query execution time
   - Number of slow queries
   - Index usage
4. Optimize as needed:
   - Add indexes for frequently queried fields
   - Archive old data
   - Partition large tables

### Cache Performance

1. Navigate to **Administration** → **Performance** → **Cache**
2. Configure cache settings:
   - **Cache Type**: Redis, Memcached, or In-Memory
   - **Cache Size**: Maximum cache size
   - **TTL**: Time-to-live for cached items
   - **Eviction Policy**: How to handle cache overflow
3. Monitor cache performance:
   - Cache hit rate
   - Cache miss rate
   - Cache size
4. Optimize as needed:
   - Increase cache size if hit rate is low
   - Adjust TTL based on data freshness needs
   - Monitor memory usage

### API Performance

1. Navigate to **Administration** → **Performance** → **API**
2. Configure API settings:
   - **Rate Limiting**: Requests per second per user
   - **Timeout**: API request timeout
   - **Batch Size**: Maximum items per batch operation
   - **Pagination**: Default items per page
3. Monitor API performance:
   - Response time
   - Request rate
   - Error rate
4. Optimize as needed:
   - Adjust rate limits based on load
   - Increase batch size for better throughput
   - Optimize slow endpoints

### Background Jobs

1. Navigate to **Administration** → **Performance** → **Jobs**
2. Configure job settings:
   - **Worker Threads**: Number of background workers
   - **Job Timeout**: Maximum job execution time
   - **Retry Policy**: How many times to retry failed jobs
   - **Queue Size**: Maximum pending jobs
3. Monitor job performance:
   - Number of pending jobs
   - Job success rate
   - Average job duration
4. Optimize as needed:
   - Increase workers if queue is growing
   - Adjust timeout for long-running jobs
   - Review failed jobs for issues

## Security Management

### User Authentication

1. Navigate to **Administration** → **Security** → **Authentication**
2. Configure authentication settings:
   - **Password Policy**: Minimum length, complexity requirements
   - **Session Timeout**: How long before session expires
   - **Login Attempts**: Maximum failed login attempts
   - **Account Lockout**: Lock account after failed attempts
   - **Two-Factor Authentication**: Enable 2FA requirement
3. Click **"Save"** to apply settings

### Access Control

1. Navigate to **Administration** → **Security** → **Access Control**
2. Configure access control:
   - **IP Whitelist**: Allow only specific IP addresses
   - **IP Blacklist**: Block specific IP addresses
   - **VPN Required**: Require VPN for access
   - **SSL/TLS**: Require encrypted connections
3. Click **"Save"** to apply settings

### API Security

1. Navigate to **Administration** → **Security** → **API**
2. Configure API security:
   - **API Keys**: Generate and manage API keys
   - **Rate Limiting**: Limit requests per API key
   - **CORS**: Configure cross-origin requests
   - **API Versioning**: Manage API versions
3. Click **"Save"** to apply settings

### Data Encryption

1. Navigate to **Administration** → **Security** → **Encryption**
2. Configure encryption:
   - **Database Encryption**: Encrypt sensitive data in database
   - **File Encryption**: Encrypt uploaded files
   - **Backup Encryption**: Encrypt backup files
   - **Encryption Key**: Manage encryption keys
3. Click **"Save"** to apply settings

### Audit Logging

1. Navigate to **Administration** → **Security** → **Audit**
2. Configure audit logging:
   - **Enable Audit Logging**: Turn on audit trail
   - **Log Level**: What events to log
   - **Retention Period**: How long to keep logs
   - **Log Storage**: Where to store logs
3. Click **"Save"** to apply settings
4. View audit logs:
   - Navigate to **Administration** → **Logs** → **Audit**
   - Filter by user, action, date range
   - Export logs for analysis

## Troubleshooting for Admins

### Common Issues

#### System Performance Degradation

**Problem**: System is slow or unresponsive

**Diagnosis**:
1. Check CPU usage in Health Dashboard
2. Check memory usage
3. Check disk space
4. Review database query performance
5. Check cache hit rate

**Solutions**:
1. Clear cache if hit rate is low
2. Optimize slow database queries
3. Increase server resources if needed
4. Archive old data to reduce database size
5. Adjust batch operation sizes

#### Database Connection Issues

**Problem**: Cannot connect to database

**Diagnosis**:
1. Check database status in Health Dashboard
2. Verify database server is running
3. Check database credentials
4. Verify network connectivity

**Solutions**:
1. Restart database server
2. Verify connection string is correct
3. Check firewall rules
4. Verify database user has correct permissions
5. Check database logs for errors

#### Backup Failures

**Problem**: Backups are failing

**Diagnosis**:
1. Check backup logs for error messages
2. Verify backup location has sufficient space
3. Check backup schedule configuration
4. Verify backup user has correct permissions

**Solutions**:
1. Free up disk space
2. Verify backup location is accessible
3. Check backup configuration
4. Manually create backup to test
5. Review backup logs for specific errors

#### User Login Issues

**Problem**: Users cannot log in

**Diagnosis**:
1. Check if user account is active
2. Verify user credentials
3. Check authentication configuration
4. Review login logs for errors

**Solutions**:
1. Verify user account is enabled
2. Reset user password
3. Check authentication settings
4. Verify network connectivity
5. Check firewall rules for login service

#### Metadata Sync Failures

**Problem**: Metadata sync is failing

**Diagnosis**:
1. Check metadata source configuration
2. Verify API keys are valid
3. Check network connectivity
4. Review sync logs for errors

**Solutions**:
1. Verify API keys are correct and active
2. Check network connectivity to metadata sources
3. Verify rate limits haven't been exceeded
4. Try syncing with different metadata source
5. Contact metadata source provider if issues persist

### Getting Help

If you encounter issues not covered here:

1. **Check Logs**: Review system logs for error messages
2. **Check Documentation**: Review this guide and other documentation
3. **Contact Support**: Reach out to system support
4. **Review Configuration**: Verify all settings are correct
5. **Test Manually**: Try operations manually to isolate issues

### Reporting Issues

When reporting issues, include:
- Description of the problem
- Steps to reproduce
- Error messages or logs
- System configuration details
- When the issue started occurring
- Any recent changes to the system

---

For more information, see:
- [Configuration Guide](CONFIGURATION_GUIDE.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Troubleshooting Guide](USER_TROUBLESHOOTING.md)
