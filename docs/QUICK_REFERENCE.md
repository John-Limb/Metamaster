# Quick Reference Guide

This guide provides quick reference information for common tasks and features in the Media Library Management System.

## Table of Contents

1. [Keyboard Shortcuts](#keyboard-shortcuts)
2. [Common Commands](#common-commands)
3. [API Quick Reference](#api-quick-reference)
4. [Configuration Quick Reference](#configuration-quick-reference)
5. [Troubleshooting Quick Reference](#troubleshooting-quick-reference)

## Keyboard Shortcuts

### Navigation

| Shortcut | Action |
|----------|--------|
| `Ctrl+H` / `Cmd+H` | Go to Home/Dashboard |
| `Ctrl+M` / `Cmd+M` | Go to Movies |
| `Ctrl+T` / `Cmd+T` | Go to TV Shows |
| `Ctrl+S` / `Cmd+S` | Go to Search |
| `Ctrl+,` / `Cmd+,` | Go to Settings |
| `Ctrl+?` / `Cmd+?` | Show Help |

### Search and Filter

| Shortcut | Action |
|----------|--------|
| `Ctrl+F` / `Cmd+F` | Focus search box |
| `Ctrl+L` / `Cmd+L` | Clear search |
| `Ctrl+Alt+F` / `Cmd+Option+F` | Open filters |
| `Ctrl+Alt+C` / `Cmd+Option+C` | Clear filters |
| `Enter` | Execute search |
| `Escape` | Close search/filters |

### Item Management

| Shortcut | Action |
|----------|--------|
| `Ctrl+N` / `Cmd+N` | Add new item |
| `Ctrl+E` / `Cmd+E` | Edit selected item |
| `Ctrl+D` / `Cmd+D` | Delete selected item |
| `Ctrl+A` / `Cmd+A` | Select all items |
| `Ctrl+Shift+A` / `Cmd+Shift+A` | Deselect all items |
| `Ctrl+C` / `Cmd+C` | Copy selected items |
| `Ctrl+X` / `Cmd+X` | Cut selected items |
| `Ctrl+V` / `Cmd+V` | Paste items |

### Batch Operations

| Shortcut | Action |
|----------|--------|
| `Ctrl+B` / `Cmd+B` | Open batch operations |
| `Ctrl+Shift+E` / `Cmd+Shift+E` | Export selected items |
| `Ctrl+Shift+S` / `Cmd+Shift+S` | Sync metadata |
| `Ctrl+Shift+D` / `Cmd+Shift+D` | Delete selected items |

### Other

| Shortcut | Action |
|----------|--------|
| `Ctrl+Z` / `Cmd+Z` | Undo last action |
| `Ctrl+Y` / `Cmd+Y` | Redo last action |
| `Ctrl+P` / `Cmd+P` | Print current page |
| `F5` | Refresh page |
| `Escape` | Close dialogs/modals |

## Common Commands

### Adding Content

```
1. Click "Add Movie" or "Add Show"
2. Enter title
3. (Optional) Click "Search Metadata"
4. Review and confirm
5. Click "Save"
```

### Searching

```
1. Click search box or press Ctrl+F
2. Enter search term
3. (Optional) Apply filters
4. Press Enter or click Search
5. Browse results
```

### Filtering

```
1. Click "Filters" button
2. Select filter criteria
3. Click "Apply Filters"
4. Results update automatically
5. Click "Clear Filters" to reset
```

### Batch Operations

```
1. Select items using checkboxes
2. Click "Batch Operations" button
3. Choose operation type
4. Configure operation
5. Click "Start" or "Apply"
6. Monitor progress
```

### Syncing Metadata

```
1. Select items
2. Click "Sync Metadata"
3. Choose metadata source
4. Click "Start Sync"
5. Review results
6. Click "Confirm" to save
```

### Exporting Data

```
1. Select items
2. Click "Batch Export"
3. Choose format (CSV/JSON/Excel)
4. Select fields to include
5. Click "Export"
6. Download file
```

### Marking as Watched

```
For Movies:
1. Click on movie
2. Click "Mark as Watched"
3. (Optional) Set date
4. Confirm

For TV Shows:
1. Click on show
2. Click "Seasons" tab
3. Check episode checkbox
4. Changes save automatically
```

### Adding Notes

```
1. Click on item
2. Scroll to "Notes" section
3. Click "Add Note"
4. Enter note text
5. Click "Save Note"
```

### Rating Content

```
1. Click on item
2. Click "Rate" button
3. Select rating (1-10)
4. (Optional) Add review
5. Click "Save"
```

## API Quick Reference

### Base URL

```
http://localhost:8000/api/v1
```

### Authentication

```
Header: Authorization: Bearer {token}
```

### Movies Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/movies` | List all movies |
| `POST` | `/movies` | Create new movie |
| `GET` | `/movies/{id}` | Get movie details |
| `PUT` | `/movies/{id}` | Update movie |
| `DELETE` | `/movies/{id}` | Delete movie |
| `POST` | `/movies/{id}/sync` | Sync movie metadata |
| `POST` | `/movies/{id}/watch` | Mark as watched |

### TV Shows Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/shows` | List all TV shows |
| `POST` | `/shows` | Create new show |
| `GET` | `/shows/{id}` | Get show details |
| `PUT` | `/shows/{id}` | Update show |
| `DELETE` | `/shows/{id}` | Delete show |
| `GET` | `/shows/{id}/seasons` | Get seasons |
| `GET` | `/shows/{id}/episodes` | Get episodes |
| `POST` | `/shows/{id}/sync` | Sync show metadata |

### Search Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/search` | Search all content |
| `GET` | `/search/movies` | Search movies |
| `GET` | `/search/shows` | Search TV shows |

### Batch Operations Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/batch/edit` | Batch edit items |
| `POST` | `/batch/delete` | Batch delete items |
| `POST` | `/batch/export` | Batch export items |
| `POST` | `/batch/sync` | Batch sync metadata |
| `GET` | `/batch/status/{id}` | Get operation status |
| `POST` | `/batch/cancel/{id}` | Cancel operation |

### Query Parameters

```
?page=1              # Page number
?limit=25            # Items per page
?sort=title          # Sort field
?order=asc           # Sort order (asc/desc)
?genre=Drama         # Filter by genre
?rating_min=7.0      # Minimum rating
?rating_max=10.0     # Maximum rating
?year_from=2000      # From year
?year_to=2023        # To year
?search=term         # Search term
```

### Example Requests

**Get all movies**:
```bash
curl -H "Authorization: Bearer {token}" \
  http://localhost:8000/api/v1/movies
```

**Search movies**:
```bash
curl -H "Authorization: Bearer {token}" \
  "http://localhost:8000/api/v1/search/movies?search=Batman&genre=Action"
```

**Create movie**:
```bash
curl -X POST -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"title":"The Dark Knight","year":2008}' \
  http://localhost:8000/api/v1/movies
```

**Batch sync metadata**:
```bash
curl -X POST -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"ids":[1,2,3],"source":"tmdb"}' \
  http://localhost:8000/api/v1/batch/sync
```

## Configuration Quick Reference

### Environment Variables

```bash
# Core
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=your-secret-key

# Database
DATABASE_URL=postgresql://user:pass@host:5432/db

# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# API Keys
OMDB_API_KEY=your-key
TMDB_API_KEY=your-key
TVDB_API_KEY=your-key

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/app.log
```

### Configuration Files

| File | Purpose |
|------|---------|
| `.env` | Environment variables |
| `app/config.py` | Python configuration |
| `docker-compose.yml` | Docker configuration |
| `alembic.ini` | Database migrations |
| `requirements.txt` | Python dependencies |

### Common Configuration Tasks

**Change log level**:
```bash
export LOG_LEVEL=DEBUG
```

**Change database**:
```bash
export DATABASE_URL=postgresql://user:pass@newhost:5432/db
```

**Enable HTTPS**:
```bash
export HTTPS_ENABLED=True
export SSL_CERT_PATH=/path/to/cert.pem
export SSL_KEY_PATH=/path/to/key.pem
```

**Configure rate limiting**:
```bash
export RATE_LIMIT_ENABLED=True
export RATE_LIMIT_REQUESTS=100
```

## Troubleshooting Quick Reference

### Quick Fixes

| Issue | Quick Fix |
|-------|-----------|
| Page won't load | Refresh (F5), clear cache, try different browser |
| Search not working | Clear filters, check spelling, try simpler term |
| Slow performance | Close tabs, clear cache, reduce results |
| Can't log in | Reset password, clear cookies, try different browser |
| Metadata sync fails | Check internet, verify title, try different source |
| Duplicate entries | Delete duplicate or merge entries |
| Missing data | Sync metadata, manually enter, check filters |
| Batch operation fails | Check error message, reduce batch size, retry |

### Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| "Database Connection Error" | DB down | Check DB status, restart DB |
| "Authentication Failed" | Wrong credentials | Reset password, check username |
| "Permission Denied" | No access | Contact admin, request permission |
| "Item Not Found" | Item deleted | Check if exists, restore from backup |
| "Operation Timeout" | Too slow | Reduce batch size, try later |
| "Invalid File Format" | Wrong format | Convert file, try different format |
| "Quota Exceeded" | Limit reached | Delete old items, request increase |

### Common Issues

**Search returns no results**:
- Check spelling
- Remove filters
- Try simpler search
- Verify items exist

**Metadata sync fails**:
- Check internet connection
- Verify API keys
- Try different source
- Manually enter data

**Application is slow**:
- Clear cache
- Close tabs
- Reduce results
- Check connection

**Can't find item**:
- Check filters
- Search for item
- Verify it was saved
- Check if deleted

### Getting Help

- **Documentation**: See User Guide
- **FAQ**: Check FAQ section
- **Support**: Contact support team
- **Logs**: Check browser console (F12)
- **Status**: Check system status page

---

For more information, see:
- [Main User Guide](USER_GUIDE.md)
- [API Reference](API.md)
- [Configuration Guide](CONFIGURATION_GUIDE.md)
- [Troubleshooting Guide](USER_TROUBLESHOOTING.md)
