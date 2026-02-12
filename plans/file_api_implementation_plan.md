# File API Implementation Plan

## Problem Summary

The frontend cannot display files because the backend is missing the `/api/v1/files` API endpoints. The frontend calls these endpoints but they return 404 errors.

## Root Cause

- **Missing**: `app/api/v1/files/` directory with endpoints
- **Missing**: Files router registration in `app/main.py`
- **Exists**: File system monitoring infrastructure in `app/infrastructure/file_system/`
- **Exists**: File-related models (`FileQueue`, `MovieFile`, `EpisodeFile`)

## Implementation Architecture

```mermaid
graph TB
    subgraph Frontend
        FE[FileExplorer] --> FS[fileService]
        FS --> API[/api/v1/files]
    end
    
    subgraph Backend API
        API --> FR[Files Router]
        FR --> FSVC[File Service]
        FSVC --> FMS[FileMonitorService]
        FSVC --> DB[(Database)]
    end
    
    subgraph Infrastructure
        FMS --> W[Watchdog Observer]
        W --> MP[Media Paths]
    end
```

## Implementation Steps

### Step 1: Create Domain Layer

**File**: `app/domain/files/__init__.py`
```python
# Empty init file for files domain module
```

**File**: `app/domain/files/models.py`
```python
# TODO: Define FileItem model with:
# - id: str
# - name: str  
# - path: str
# - type: file or directory
# - size: int
# - mime_type: Optional[str]
# - created_at: datetime
# - updated_at: datetime
# - is_indexed: bool
# - metadata: Optional[dict]
```

**File**: `app/domain/files/schemas.py`
```python
# TODO: Define Pydantic schemas matching frontend FileItem type
# - FileItemResponse
# - FileListResponse (Paginated)
# - FileStatsResponse
# - FileCreateRequest
# - FileUpdateRequest
# - FileDeleteRequest
```

**File**: `app/domain/files/service.py`
```python
# TODO: Define file service interface
# - get_files(path, page, page_size)
# - get_file_by_id(id)
# - get_file_stats()
# - delete_file(id)
# - move_file(id, new_path)
# - rename_file(id, new_name)
# - search_files(query)
```

---

### Step 2: Create Infrastructure Layer

**File**: `app/infrastructure/file_system/file_service.py`
```python
# TODO: Implement FileService using:
# - os.listdir() for directory listing
# - os.path.getsize() for file sizes
# - FileMonitorService for file discovery
# - Database for indexed files
```

---

### Step 3: Create API Layer

**File**: `app/api/v1/files/__init__.py`
```python
# Init file for files API module
```

**File**: `app/api/v1/files/endpoints.py`
```python
# TODO: Implement FastAPI endpoints:
# - GET /files - List files in directory
# - GET /files/{id} - Get file details
# - GET /files/stats - Get file statistics
# - DELETE /files/{id} - Delete file
# - PATCH /files/{id} - Move/Rename file
# - POST /files/upload - Upload file
# - POST /files/batch-delete - Batch delete
# - POST /files/batch-move - Batch move
# - GET /files/search - Search files
```

---

### Step 4: Register Router

**File**: `app/main.py` (line ~150)
```python
# Add: from app.api.v1.files import router as files_router
# Add: app.include_router(files_router, prefix="/api/v1")
```

---

### Step 5: Create Type Mappings (Optional)

**File**: `app/api/v1/files/utils.py`
```python
# TODO: Create mapping between domain FileItem and frontend FileItem
# Ensure response format matches frontend expectations
```

## API Endpoint Specifications

### GET /api/v1/files

**Query Parameters**:
- `path` (string, default: "/") - Directory path to list
- `page` (int, default: 1) - Page number
- `pageSize` (int, default: 20) - Items per page

**Response**:
```json
{
  "items": [
    {
      "id": "string",
      "name": "string",
      "path": "string",
      "type": "file | directory",
      "size": 0,
      "mimeType": "string",
      "createdAt": "ISO8601",
      "updatedAt": "ISO8601",
      "isIndexed": false
    }
  ],
  "total": 100,
  "page": 1,
  "pageSize": 20,
  "totalPages": 5
}
```

### GET /api/v1/files/stats

**Response**:
```json
{
  "totalFiles": 100,
  "totalSize": 1073741824,
  "filesByType": {
    "video": 50,
    "audio": 30,
    "subtitle": 20
  },
  "lastUpdated": "ISO8601"
}
```

## Implementation Checklist

- [ ] Create `app/domain/files/__init__.py`
- [ ] Create `app/domain/files/models.py`
- [ ] Create `app/domain/files/schemas.py`
- [ ] Create `app/domain/files/service.py`
- [ ] Create `app/infrastructure/file_system/file_service.py`
- [ ] Create `app/api/v1/files/__init__.py`
- [ ] Create `app/api/v1/files/endpoints.py`
- [ ] Create `app/api/v1/files/utils.py`
- [ ] Register files router in `app/main.py`
- [ ] Test endpoints with frontend

## Dependencies

- Already exists: `FileMonitorService` in `app/infrastructure/file_system/monitor.py`
- Already exists: `MovieFile`, `EpisodeFile` models
- Already exists: `FileQueue` model
- Needed: New `File` domain model

## Files to Create

1. `app/domain/files/__init__.py`
2. `app/domain/files/models.py`
3. `app/domain/files/schemas.py`
4. `app/domain/files/service.py`
5. `app/infrastructure/file_system/file_service.py`
6. `app/api/v1/files/__init__.py`
7. `app/api/v1/files/endpoints.py`
8. `app/api/v1/files/utils.py`

## Files to Modify

1. `app/main.py` - Add files router registration
