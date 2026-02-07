# Movie Management User Guide

This guide provides comprehensive instructions for managing your movie collection in the Media Library Management System.

## Table of Contents

1. [Adding Movies](#adding-movies)
2. [Searching and Filtering Movies](#searching-and-filtering-movies)
3. [Viewing Movie Details](#viewing-movie-details)
4. [Organizing Movies](#organizing-movies)
5. [Syncing Movie Metadata](#syncing-movie-metadata)
6. [Bulk Operations on Movies](#bulk-operations-on-movies)
7. [Best Practices](#best-practices)

## Adding Movies

### Adding a Single Movie

#### Method 1: Manual Entry

1. Navigate to the **Movies** section from the main menu
2. Click the **"Add Movie"** button in the top-right corner
3. Fill in the movie details:
   - **Title** (required): Enter the exact movie title
   - **Year** (optional): Enter the release year
   - **Genre** (optional): Select one or more genres
   - **Rating** (optional): Set the movie rating (1-10 or similar scale)
   - **Director** (optional): Enter the director's name
   - **Cast** (optional): Add main cast members
   - **Plot** (optional): Enter a brief plot summary
   - **Runtime** (optional): Enter the movie duration in minutes
   - **Language** (optional): Select the primary language
   - **Poster URL** (optional): Provide a link to the movie poster
4. Click **"Save"** to add the movie to your library

#### Method 2: Search and Fetch Metadata

1. Navigate to the **Movies** section
2. Click the **"Add Movie"** button
3. Enter the movie title in the search field
4. Click **"Search Metadata"** to fetch information from external sources
5. Review the search results:
   - Select the correct movie from the results
   - Verify the information is accurate
   - Check the poster and other details
6. Click **"Confirm"** to populate the form with fetched data
7. Make any necessary adjustments to the information
8. Click **"Save"** to add the movie

### Adding Multiple Movies

#### Bulk Import

1. Navigate to the **Movies** section
2. Click the **"Bulk Import"** button
3. Choose your import method:
   - **CSV File**: Upload a CSV file with movie data
   - **JSON File**: Upload a JSON file with movie data
   - **Paste Data**: Paste movie data directly
4. Map the columns to the correct fields:
   - Title → Movie Title
   - Year → Release Year
   - Genre → Genre(s)
   - Rating → Rating
   - Director → Director
5. Click **"Preview"** to verify the data
6. Click **"Import"** to add all movies to your library
7. Monitor the import progress in the status panel

#### CSV Format Example

```
Title,Year,Genre,Rating,Director,Runtime
The Shawshank Redemption,1994,Drama,9.3,Frank Darabont,142
The Godfather,1972,Crime|Drama,9.2,Francis Ford Coppola,175
The Dark Knight,2008,Action|Crime|Drama,9.0,Christopher Nolan,152
```

#### JSON Format Example

```json
[
  {
    "title": "The Shawshank Redemption",
    "year": 1994,
    "genre": ["Drama"],
    "rating": 9.3,
    "director": "Frank Darabont",
    "runtime": 142
  },
  {
    "title": "The Godfather",
    "year": 1972,
    "genre": ["Crime", "Drama"],
    "rating": 9.2,
    "director": "Francis Ford Coppola",
    "runtime": 175
  }
]
```

## Searching and Filtering Movies

### Basic Search

1. Navigate to the **Movies** section
2. Use the search box at the top of the movie list
3. Type the movie title or keywords
4. Press **Enter** or click the **Search** button
5. Results will display matching movies

### Advanced Filtering

1. Click the **"Filters"** button to expand filter options
2. Apply one or more filters:
   - **Genre**: Select one or more genres
   - **Rating**: Set minimum and maximum rating
   - **Year**: Set year range (from/to)
   - **Director**: Filter by director name
   - **Language**: Select language(s)
   - **Status**: Filter by watched/unwatched status
3. Click **"Apply Filters"** to update results
4. Click **"Clear Filters"** to reset all filters

### Sorting Options

1. Click the **"Sort By"** dropdown menu
2. Choose a sorting option:
   - **Title (A-Z)**: Alphabetical order
   - **Title (Z-A)**: Reverse alphabetical order
   - **Year (Newest)**: Most recent first
   - **Year (Oldest)**: Oldest first
   - **Rating (Highest)**: Highest rated first
   - **Rating (Lowest)**: Lowest rated first
   - **Date Added**: Most recently added first
   - **Date Watched**: Most recently watched first
3. Results will be sorted according to your selection

### Pagination

1. At the bottom of the movie list, you'll see pagination controls
2. Choose how many items to display per page:
   - 10 items per page
   - 25 items per page
   - 50 items per page
   - 100 items per page
3. Navigate between pages using:
   - **Previous** button: Go to previous page
   - **Next** button: Go to next page
   - **Page numbers**: Click to jump to specific page
   - **Go to page**: Enter page number and press Enter

### Saved Searches

1. Set up your desired search and filters
2. Click the **"Save Search"** button
3. Enter a name for your saved search (e.g., "Top Rated Dramas")
4. Click **"Save"**
5. To use a saved search:
   - Click the **"Saved Searches"** dropdown
   - Select your saved search
   - Results will load automatically

## Viewing Movie Details

### Movie Details Page

1. Click on any movie in the list to open its details page
2. The details page displays:
   - **Poster**: Movie poster image
   - **Title**: Movie title and year
   - **Rating**: User rating and external ratings
   - **Genre**: Movie genres
   - **Director**: Director information
   - **Cast**: Main cast members
   - **Plot**: Full plot summary
   - **Runtime**: Movie duration
   - **Language**: Primary language
   - **Release Date**: Official release date
   - **Production Company**: Studio/production company
   - **Budget**: Production budget (if available)
   - **Box Office**: Box office earnings (if available)

### Editing Movie Details

1. On the movie details page, click the **"Edit"** button
2. Modify any of the following fields:
   - Title
   - Year
   - Genre
   - Rating
   - Director
   - Cast
   - Plot
   - Runtime
   - Language
   - Poster URL
   - Custom fields
3. Click **"Save"** to update the movie
4. Click **"Cancel"** to discard changes

### Marking Movies as Watched

1. On the movie details page, click the **"Mark as Watched"** button
2. (Optional) Set the watch date:
   - Click the date field
   - Select the date you watched the movie
   - Click **"Confirm"**
3. (Optional) Add a rating:
   - Click the rating field
   - Select your rating (1-10 or similar)
   - Click **"Save"**
4. The movie will be marked as watched in your library

### Adding Notes and Reviews

1. On the movie details page, scroll to the **"Notes"** section
2. Click **"Add Note"** to create a new note
3. Enter your note or review
4. (Optional) Set a note type:
   - Personal Review
   - Recommendation
   - Reminder
   - Other
5. Click **"Save Note"**
6. To edit a note, click the **"Edit"** button next to it
7. To delete a note, click the **"Delete"** button

## Organizing Movies

### By Genre

1. Navigate to the **Movies** section
2. Click the **"Genre"** filter
3. Select one or more genres:
   - Action
   - Comedy
   - Drama
   - Horror
   - Romance
   - Sci-Fi
   - Thriller
   - And more...
4. Results will show only movies in selected genres
5. Click **"Save as Search"** to save this genre filter

### By Rating

1. Use the **Rating** filter to organize by quality:
   - **Highly Rated**: 8.0 and above
   - **Well Rated**: 7.0 - 7.9
   - **Good**: 6.0 - 6.9
   - **Average**: 5.0 - 5.9
   - **Below Average**: Below 5.0
2. Set the minimum and maximum rating
3. Click **"Apply"** to filter results

### By Year

1. Use the **Year** filter to organize by release date:
   - Set the "From" year (earliest)
   - Set the "To" year (latest)
   - Click **"Apply"**
2. Results will show movies released in the selected year range

### By Status

1. Use the **Status** filter to organize by viewing status:
   - **Watched**: Movies you've already watched
   - **Unwatched**: Movies you haven't watched yet
   - **In Progress**: Movies you're currently watching
2. Select the status(es) you want to view
3. Click **"Apply"**

### Creating Custom Collections

1. Navigate to the **Movies** section
2. Click the **"Collections"** menu
3. Click **"Create Collection"**
4. Enter a collection name (e.g., "Oscar Winners", "Favorites")
5. (Optional) Add a description
6. Click **"Create"**
7. To add movies to a collection:
   - Select movies using checkboxes
   - Click **"Add to Collection"**
   - Choose the collection
   - Click **"Confirm"**

## Syncing Movie Metadata

### Manual Metadata Sync

1. Navigate to the **Movies** section
2. Select one or more movies using checkboxes
3. Click the **"Sync Metadata"** button
4. Choose the metadata source:
   - **OMDB**: Open Movie Database
   - **TMDB**: The Movie Database
   - **Both**: Fetch from both sources and merge
5. Click **"Start Sync"**
6. Monitor the progress in the status panel
7. Review the updated information
8. Click **"Confirm"** to save changes

### Automatic Metadata Sync

1. Navigate to **Settings** → **Preferences**
2. Enable **"Automatic Metadata Sync"**
3. Set the sync frequency:
   - Daily
   - Weekly
   - Monthly
4. Choose the time for automatic syncs
5. Click **"Save"**

### Handling Metadata Conflicts

When syncing metadata, you may encounter conflicts between existing and new data:

1. Review the conflicting fields
2. Choose which version to keep:
   - **Keep Existing**: Keep your current data
   - **Use New**: Replace with fetched data
   - **Merge**: Combine both versions
3. Click **"Resolve"** to apply your choice
4. Continue with remaining conflicts
5. Click **"Complete Sync"** when finished

### Metadata Sync Best Practices

- **Verify Accuracy**: Always verify fetched metadata matches the correct movie
- **Handle Duplicates**: Remove duplicate entries before syncing
- **Update Regularly**: Sync metadata periodically to keep information current
- **Check Multiple Sources**: Compare data from different sources for accuracy
- **Manual Corrections**: Manually correct any inaccurate information

## Bulk Operations on Movies

### Bulk Edit

1. Navigate to the **Movies** section
2. Select multiple movies using checkboxes
3. Click the **"Bulk Edit"** button
4. Choose fields to update:
   - Genre
   - Rating
   - Status
   - Custom fields
5. Enter the new values
6. Click **"Preview"** to see which movies will be affected
7. Click **"Apply"** to update all selected movies
8. Monitor the progress in the status panel

### Bulk Delete

1. Select multiple movies using checkboxes
2. Click the **"Bulk Delete"** button
3. Review the list of movies to be deleted
4. Click **"Confirm Delete"** to proceed
5. The selected movies will be removed from your library
6. (Optional) Click **"Undo"** within 5 minutes to restore deleted movies

### Bulk Export

1. Select multiple movies using checkboxes
2. Click the **"Bulk Export"** button
3. Choose export format:
   - **CSV**: Comma-separated values
   - **JSON**: JSON format
   - **Excel**: Microsoft Excel format
4. Choose which fields to include:
   - Title, Year, Genre, Rating, Director, Cast, Plot, Runtime, etc.
5. Click **"Export"** to download the file

### Bulk Import

See the "Adding Multiple Movies" section above for detailed bulk import instructions.

### Batch Metadata Sync

1. Select multiple movies using checkboxes
2. Click the **"Batch Sync Metadata"** button
3. Choose metadata source (OMDB, TMDB, or Both)
4. Click **"Start Batch Sync"**
5. Monitor progress in the batch operations panel
6. Review results when complete
7. Click **"Apply Changes"** to save all updates

## Best Practices

### Library Organization

- **Consistent Naming**: Use consistent movie titles for better search results
- **Complete Information**: Fill in as much metadata as possible
- **Regular Updates**: Keep metadata current with periodic syncs
- **Remove Duplicates**: Periodically check for and remove duplicate entries
- **Use Collections**: Organize movies into meaningful collections

### Search Optimization

- **Specific Searches**: Use specific terms for better results
- **Combine Filters**: Use multiple filters together for precise results
- **Save Searches**: Save frequently used searches for quick access
- **Sort Strategically**: Sort by different criteria to find what you need
- **Use Pagination**: Navigate through results efficiently

### Performance Tips

- **Limit Results**: Use filters to reduce the number of items displayed
- **Batch Operations**: Use batch operations for bulk updates
- **Schedule Syncs**: Perform large metadata syncs during off-peak hours
- **Clear Cache**: Periodically clear your browser cache
- **Archive Old Items**: Move completed or unwanted items to an archive

### Data Quality

- **Verify Metadata**: Always verify fetched metadata is accurate
- **Handle Conflicts**: Carefully resolve metadata conflicts
- **Manual Corrections**: Correct any inaccurate information manually
- **Use Official Sources**: Prefer official metadata sources
- **Document Changes**: Keep notes about significant changes to your library

---

For more information, see:
- [Main User Guide](USER_GUIDE.md)
- [Search and Filtering Guide](USER_GUIDE_SEARCH_FILTER.md)
- [Batch Operations Guide](USER_GUIDE_BATCH_OPERATIONS.md)
