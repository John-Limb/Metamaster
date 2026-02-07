# Search and Filtering User Guide

This guide provides comprehensive instructions for using the search and filtering features in the Media Library Management System.

## Table of Contents

1. [Basic Search](#basic-search)
2. [Advanced Filtering](#advanced-filtering)
3. [Sorting Options](#sorting-options)
4. [Pagination](#pagination)
5. [Saved Searches](#saved-searches)
6. [Search Tips and Tricks](#search-tips-and-tricks)
7. [Performance Optimization](#performance-optimization)

## Basic Search

### Quick Search

The quick search feature allows you to search across your entire library with a simple text query.

1. Navigate to the **Search** section or use the search box in the main navigation
2. Enter your search query:
   - Movie or show title
   - Actor or director name
   - Genre keyword
   - Any other relevant term
3. Press **Enter** or click the **Search** button
4. Results will display matching items from both movies and TV shows
5. Click on any result to view full details

### Search Scope

By default, search looks across:
- **Titles**: Movie and show titles
- **Descriptions**: Plot summaries and descriptions
- **Cast**: Actor and director names
- **Genres**: Genre tags
- **Custom Fields**: Any custom metadata fields

### Search Operators

Use these operators to refine your search:

- **Exact Match**: Use quotes to search for exact phrases
  - Example: `"The Dark Knight"` finds only exact title matches
  
- **Exclude Terms**: Use minus sign to exclude results
  - Example: `Batman -Begins` finds Batman movies except Batman Begins
  
- **OR Operator**: Use pipe symbol to search for multiple terms
  - Example: `Action|Adventure` finds items with either genre
  
- **Wildcard**: Use asterisk for partial matches
  - Example: `Star*` finds Star Wars, Star Trek, etc.

### Search Results

Search results display:
- **Item Type**: Icon indicating Movie or TV Show
- **Title**: Item title with year
- **Rating**: User rating and external ratings
- **Genre**: Primary genres
- **Description**: Brief plot summary
- **Poster**: Thumbnail image
- **Relevance Score**: How well the result matches your query

## Advanced Filtering

### Accessing Filters

1. In the Search section, click the **"Filters"** button
2. The filter panel will expand showing all available filter options
3. Apply one or more filters as needed
4. Click **"Apply Filters"** to update results
5. Click **"Clear Filters"** to reset all filters

### Available Filters

#### Content Type Filter

Filter by the type of content:
- **Movies**: Show only movies
- **TV Shows**: Show only TV shows
- **Both**: Show both movies and TV shows (default)

#### Genre Filter

Select one or more genres:
- Action
- Adventure
- Animation
- Comedy
- Crime
- Documentary
- Drama
- Family
- Fantasy
- History
- Horror
- Music
- Mystery
- Romance
- Sci-Fi
- Sport
- Thriller
- War
- Western
- And more...

**Usage**:
1. Click the **Genre** filter
2. Check the genres you want to include
3. Results will show items matching any selected genre
4. To narrow results, select fewer genres

#### Rating Filter

Filter by content rating:

**User Rating**:
- Set minimum rating: 1-10 scale
- Set maximum rating: 1-10 scale
- Example: Show only movies rated 7.0 or higher

**Content Rating** (for movies):
- G: General Audiences
- PG: Parental Guidance
- PG-13: Parents Strongly Cautioned
- R: Restricted
- NC-17: Adults Only
- Not Rated: Unrated content

**Usage**:
1. Click the **Rating** filter
2. Set minimum and/or maximum values
3. Click **"Apply"** to filter results

#### Year Filter

Filter by release year:

1. Click the **Year** filter
2. Set the "From" year (earliest)
3. Set the "To" year (latest)
4. Click **"Apply"** to filter results

**Examples**:
- Classic films: 1900-1980
- Modern movies: 2000-present
- Recent releases: 2020-present
- Specific year: Set both from and to the same year

#### Network/Studio Filter

Filter by network or production studio:

1. Click the **Network** filter (for TV shows)
2. Select one or more networks:
   - HBO
   - Netflix
   - Amazon Prime
   - NBC
   - ABC
   - CBS
   - Fox
   - And more...
3. Click **"Apply"** to filter results

#### Status Filter

Filter by content status:

**For TV Shows**:
- Ongoing: Currently airing
- Completed: Finished series
- Cancelled: Cancelled series
- On Hiatus: Temporarily on break

**For Movies**:
- Watched: Movies you've watched
- Unwatched: Movies you haven't watched
- In Progress: Movies you're currently watching

#### Language Filter

Filter by primary language:

1. Click the **Language** filter
2. Select one or more languages:
   - English
   - Spanish
   - French
   - German
   - Italian
   - Japanese
   - Korean
   - And more...
3. Click **"Apply"** to filter results

#### Director/Creator Filter

Filter by director or creator:

1. Click the **Director/Creator** filter
2. Enter the name or select from the list
3. Results will show only items by that director/creator
4. Click **"Apply"** to filter results

#### Custom Filters

If your administrator has set up custom fields, you can filter by:
- Custom categories
- Custom tags
- Custom ratings
- Other custom metadata

### Combining Filters

You can combine multiple filters for precise results:

1. Select a genre (e.g., "Drama")
2. Set a rating range (e.g., 8.0-10.0)
3. Set a year range (e.g., 2000-2023)
4. Select a language (e.g., "English")
5. Click **"Apply Filters"**
6. Results will show only Drama movies in English from 2000-2023 rated 8.0 or higher

### Filter Presets

Save common filter combinations:

1. Set up your desired filters
2. Click **"Save as Preset"**
3. Enter a name (e.g., "Top Rated Dramas")
4. Click **"Save"**
5. To use a preset:
   - Click **"Load Preset"**
   - Select your saved preset
   - Filters will be applied automatically

## Sorting Options

### Available Sort Options

Click the **"Sort By"** dropdown to choose how results are organized:

#### For Movies

- **Title (A-Z)**: Alphabetical order by title
- **Title (Z-A)**: Reverse alphabetical order
- **Year (Newest)**: Most recent release first
- **Year (Oldest)**: Oldest release first
- **Rating (Highest)**: Highest rated first
- **Rating (Lowest)**: Lowest rated first
- **Date Added**: Most recently added to library first
- **Date Watched**: Most recently watched first
- **Runtime (Longest)**: Longest movies first
- **Runtime (Shortest)**: Shortest movies first
- **Relevance**: Best match to search query first

#### For TV Shows

- **Title (A-Z)**: Alphabetical order by title
- **Title (Z-A)**: Reverse alphabetical order
- **Network**: Sort by network name
- **Status**: Sort by show status
- **Rating (Highest)**: Highest rated first
- **Rating (Lowest)**: Lowest rated first
- **Date Added**: Most recently added to library first
- **Air Date (Newest)**: Most recent air date first
- **Air Date (Oldest)**: Oldest air date first
- **Relevance**: Best match to search query first

### Reverse Sort Order

1. Click the sort option
2. Click the **"Reverse"** button or arrow icon
3. Results will be sorted in the opposite order

### Multi-Level Sorting

Sort by multiple criteria:

1. Click the **"Advanced Sort"** button
2. Select primary sort criteria
3. Click **"Add Sort Level"**
4. Select secondary sort criteria
5. (Optional) Add additional sort levels
6. Click **"Apply"** to sort results

**Example**: Sort by Genre, then by Rating (highest first), then by Title (A-Z)

## Pagination

### Pagination Controls

At the bottom of search results, you'll find pagination controls:

- **Items Per Page**: Choose how many results to display
  - 10 items per page
  - 25 items per page
  - 50 items per page
  - 100 items per page
  
- **Page Navigation**:
  - **Previous**: Go to previous page
  - **Next**: Go to next page
  - **Page Numbers**: Click to jump to specific page
  - **Go to Page**: Enter page number and press Enter

### Pagination Information

The pagination display shows:
- Current page number
- Total number of pages
- Total number of results
- Results displayed on current page

**Example**: "Showing 1-25 of 487 results (Page 1 of 20)"

### Infinite Scroll

Enable infinite scroll for continuous browsing:

1. Navigate to **Settings** → **Preferences**
2. Enable **"Infinite Scroll"**
3. Click **"Save"**
4. Results will load automatically as you scroll down

## Saved Searches

### Creating a Saved Search

1. Set up your desired search query and filters
2. Click the **"Save Search"** button
3. Enter a descriptive name:
   - "Top Rated Dramas"
   - "Recent Action Movies"
   - "Completed HBO Shows"
   - "Unwatched Sci-Fi"
4. (Optional) Add a description
5. Click **"Save"**

### Using Saved Searches

1. Click the **"Saved Searches"** dropdown menu
2. Select your saved search from the list
3. The search query and filters will be applied automatically
4. Results will load immediately

### Managing Saved Searches

1. Click the **"Saved Searches"** dropdown
2. Hover over a saved search to see options:
   - **Load**: Apply the saved search
   - **Edit**: Modify the search name or description
   - **Delete**: Remove the saved search
   - **Duplicate**: Create a copy of the search

### Organizing Saved Searches

Create folders to organize your saved searches:

1. Click **"Manage Saved Searches"**
2. Click **"Create Folder"**
3. Enter a folder name (e.g., "Favorites", "To Watch")
4. Click **"Create"**
5. Drag saved searches into folders to organize them

## Search Tips and Tricks

### Effective Search Strategies

#### Specific Searches

- **Good**: "The Shawshank Redemption"
- **Better**: "Shawshank Redemption 1994"
- **Best**: "Shawshank Redemption" + Drama filter + 1994 year filter

#### Partial Searches

- Use wildcards for partial matches: `Star*` finds Star Wars, Star Trek, etc.
- Search for actor names: `Tom Hanks` finds all movies with Tom Hanks
- Search for directors: `Spielberg` finds all Spielberg films

#### Combining Search and Filters

1. Search for a broad term: "Action"
2. Apply filters to narrow results:
   - Year: 2020-2023
   - Rating: 7.0+
   - Language: English
3. Results will show recent, highly-rated English action movies

### Advanced Search Techniques

#### Finding Similar Content

1. Find a movie or show you like
2. Note its genre, director, and cast
3. Search for the director or actor
4. Apply genre filters
5. Sort by rating to find similar highly-rated content

#### Discovering New Content

1. Search for a broad genre: "Drama"
2. Apply filters:
   - Year: 2020-2023 (recent)
   - Rating: 7.0+ (well-rated)
   - Language: Your preferred language
3. Sort by rating (highest first)
4. Browse results to discover new content

#### Finding Specific Content

1. Use exact match with quotes: `"The Office"`
2. Add year if needed: `"The Office" 2005`
3. Add network if needed: `"The Office" NBC`
4. Apply filters to narrow further

### Search Performance Tips

- **Use Specific Terms**: More specific searches are faster
- **Combine Filters**: Use filters to reduce result set size
- **Limit Results**: Display fewer items per page for faster loading
- **Clear Cache**: Periodically clear browser cache for better performance
- **Avoid Wildcards**: Wildcard searches can be slower; use specific terms when possible

### Troubleshooting Search Issues

#### No Results Found

1. Check spelling of search terms
2. Try a simpler search query
3. Remove or adjust filters
4. Try searching for related terms
5. Check if items exist in your library

#### Too Many Results

1. Add more specific filters
2. Combine multiple filters
3. Use exact match with quotes
4. Sort by relevance to find best matches
5. Use pagination to browse results

#### Slow Search Performance

1. Use more specific search terms
2. Apply filters to reduce result set
3. Reduce items per page
4. Clear browser cache
5. Try searching again after a few minutes

## Performance Optimization

### Optimizing Search Performance

#### Use Filters Effectively

- Filters reduce the result set before displaying
- Combining filters is more efficient than complex search queries
- Apply the most restrictive filters first

#### Pagination Best Practices

- Display fewer items per page (10-25) for faster loading
- Use pagination instead of infinite scroll for large result sets
- Navigate directly to specific pages instead of scrolling

#### Cache Management

1. Clear browser cache regularly:
   - Chrome: Ctrl+Shift+Delete (Windows) or Cmd+Shift+Delete (Mac)
   - Firefox: Ctrl+Shift+Delete (Windows) or Cmd+Shift+Delete (Mac)
   - Safari: Develop → Empty Caches
2. Clear application cache in Settings → Preferences

#### Browser Optimization

- Close unused browser tabs
- Use a modern browser (Chrome, Firefox, Safari, Edge)
- Disable unnecessary browser extensions
- Ensure sufficient available RAM

### Monitoring Search Performance

1. Navigate to **Settings** → **Advanced**
2. Enable **"Show Performance Metrics"**
3. Search metrics will display:
   - Query execution time
   - Number of results
   - Filter processing time
   - Display rendering time

---

For more information, see:
- [Main User Guide](USER_GUIDE.md)
- [Movie Management Guide](USER_GUIDE_MOVIES.md)
- [TV Show Management Guide](USER_GUIDE_TV_SHOWS.md)
- [Batch Operations Guide](USER_GUIDE_BATCH_OPERATIONS.md)
