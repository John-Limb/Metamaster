# API Client Examples

## Overview

This document provides comprehensive examples for consuming the Media Management API using various programming languages and tools. All examples demonstrate common workflows and best practices.

---

## Table of Contents

1. [Python Examples](#python-examples)
2. [JavaScript/Node.js Examples](#javascriptnodejs-examples)
3. [cURL Examples](#curl-examples)
4. [Postman Collection](#postman-collection)
5. [Common Workflows](#common-workflows)

---

## Python Examples

### Installation

```bash
pip install requests
```

### Basic Setup

```python
import requests
import json
from typing import Dict, List, Optional

class MediaAPIClient:
    """Client for Media Management API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make HTTP request to API"""
        url = f"{self.base_url}{endpoint}"
        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()
```

### List Movies

```python
def list_movies(self, genre: Optional[str] = None, 
                min_rating: Optional[float] = None,
                limit: int = 10, offset: int = 0) -> Dict:
    """List movies with optional filtering"""
    params = {
        "limit": limit,
        "offset": offset
    }
    if genre:
        params["genre"] = genre
    if min_rating is not None:
        params["min_rating"] = min_rating
    
    return self._make_request("GET", "/movies", params=params)

# Usage
client = MediaAPIClient()
movies = client.list_movies(genre="action", min_rating=7.0, limit=20)
print(f"Found {movies['total']} movies")
for movie in movies['items']:
    print(f"- {movie['title']} ({movie['year']}) - Rating: {movie['rating']}")
```

### Search Movies

```python
def search_movies(self, query: str, limit: int = 10, 
                  offset: int = 0) -> Dict:
    """Search movies by title"""
    params = {
        "q": query,
        "limit": limit,
        "offset": offset
    }
    return self._make_request("GET", "/movies/search", params=params)

# Usage
results = client.search_movies("inception", limit=5)
for movie in results['items']:
    print(f"{movie['title']} - {movie['plot'][:100]}...")
```

### Get Movie Details

```python
def get_movie(self, movie_id: int) -> Dict:
    """Get movie details"""
    return self._make_request("GET", f"/movies/{movie_id}")

# Usage
movie = client.get_movie(1)
print(f"Title: {movie['title']}")
print(f"Rating: {movie['rating']}")
print(f"Genres: {', '.join(movie['genres'])}")
print(f"Plot: {movie['plot']}")
```

### Create Movie

```python
def create_movie(self, title: str, plot: str = None, 
                 year: int = None, rating: float = None,
                 genres: List[str] = None, runtime: int = None,
                 omdb_id: str = None) -> Dict:
    """Create a new movie"""
    data = {
        "title": title,
        "plot": plot,
        "year": year,
        "rating": rating,
        "genres": genres or [],
        "runtime": runtime,
        "omdb_id": omdb_id
    }
    return self._make_request("POST", "/movies", json=data)

# Usage
new_movie = client.create_movie(
    title="New Movie",
    plot="An exciting new film",
    year=2026,
    rating=8.0,
    genres=["action", "drama"],
    runtime=130
)
print(f"Created movie with ID: {new_movie['id']}")
```

### Update Movie

```python
def update_movie(self, movie_id: int, **kwargs) -> Dict:
    """Update movie details"""
    return self._make_request("PUT", f"/movies/{movie_id}", json=kwargs)

# Usage
updated = client.update_movie(1, rating=8.5, genres=["action", "thriller"])
print(f"Updated movie: {updated['title']}")
```

### Delete Movie

```python
def delete_movie(self, movie_id: int) -> None:
    """Delete a movie"""
    self._make_request("DELETE", f"/movies/{movie_id}")

# Usage
client.delete_movie(1)
print("Movie deleted")
```

### Sync Movie Metadata

```python
def sync_movie_metadata(self, movie_id: int) -> Dict:
    """Sync movie metadata from OMDB"""
    return self._make_request("POST", f"/movies/{movie_id}/sync-metadata")

# Usage
result = client.sync_movie_metadata(1)
print(f"Sync successful: {result['success']}")
print(f"Updated fields: {', '.join(result['updated_fields'])}")
```

### List TV Shows

```python
def list_tv_shows(self, genre: Optional[str] = None,
                  min_rating: Optional[float] = None,
                  limit: int = 10, offset: int = 0) -> Dict:
    """List TV shows with optional filtering"""
    params = {
        "limit": limit,
        "offset": offset
    }
    if genre:
        params["genre"] = genre
    if min_rating is not None:
        params["min_rating"] = min_rating
    
    return self._make_request("GET", "/tv-shows", params=params)

# Usage
shows = client.list_tv_shows(genre="drama", limit=10)
for show in shows['items']:
    print(f"- {show['title']} - {show['season_count']} seasons")
```

### Get Task Status

```python
def get_task_status(self, task_id: str) -> Dict:
    """Get task status"""
    return self._make_request("GET", f"/api/tasks/{task_id}")

# Usage
task = client.get_task_status("550e8400-e29b-41d4-a716-446655440000")
print(f"Task status: {task['status']}")
if task['status'] == 'success':
    print(f"Result: {task['result']}")
elif task['status'] == 'failure':
    print(f"Error: {task['error']}")
```

### Start Batch Metadata Sync

```python
def start_metadata_sync_batch(self, media_ids: List[int], 
                              media_type: str = "movie") -> Dict:
    """Start bulk metadata sync"""
    data = {
        "operation_type": "metadata_sync",
        "media_ids": media_ids,
        "media_type": media_type
    }
    return self._make_request("POST", "/api/tasks/batch/metadata-sync", json=data)

# Usage
batch = client.start_metadata_sync_batch([1, 2, 3, 4, 5], media_type="movie")
print(f"Batch ID: {batch['id']}")
print(f"Processing {batch['total_items']} items")
```

### Get Cache Statistics

```python
def get_cache_stats(self) -> Dict:
    """Get cache statistics"""
    return self._make_request("GET", "/cache/stats")

# Usage
stats = client.get_cache_stats()
print(f"Total cache entries: {stats['total_entries']}")
print(f"Cache size: {stats['total_size_mb']} MB")
```

### Error Handling

```python
def safe_get_movie(self, movie_id: int) -> Optional[Dict]:
    """Get movie with error handling"""
    try:
        return self.get_movie(movie_id)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"Movie {movie_id} not found")
        elif e.response.status_code == 500:
            print("Server error, please try again later")
        else:
            print(f"Error: {e.response.status_code}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Connection error: {e}")
        return None

# Usage
movie = client.safe_get_movie(1)
if movie:
    print(f"Found: {movie['title']}")
```

---

## JavaScript/Node.js Examples

### Installation

```bash
npm install axios
# or
npm install node-fetch
```

### Using Axios

```javascript
const axios = require('axios');

class MediaAPIClient {
  constructor(baseURL = 'http://localhost:8000') {
    this.client = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      }
    });
  }

  async listMovies(options = {}) {
    const { genre, minRating, limit = 10, offset = 0 } = options;
    const params = { limit, offset };
    if (genre) params.genre = genre;
    if (minRating !== undefined) params.min_rating = minRating;
    
    const response = await this.client.get('/movies', { params });
    return response.data;
  }

  async searchMovies(query, limit = 10, offset = 0) {
    const response = await this.client.get('/movies/search', {
      params: { q: query, limit, offset }
    });
    return response.data;
  }

  async getMovie(movieId) {
    const response = await this.client.get(`/movies/${movieId}`);
    return response.data;
  }

  async createMovie(movieData) {
    const response = await this.client.post('/movies', movieData);
    return response.data;
  }

  async updateMovie(movieId, updates) {
    const response = await this.client.put(`/movies/${movieId}`, updates);
    return response.data;
  }

  async deleteMovie(movieId) {
    await this.client.delete(`/movies/${movieId}`);
  }

  async syncMovieMetadata(movieId) {
    const response = await this.client.post(`/movies/${movieId}/sync-metadata`);
    return response.data;
  }

  async getTaskStatus(taskId) {
    const response = await this.client.get(`/api/tasks/${taskId}`);
    return response.data;
  }

  async startMetadataSyncBatch(mediaIds, mediaType = 'movie') {
    const response = await this.client.post('/api/tasks/batch/metadata-sync', {
      operation_type: 'metadata_sync',
      media_ids: mediaIds,
      media_type: mediaType
    });
    return response.data;
  }

  async getCacheStats() {
    const response = await this.client.get('/cache/stats');
    return response.data;
  }
}

// Usage
const client = new MediaAPIClient();

// List movies
client.listMovies({ genre: 'action', minRating: 7.0, limit: 20 })
  .then(data => {
    console.log(`Found ${data.total} movies`);
    data.items.forEach(movie => {
      console.log(`- ${movie.title} (${movie.year}) - Rating: ${movie.rating}`);
    });
  })
  .catch(error => console.error('Error:', error.message));

// Search movies
client.searchMovies('inception', 5)
  .then(data => {
    data.items.forEach(movie => {
      console.log(`${movie.title} - ${movie.plot.substring(0, 100)}...`);
    });
  })
  .catch(error => console.error('Error:', error.message));

// Get movie details
client.getMovie(1)
  .then(movie => {
    console.log(`Title: ${movie.title}`);
    console.log(`Rating: ${movie.rating}`);
    console.log(`Genres: ${movie.genres.join(', ')}`);
  })
  .catch(error => console.error('Error:', error.message));

// Create movie
client.createMovie({
  title: 'New Movie',
  plot: 'An exciting new film',
  year: 2026,
  rating: 8.0,
  genres: ['action', 'drama'],
  runtime: 130
})
  .then(movie => console.log(`Created movie with ID: ${movie.id}`))
  .catch(error => console.error('Error:', error.message));
```

### Using Fetch API

```javascript
class MediaAPIClient {
  constructor(baseURL = 'http://localhost:8000') {
    this.baseURL = baseURL;
  }

  async request(method, endpoint, data = null) {
    const url = `${this.baseURL}${endpoint}`;
    const options = {
      method,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      }
    };

    if (data) {
      options.body = JSON.stringify(data);
    }

    const response = await fetch(url, options);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return response.json();
  }

  async listMovies(options = {}) {
    const { genre, minRating, limit = 10, offset = 0 } = options;
    const params = new URLSearchParams({ limit, offset });
    if (genre) params.append('genre', genre);
    if (minRating !== undefined) params.append('min_rating', minRating);
    
    return this.request('GET', `/movies?${params}`);
  }

  async getMovie(movieId) {
    return this.request('GET', `/movies/${movieId}`);
  }

  async createMovie(movieData) {
    return this.request('POST', '/movies', movieData);
  }

  async updateMovie(movieId, updates) {
    return this.request('PUT', `/movies/${movieId}`, updates);
  }

  async deleteMovie(movieId) {
    return this.request('DELETE', `/movies/${movieId}`);
  }
}

// Usage
const client = new MediaAPIClient();

client.listMovies({ genre: 'action', limit: 10 })
  .then(data => console.log(`Found ${data.total} movies`))
  .catch(error => console.error('Error:', error.message));
```

---

## cURL Examples

### List Movies

```bash
# Basic list
curl -X GET "http://localhost:8000/movies"

# With filters
curl -X GET "http://localhost:8000/movies?genre=action&min_rating=7.0&limit=20&skip=0"

# Pretty print JSON
curl -X GET "http://localhost:8000/movies" | jq '.'
```

### Search Movies

```bash
curl -X GET "http://localhost:8000/movies/search?q=inception&limit=10"
```

### Get Movie Details

```bash
curl -X GET "http://localhost:8000/movies/1"
```

### Create Movie

```bash
curl -X POST "http://localhost:8000/movies" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "New Movie",
    "plot": "An exciting new film",
    "year": 2026,
    "rating": 8.0,
    "genres": ["action", "drama"],
    "runtime": 130,
    "omdb_id": "tt9876543"
  }'
```

### Update Movie

```bash
curl -X PUT "http://localhost:8000/movies/1" \
  -H "Content-Type: application/json" \
  -d '{
    "rating": 8.5,
    "genres": ["action", "thriller"]
  }'
```

### Delete Movie

```bash
curl -X DELETE "http://localhost:8000/movies/1"
```

### Sync Movie Metadata

```bash
curl -X POST "http://localhost:8000/movies/1/sync-metadata"
```

### List TV Shows

```bash
curl -X GET "http://localhost:8000/tv-shows?genre=drama&limit=10"
```

### Get Task Status

```bash
curl -X GET "http://localhost:8000/api/tasks/550e8400-e29b-41d4-a716-446655440000"
```

### Start Batch Metadata Sync

```bash
curl -X POST "http://localhost:8000/api/tasks/batch/metadata-sync" \
  -H "Content-Type: application/json" \
  -d '{
    "operation_type": "metadata_sync",
    "media_ids": [1, 2, 3, 4, 5],
    "media_type": "movie"
  }'
```

### Get Cache Statistics

```bash
curl -X GET "http://localhost:8000/cache/stats"
```

### Health Check

```bash
curl -X GET "http://localhost:8000/health"
curl -X GET "http://localhost:8000/health/db"
```

---

## Postman Collection

### Import Collection

1. Open Postman
2. Click "Import"
3. Select "Link" tab
4. Paste the collection URL or import the JSON file

### Collection Structure

```
Media Management API
├── Movies
│   ├── List Movies
│   ├── Search Movies
│   ├── Get Movie
│   ├── Create Movie
│   ├── Update Movie
│   ├── Delete Movie
│   └── Sync Metadata
├── TV Shows
│   ├── List TV Shows
│   ├── Get TV Show
│   ├── Get Seasons
│   ├── Get Episodes
│   ├── Create TV Show
│   ├── Update TV Show
│   ├── Delete TV Show
│   └── Sync Metadata
├── Tasks
│   ├── Get Task Status
│   ├── List Tasks
│   ├── Retry Task
│   ├── Cancel Task
│   ├── List Errors
│   └── Get Error Details
├── Batch Operations
│   ├── Start Metadata Sync
│   ├── Start File Import
│   ├── Get Batch Status
│   ├── Get Batch Progress
│   └── Cancel Batch
├── Cache
│   ├── Get Cache Stats
│   ├── List Cache by Type
│   ├── Invalidate Cache
│   ├── Get Redis Stats
│   └── Clear Redis Cache
└── Health
    ├── Basic Health Check
    └── Database Health Check
```

---

## Common Workflows

### Workflow 1: Create and Sync Movie

```python
# Python
client = MediaAPIClient()

# Create movie
movie = client.create_movie(
    title="Inception",
    year=2010,
    omdb_id="tt1375666"
)
print(f"Created movie: {movie['id']}")

# Sync metadata
result = client.sync_movie_metadata(movie['id'])
print(f"Synced fields: {result['updated_fields']}")

# Get updated movie
updated = client.get_movie(movie['id'])
print(f"Updated rating: {updated['rating']}")
```

### Workflow 2: Batch Sync with Progress Monitoring

```python
import time

# Start batch
batch = client.start_metadata_sync_batch([1, 2, 3, 4, 5])
batch_id = batch['id']
print(f"Started batch {batch_id}")

# Monitor progress
while True:
    status = client.get_batch_status(batch_id)
    progress = (status['processed_items'] / status['total_items']) * 100
    print(f"Progress: {progress:.1f}% ({status['processed_items']}/{status['total_items']})")
    
    if status['status'] in ['completed', 'failed']:
        break
    
    time.sleep(2)

print(f"Batch completed with status: {status['status']}")
```

### Workflow 3: Search and Filter

```javascript
// JavaScript
const client = new MediaAPIClient();

// Search for movies
const results = await client.searchMovies('action', 50);

// Filter by rating
const highRated = results.items.filter(m => m.rating >= 8.0);

// Sort by rating
highRated.sort((a, b) => b.rating - a.rating);

// Display top 10
console.log('Top 10 Action Movies:');
highRated.slice(0, 10).forEach((movie, index) => {
  console.log(`${index + 1}. ${movie.title} - ${movie.rating}`);
});
```

---

## Error Handling Best Practices

### Python

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session_with_retries():
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

client = MediaAPIClient()
client.session = create_session_with_retries()
```

### JavaScript

```javascript
async function retryRequest(fn, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
    }
  }
}

// Usage
const movies = await retryRequest(() => client.listMovies());
```

---

## Related Documentation

- [API Reference](./API_REFERENCE.md)
- [Error Reference](./API_ERRORS.md)
- [Authentication Guide](./API_AUTHENTICATION.md)
