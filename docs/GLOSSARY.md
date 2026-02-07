# Glossary

This glossary defines terminology used in the Media Library Management System.

## Table of Contents

1. [System Terms](#system-terms)
2. [Feature Terms](#feature-terms)
3. [Technical Terms](#technical-terms)
4. [Abbreviations](#abbreviations)

## System Terms

### Account
A user account that provides access to the Media Library Management System. Each account has a username, password, and associated permissions.

### Administrator
A user with elevated privileges who can manage system configuration, user accounts, and system maintenance.

### API (Application Programming Interface)
A set of protocols and tools that allows external applications to interact with the Media Library Management System programmatically.

### Authentication
The process of verifying a user's identity through login credentials (username and password).

### Authorization
The process of determining what actions a user is allowed to perform based on their role and permissions.

### Backup
A copy of the system data stored separately for recovery purposes in case of data loss or system failure.

### Cache
Temporary storage of frequently accessed data to improve system performance and reduce database load.

### Collection
A custom grouping of movies or TV shows created by users for organization purposes.

### Dashboard
The main landing page that displays an overview of the user's library and recent activity.

### Database
The persistent storage system that stores all application data including movies, TV shows, metadata, and user information.

### Export
The process of downloading library data in a file format (CSV, JSON, Excel) for backup or external use.

### Import
The process of uploading library data from a file to add multiple items to the library at once.

### Library
The complete collection of movies and TV shows stored in the system.

### Metadata
Information about movies and TV shows including title, year, genre, rating, cast, plot, etc.

### Permission
A specific right granted to a user that allows them to perform certain actions (e.g., add movies, delete items).

### Role
A predefined set of permissions assigned to users (e.g., Viewer, Editor, Administrator).

### Session
A period of time during which a user is logged into the system.

### User
A person with an account in the Media Library Management System.

## Feature Terms

### Batch Operation
An operation that performs the same action on multiple items simultaneously (e.g., batch edit, batch delete, batch sync).

### Episode
A single installment of a TV show, typically part of a season.

### Filter
A criterion used to narrow down search results (e.g., genre, rating, year).

### Genre
A category of content (e.g., Action, Comedy, Drama, Horror).

### Metadata Sync
The process of fetching and updating movie or TV show information from external metadata sources.

### Movie
A single film entry in the library with associated metadata.

### Note
A personal comment or review added by a user to a movie or TV show.

### Pagination
The division of search results into pages to improve performance and usability.

### Rating
A numerical score (typically 1-10) assigned to a movie or TV show by users or external sources.

### Search
The process of finding movies or TV shows using keywords or filters.

### Season
A collection of episodes of a TV show, typically released in a single year.

### Sorting
The arrangement of search results in a specific order (e.g., alphabetical, by rating, by year).

### Status
The current state of an item (e.g., Watched, Unwatched, In Progress for movies; Ongoing, Completed, Cancelled for TV shows).

### Tag
A label or keyword assigned to an item for custom organization and filtering.

### TV Show
A series of episodes organized by seasons, with associated metadata.

### Watched Status
An indicator showing whether a user has watched a movie or TV show episode.

## Technical Terms

### API Key
A unique identifier used to authenticate API requests from external applications.

### Broker
A message queue system (Redis) that manages background job distribution in Celery.

### Celery
A distributed task queue system used for running background jobs asynchronously.

### CORS (Cross-Origin Resource Sharing)
A security mechanism that controls which external websites can access the API.

### Database Connection Pool
A set of pre-established database connections that are reused to improve performance.

### Encryption
The process of converting data into a coded format to protect it from unauthorized access.

### HTTP/HTTPS
The protocol used for communication between the web browser and the server. HTTPS is the secure version using encryption.

### JSON (JavaScript Object Notation)
A lightweight data format used for data exchange between the application and external systems.

### JWT (JSON Web Token)
A token-based authentication method used for API requests.

### Logging
The process of recording system events and errors for debugging and monitoring purposes.

### Middleware
Software components that process requests and responses between the client and server.

### ORM (Object-Relational Mapping)
A programming technique that maps database tables to Python objects for easier data manipulation.

### PostgreSQL
The relational database system used to store application data.

### Query
A request for data from the database using SQL or ORM methods.

### Redis
An in-memory data store used for caching and as a message broker for Celery.

### REST API (Representational State Transfer)
An architectural style for building APIs using standard HTTP methods (GET, POST, PUT, DELETE).

### Schema
The structure and organization of data in the database, defining tables, columns, and relationships.

### SSL/TLS (Secure Sockets Layer/Transport Layer Security)
Encryption protocols used to secure communication between the client and server.

### Token
A unique identifier used for authentication, typically a JWT token for API requests.

### Webhook
A mechanism for sending real-time notifications to external systems when certain events occur.

## Abbreviations

### API
Application Programming Interface

### CSV
Comma-Separated Values (file format)

### DB
Database

### HTTPS
HyperText Transfer Protocol Secure

### JSON
JavaScript Object Notation

### JWT
JSON Web Token

### OMDB
Open Movie Database

### ORM
Object-Relational Mapping

### REST
Representational State Transfer

### SQL
Structured Query Language

### SSL
Secure Sockets Layer

### TMDB
The Movie Database

### TVDB
The TV Database

### TTL
Time-To-Live (cache expiration)

### UI
User Interface

### URL
Uniform Resource Locator

### UUID
Universally Unique Identifier

### XML
Extensible Markup Language

---

For more information, see:
- [Main User Guide](USER_GUIDE.md)
- [API Reference](API.md)
- [Administrator Guide](ADMIN_GUIDE.md)
