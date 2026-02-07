# TV Show Management User Guide

This guide provides comprehensive instructions for managing your TV show collection in the Media Library Management System.

## Table of Contents

1. [Adding TV Shows](#adding-tv-shows)
2. [Managing Seasons and Episodes](#managing-seasons-and-episodes)
3. [Searching and Filtering TV Shows](#searching-and-filtering-tv-shows)
4. [Viewing Show Details](#viewing-show-details)
5. [Syncing TV Show Metadata](#syncing-tv-show-metadata)
6. [Bulk Operations on TV Shows](#bulk-operations-on-tv-shows)
7. [Best Practices](#best-practices)

## Adding TV Shows

### Adding a Single TV Show

#### Method 1: Manual Entry

1. Navigate to the **TV Shows** section from the main menu
2. Click the **"Add Show"** button in the top-right corner
3. Fill in the show details:
   - **Title** (required): Enter the exact show title
   - **Network** (optional): Enter the network or streaming service
   - **Genre** (optional): Select one or more genres
   - **Status** (optional): Select status (Ongoing, Completed, Cancelled, On Hiatus)
   - **Rating** (optional): Set the show rating (1-10 or similar scale)
   - **Creator** (optional): Enter the creator's name
   - **Cast** (optional): Add main cast members
   - **Plot** (optional): Enter a brief plot summary
   - **Language** (optional): Select the primary language
   - **Poster URL** (optional): Provide a link to the show poster
   - **Number of Seasons** (optional): Enter total number of seasons
4. Click **"Save"** to add the show to your library

#### Method 2: Search and Fetch Metadata

1. Navigate to the **TV Shows** section
2. Click the **"Add Show"** button
3. Enter the show title in the search field
4. Click **"Search Metadata"** to fetch information from external sources
5. Review the search results:
   - Select the correct show from the results
   - Verify the information is accurate
   - Check the poster and other details
6. Click **"Confirm"** to populate the form with fetched data
7. Make any necessary adjustments to the information
8. Click **"Save"** to add the show

### Adding Multiple TV Shows

#### Bulk Import

1. Navigate to the **TV Shows** section
2. Click the **"Bulk Import"** button
3. Choose your import method:
   - **CSV File**: Upload a CSV file with show data
   - **JSON File**: Upload a JSON file with show data
   - **Paste Data**: Paste show data directly
4. Map the columns to the correct fields:
   - Title → Show Title
   - Network → Network
   - Genre → Genre(s)
   - Status → Status
   - Rating → Rating
   - Creator → Creator
5. Click **"Preview"** to verify the data
6. Click **"Import"** to add all shows to your library
7. Monitor the import progress in the status panel

#### CSV Format Example

```
Title,Network,Genre,Status,Rating,Creator
Breaking Bad,AMC,Crime|Drama,Completed,9.5,Vince Gilligan
Game of Thrones,HBO,Action|Adventure|Drama,Completed,9.2,David Benioff|D.B. Weiss
The Office,NBC,Comedy,Completed,9.0,Greg Daniels|Michael Schur
```

#### JSON Format Example

```json
[
  {
    "title": "Breaking Bad",
    "network": "AMC",
    "genre": ["Crime", "Drama"],
    "status": "Completed",
    "rating": 9.5,
    "creator": "Vince Gilligan"
  },
  {
    "title": "Game of Thrones",
    "network": "HBO",
    "genre": ["Action", "Adventure", "Drama"],
    "status": "Completed",
    "rating": 9.2,
    "creator": ["David Benioff", "D.B. Weiss"]
  }
]
```

## Managing Seasons and Episodes

### Adding Seasons

1. Navigate to the **TV Shows** section
2. Click on a show to open its details page
3. Click the **"Seasons"** tab
4. Click the **"Add Season"** button
5. Enter season details:
   - **Season Number** (required): Enter the season number
   - **Air Date** (optional): Enter the air date
   - **Number of Episodes** (optional): Enter the number of episodes
   - **Description** (optional): Add a season description
6. Click **"Save"** to add the season

### Adding Episodes

1. On the show details page, click the **"Seasons"** tab
2. Select a season to view its episodes
3. Click the **"Add Episode"** button
4. Enter episode details:
   - **Episode Number** (required): Enter the episode number
   - **Title** (optional): Enter the episode title
   - **Air Date** (optional): Enter the air date
   - **Runtime** (optional): Enter the episode duration
   - **Plot** (optional): Enter the episode plot summary
   - **Director** (optional): Enter the director's name
   - **Writer** (optional): Enter the writer's name
5. Click **"Save"** to add the episode

### Marking Episodes as Watched

#### Method 1: Individual Episode

1. On the show details page, click the **"Seasons"** tab
2. Select a season to view episodes
3. Find the episode you want to mark as watched
4. Click the checkbox next to the episode
5. (Optional) Set the watch date:
   - Click the date field
   - Select the date you watched the episode
   - Click **"Confirm"**
6. The episode will be marked as watched

#### Method 2: Bulk Mark Season

1. On the show details page, click the **"Seasons"** tab
2. Select a season
3. Click the **"Mark Season as Watched"** button
4. Confirm the action
5. All episodes in the season will be marked as watched

#### Method 3: Bulk Mark Show

1. On the show details page, click the **"Mark All as Watched"** button
2. Confirm the action
3. All episodes in all seasons will be marked as watched

### Editing Episode Details

1. On the show details page, click the **"Seasons"** tab
2. Select a season to view episodes
3. Click on an episode to open its details
4. Click the **"Edit"** button
5. Modify the episode information:
   - Title
   - Air Date
   - Runtime
   - Plot
   - Director
   - Writer
   - Guest Cast
6. Click **"Save"** to update the episode
7. Click **"Cancel"** to discard changes

### Rating Episodes

1. On the show details page, click the **"Seasons"** tab
2. Select a season to view episodes
3. Click on an episode to open its details
4. Click the **"Rate"** button
5. Select your rating (1-10 or similar scale)
6. (Optional) Add a review or comment
7. Click **"Save"** to save your rating

### Adding Episode Notes

1. On the episode details page, scroll to the **"Notes"** section
2. Click **"Add Note"** to create a new note
3. Enter your note or review
4. (Optional) Set a note type:
   - Personal Review
   - Reminder
   - Trivia
   - Other
5. Click **"Save Note"**

## Searching and Filtering TV Shows

### Basic Search

1. Navigate to the **TV Shows** section
2. Use the search box at the top of the show list
3. Type the show title or keywords
4. Press **Enter** or click the **Search** button
5. Results will display matching shows

### Advanced Filtering

1. Click the **"Filters"** button to expand filter options
2. Apply one or more filters:
   - **Genre**: Select one or more genres
   - **Network**: Filter by network or streaming service
   - **Status**: Filter by show status (Ongoing, Completed, Cancelled, On Hiatus)
   - **Rating**: Set minimum and maximum rating
   - **Creator**: Filter by creator name
   - **Language**: Select language(s)
   - **Viewing Status**: Filter by watched/unwatched status
3. Click **"Apply Filters"** to update results
4. Click **"Clear Filters"** to reset all filters

### Sorting Options

1. Click the **"Sort By"** dropdown menu
2. Choose a sorting option:
   - **Title (A-Z)**: Alphabetical order
   - **Title (Z-A)**: Reverse alphabetical order
   - **Network**: Sort by network name
   - **Status**: Sort by show status
   - **Rating (Highest)**: Highest rated first
   - **Rating (Lowest)**: Lowest rated first
   - **Date Added**: Most recently added first
   - **Air Date (Newest)**: Most recent air date first
   - **Air Date (Oldest)**: Oldest air date first
3. Results will be sorted according to your selection

### Pagination

1. At the bottom of the show list, you'll see pagination controls
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
3. Enter a name for your saved search (e.g., "Completed HBO Shows")
4. Click **"Save"**
5. To use a saved search:
   - Click the **"Saved Searches"** dropdown
   - Select your saved search
   - Results will load automatically

## Viewing Show Details

### Show Details Page

1. Click on any show in the list to open its details page
2. The details page displays:
   - **Poster**: Show poster image
   - **Title**: Show title and network
   - **Rating**: User rating and external ratings
   - **Genre**: Show genres
   - **Status**: Current show status
   - **Creator**: Creator information
   - **Cast**: Main cast members
   - **Plot**: Full plot summary
   - **Language**: Primary language
   - **First Air Date**: Original air date
   - **Network**: Broadcasting network or streaming service
   - **Number of Seasons**: Total seasons
   - **Number of Episodes**: Total episodes
   - **Production Company**: Studio/production company

### Seasons and Episodes Tab

1. On the show details page, click the **"Seasons"** tab
2. View all seasons with:
   - Season number
   - Number of episodes
   - Air date
   - Season description
3. Click on a season to expand and view episodes
4. Each episode shows:
   - Episode number and title
   - Air date
   - Runtime
   - Watched status (checkbox)
   - Rating (if rated)

### Editing Show Details

1. On the show details page, click the **"Edit"** button
2. Modify any of the following fields:
   - Title
   - Network
   - Genre
   - Status
   - Rating
   - Creator
   - Cast
   - Plot
   - Language
   - Poster URL
   - Custom fields
3. Click **"Save"** to update the show
4. Click **"Cancel"** to discard changes

### Adding Show Notes and Reviews

1. On the show details page, scroll to the **"Notes"** section
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

## Syncing TV Show Metadata

### Manual Metadata Sync

1. Navigate to the **TV Shows** section
2. Select one or more shows using checkboxes
3. Click the **"Sync Metadata"** button
4. Choose the metadata source:
   - **TVDB**: The TV Database
   - **TMDB**: The Movie Database
   - **Both**: Fetch from both sources and merge
5. Click **"Start Sync"**
6. Monitor the progress in the status panel
7. Review the updated information
8. Click **"Confirm"** to save changes

### Syncing Episode Metadata

1. On the show details page, click the **"Seasons"** tab
2. Click the **"Sync Episode Metadata"** button
3. Choose the metadata source (TVDB, TMDB, or Both)
4. Click **"Start Sync"**
5. Monitor the progress as episode information is fetched
6. Review the updated episode details
7. Click **"Confirm"** to save changes

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

## Bulk Operations on TV Shows

### Bulk Edit

1. Navigate to the **TV Shows** section
2. Select multiple shows using checkboxes
3. Click the **"Bulk Edit"** button
4. Choose fields to update:
   - Genre
   - Network
   - Status
   - Rating
   - Custom fields
5. Enter the new values
6. Click **"Preview"** to see which shows will be affected
7. Click **"Apply"** to update all selected shows
8. Monitor the progress in the status panel

### Bulk Delete

1. Select multiple shows using checkboxes
2. Click the **"Bulk Delete"** button
3. Review the list of shows to be deleted
4. Click **"Confirm Delete"** to proceed
5. The selected shows will be removed from your library
6. (Optional) Click **"Undo"** within 5 minutes to restore deleted shows

### Bulk Export

1. Select multiple shows using checkboxes
2. Click the **"Bulk Export"** button
3. Choose export format:
   - **CSV**: Comma-separated values
   - **JSON**: JSON format
   - **Excel**: Microsoft Excel format
4. Choose which fields to include:
   - Title, Network, Genre, Status, Rating, Creator, Cast, Plot, etc.
5. Choose whether to include episode data
6. Click **"Export"** to download the file

### Bulk Import

See the "Adding Multiple TV Shows" section above for detailed bulk import instructions.

### Batch Metadata Sync

1. Select multiple shows using checkboxes
2. Click the **"Batch Sync Metadata"** button
3. Choose metadata source (TVDB, TMDB, or Both)
4. Click **"Start Batch Sync"**
5. Monitor progress in the batch operations panel
6. Review results when complete
7. Click **"Apply Changes"** to save all updates

## Best Practices

### Library Organization

- **Consistent Naming**: Use consistent show titles for better search results
- **Complete Information**: Fill in as much metadata as possible
- **Regular Updates**: Keep metadata current with periodic syncs
- **Remove Duplicates**: Periodically check for and remove duplicate entries
- **Track Progress**: Keep episode viewing status up to date

### Episode Management

- **Update Regularly**: Mark episodes as watched promptly
- **Rate Episodes**: Rate episodes to track your favorites
- **Add Notes**: Document interesting episodes or plot points
- **Organize Seasons**: Keep season information organized and complete
- **Sync Metadata**: Periodically sync episode metadata for accuracy

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
- **Archive Completed**: Move completed shows to an archive section

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
