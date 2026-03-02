# Architecture Diagrams

## ASCII (Human Readable)

```
 USER BROWSER
      │
      │ HTTP :80
      ▼
 ┌─────────────────────────────────────────────────────────────┐
 │  PUBLIC NETWORK                                             │
 │                                                             │
 │  ┌──────────────────┐                                       │
 │  │    Frontend      │  React SPA served by nginx            │
 │  │  (nginx :8080)   │  Proxies /api/* to App internally     │
 │  └────────┬─────────┘                                       │
 └───────────┼─────────────────────────────────────────────────┘
             │ /api/* proxy
 ┌───────────┼─────────────────────────────────────────────────┐
 │  INTERNAL NETWORK                                           │
 │           │                                                  │
 │           ▼                                                  │
 │  ┌──────────────────┐   SQLAlchemy   ┌──────────────────┐   │
 │  │      App         │ ─────────────► │    PostgreSQL     │   │
 │  │   (FastAPI)      │                │   (persistent     │   │
 │  │                  │ ◄───────────── │    volume)        │   │
 │  └────────┬─────────┘                └──────────────────┘   │
 │           │                                                  │
 │           │ cache / pub                                      │
 │           ▼                                                  │
 │  ┌──────────────────┐                                        │
 │  │      Redis       │  Broker (DB 0) + Result Backend (DB 1) │
 │  │                  │  + App cache (DB 2)                    │
 │  └──────┬───────────┘                                        │
 │         │              │                                      │
 │    tasks│         beat │ schedule                            │
 │         ▼              ▼                                      │
 │  ┌──────────────┐  ┌──────────────┐                          │
 │  │Celery Worker │  │ Celery Beat  │                          │
 │  │              │  │ (Scheduler)  │                          │
 │  │ - TMDB fetch │  │ - Media scan │                          │
 │  │ - Enrichment │  │   (cron)     │                          │
 │  │ - Batch ops  │  └──────────────┘                          │
 │  └──────┬───────┘                                            │
 │         │                                                    │
 │         │ writes results                                     │
 │         ▼                                                    │
 │  ┌──────────────────┐                                        │
 │  │    PostgreSQL    │  (same DB as App)                      │
 │  └──────────────────┘                                        │
 │                                                              │
 │  Host volumes (read-only)                                    │
 │  /path/to/movies ──► /media/movies  (App + Worker)          │
 │  /path/to/tv     ──► /media/tv      (App + Worker)          │
 │                                                              │
 └──────────────────────────────────────────────────────────────┘
             │
             │ HTTPS (enrichment)
             ▼
    ┌─────────────────┐
    │    TMDB API     │
    │   (external)    │
    └─────────────────┘
```

### Data Flow

```
  New media file appears on disk
          │
          ▼
  App startup scan  ──OR──  Celery Beat (cron)
          │
          ▼
  FileService scans /media/movies + /media/tv
          │
          ▼
  Movie / TVShow record created  (status: local_only)
          │
          ▼
  Enrichment task dispatched → Redis queue
          │
          ▼
  Celery Worker picks up task
          │
          ├──► TMDB API (fetch metadata)
          │
          ▼
  Movie / TVShow record updated  (status: fully_enriched)
          │
          ▼
  Frontend reflects updated metadata
```

---

## Mermaid

```mermaid
graph TB
    Browser([User Browser])

    subgraph public["Public Network"]
        Frontend["Frontend\nnginx :8080\n(React SPA)"]
    end

    subgraph internal["Internal Network"]
        App["App\nFastAPI :8000"]
        Redis[("Redis\nBroker · Cache · Results")]
        Postgres[("PostgreSQL\nPersistent Volume")]
        Worker["Celery Worker\nEnrichment · Batch ops"]
        Beat["Celery Beat\nScheduler (cron)"]
    end

    subgraph host["Host Machine"]
        Movies["/path/to/movies"]
        TV["/path/to/tv"]
    end

    TMDB(["TMDB API\n(external)"])

    Browser -->|":80"| Frontend
    Frontend -->|"/api/* proxy"| App

    App -->|"SQLAlchemy"| Postgres
    App -->|"cache / publish tasks"| Redis

    Redis -->|"task queue"| Worker
    Beat -->|"cron schedule"| Redis

    Worker -->|"write results"| Postgres
    Worker -->|"HTTPS"| TMDB
    App -->|"HTTPS"| TMDB

    Movies -->|"volume :ro"| App
    Movies -->|"volume :ro"| Worker
    TV -->|"volume :ro"| App
    TV -->|"volume :ro"| Worker
```
