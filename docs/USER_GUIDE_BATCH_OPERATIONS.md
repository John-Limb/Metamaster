# Batch Operations User Guide

This guide provides comprehensive instructions for performing batch operations on multiple items in the Media Library Management System.

## Table of Contents

1. [Starting Batch Operations](#starting-batch-operations)
2. [Monitoring Progress](#monitoring-progress)
3. [Canceling Operations](#canceling-operations)
4. [Error Handling](#error-handling)
5. [Performance Considerations](#performance-considerations)
6. [Best Practices](#best-practices)
7. [Common Batch Operations](#common-batch-operations)

## Starting Batch Operations

### Selecting Items

Before starting a batch operation, you must select the items to operate on:

1. Navigate to the **Movies** or **TV Shows** section
2. Use checkboxes to select items:
   - **Select Individual Items**: Click the checkbox next to each item
   - **Select All on Page**: Click the checkbox in the header row
   - **Select All Results**: Click **"Select All"** button (selects all matching items, not just current page)
3. The selection counter shows how many items are selected
4. Click **"Clear Selection"** to deselect all items

### Available Batch Operations

#### Batch Edit

Update multiple items with the same information:

1. Select items using checkboxes
2. Click the **"Batch Edit"** button
3. Choose fields to update:
   - Genre
   - Rating
   - Status
   - Language
   - Custom fields
4. Enter the new values
5. Click **"Preview"** to see which items will be affected
6. Click **"Apply"** to start the operation

#### Batch Delete

Remove multiple items from your library:

1. Select items using checkboxes
2. Click the **"Batch Delete"** button
3. Review the list of items to be deleted
4. Click **"Confirm Delete"** to proceed
5. Items will be removed from your library
6. (Optional) Click **"Undo"** within 5 minutes to restore deleted items

#### Batch Export

Export multiple items to a file:

1. Select items using checkboxes
2. Click the **"Batch Export"** button
3. Choose export format:
   - **CSV**: Comma-separated values (Excel compatible)
   - **JSON**: JSON format (for data import/backup)
   - **Excel**: Microsoft Excel format (.xlsx)
4. Choose which fields to include:
   - Title, Year, Genre, Rating, Director, Cast, Plot, etc.
5. (For TV Shows) Choose whether to include episode data
6. Click **"Export"** to download the file

#### Batch Metadata Sync

Synchronize metadata for multiple items:

1. Select items using checkboxes
2. Click the **"Batch Sync Metadata"** button
3. Choose metadata source:
   - **OMDB**: Open Movie Database (movies)
   - **TVDB**: The TV Database (TV shows)
   - **TMDB**: The Movie Database (both)
   - **All**: Fetch from all available sources
4. Click **"Start Sync"**
5. Monitor progress in the batch operations panel
6. Review results when complete
7. Click **"Apply Changes"** to save all updates

#### Batch Tag/Categorize

Add tags or categories to multiple items:

1. Select items using checkboxes
2. Click the **"Batch Tag"** button
3. Choose action:
   - **Add Tags**: Add new tags to selected items
   - **Remove Tags**: Remove tags from selected items
   - **Replace Tags**: Replace existing tags
4. Enter or select tags
5. Click **"Preview"** to see affected items
6. Click **"Apply"** to apply tags

#### Batch Change Status

Update the status of multiple items:

1. Select items using checkboxes
2. Click the **"Batch Change Status"** button
3. Choose new status:
   - For Movies: Watched, Unwatched, In Progress
   - For TV Shows: Ongoing, Completed, Cancelled, On Hiatus
4. (Optional) Set the date for status change
5. Click **"Preview"** to see affected items
6. Click **"Apply"** to update status

#### Batch Move to Collection

Move multiple items to a collection:

1. Select items using checkboxes
2. Click the **"Batch Move to Collection"** button
3. Choose destination collection
4. Click **"Preview"** to see affected items
5. Click **"Apply"** to move items

#### Batch Copy to Collection

Copy multiple items to a collection (keeping originals):

1. Select items using checkboxes
2. Click the **"Batch Copy to Collection"** button
3. Choose destination collection
4. Click **"Preview"** to see affected items
5. Click **"Apply"** to copy items

## Monitoring Progress

### Batch Operations Panel

The batch operations panel displays real-time progress:

1. When a batch operation starts, the panel appears at the bottom of the screen
2. The panel shows:
   - **Operation Name**: Type of operation being performed
   - **Progress Bar**: Visual representation of completion percentage
   - **Status**: Current status (Processing, Completed, Failed, Cancelled)
   - **Items Processed**: Number of items completed / total items
   - **Time Elapsed**: How long the operation has been running
   - **Estimated Time Remaining**: Estimated completion time
   - **Current Item**: Name of item currently being processed

### Viewing Operation History

1. Click the **"Batch Operations"** menu
2. Click **"History"** to view past operations
3. The history shows:
   - Operation type
   - Number of items processed
   - Completion status
   - Date and time
   - Duration
4. Click on an operation to view detailed results

### Detailed Progress View

For long-running operations, open the detailed progress view:

1. Click the **"View Details"** button in the batch operations panel
2. The detailed view shows:
   - Overall progress percentage
   - Breakdown by status (Pending, Processing, Completed, Failed)
   - List of items being processed
   - Any errors encountered
   - Estimated completion time
3. Click **"Minimize"** to return to the compact view

### Notifications

Receive notifications when batch operations complete:

1. Navigate to **Settings** → **Notifications**
2. Enable **"Batch Operation Notifications"**
3. Choose notification type:
   - **Browser Notification**: Pop-up notification
   - **Email Notification**: Email when operation completes
   - **In-App Notification**: Message in the application
4. Click **"Save"**

## Canceling Operations

### Canceling a Running Operation

1. In the batch operations panel, click the **"Cancel"** button
2. Confirm the cancellation:
   - **Cancel Operation**: Stop the operation immediately
   - **Finish Current Item**: Complete the current item then stop
3. The operation will be cancelled
4. Items already processed will be saved
5. Remaining items will not be processed

### Partial Completion

When you cancel an operation:

- **Items Already Processed**: Changes are saved
- **Current Item**: May or may not be completed depending on cancellation type
- **Remaining Items**: Will not be processed
- **Undo Available**: You can undo the partial operation within 5 minutes

### Resuming Canceled Operations

If you cancel an operation, you can resume it:

1. Click the **"Batch Operations"** menu
2. Click **"Resume"** next to the canceled operation
3. The operation will resume from where it left off
4. Only remaining items will be processed

## Error Handling

### Understanding Error Messages

When errors occur during batch operations, you'll see:

- **Error Type**: Category of error (Validation, Network, Permission, etc.)
- **Error Message**: Description of what went wrong
- **Affected Item**: Which item caused the error
- **Suggested Action**: How to resolve the error

### Common Errors

#### Validation Errors

**Problem**: Invalid data provided for an item

**Solutions**:
1. Review the error message for specific field
2. Check the item's current data
3. Verify the new data is valid
4. Correct the data and retry

#### Network Errors

**Problem**: Connection lost during operation

**Solutions**:
1. Check your internet connection
2. Wait a few moments and retry
3. Try the operation again with fewer items
4. Contact your administrator if issues persist

#### Permission Errors

**Problem**: You don't have permission to modify certain items

**Solutions**:
1. Check your user permissions
2. Contact your administrator to request access
3. Try the operation on items you have permission to modify

#### Duplicate Errors

**Problem**: Attempting to create duplicate entries

**Solutions**:
1. Check for existing items with same data
2. Remove duplicates before retrying
3. Use different data for new items

### Error Recovery

1. When errors occur, the operation pauses
2. Review the error details
3. Choose an action:
   - **Retry**: Try the operation again for the failed item
   - **Skip**: Skip this item and continue with others
   - **Skip All Similar**: Skip all items with similar errors
   - **Cancel**: Stop the entire operation
4. The operation will continue based on your choice

### Viewing Error Reports

1. After an operation completes with errors, click **"View Error Report"**
2. The report shows:
   - Total items processed
   - Number of successful operations
   - Number of failed operations
   - Detailed error list
   - Suggested actions
3. Click **"Export Report"** to download the error report

## Performance Considerations

### Operation Size

The size of batch operations affects performance:

- **Small Operations**: 1-50 items (typically < 1 minute)
- **Medium Operations**: 50-500 items (typically 1-10 minutes)
- **Large Operations**: 500+ items (may take 10+ minutes)

### Recommended Batch Sizes

For optimal performance:

- **Metadata Sync**: 50-100 items per batch
- **Bulk Edit**: 100-500 items per batch
- **Bulk Delete**: 50-200 items per batch
- **Bulk Export**: 500+ items per batch

### System Load

Batch operations consume system resources:

- **CPU**: Processing and data transformation
- **Memory**: Storing operation state and results
- **Network**: Fetching metadata or uploading data
- **Database**: Reading and writing data

### Scheduling Operations

For large operations, schedule them during off-peak hours:

1. Navigate to **Settings** → **Batch Operations**
2. Enable **"Schedule Operations"**
3. Set preferred time window:
   - Off-peak hours (e.g., 2 AM - 6 AM)
   - Low-traffic periods
4. Click **"Save"**
5. Large operations will be automatically scheduled

### Monitoring System Resources

1. Navigate to **Settings** → **System**
2. View current resource usage:
   - CPU usage
   - Memory usage
   - Disk space
   - Network bandwidth
3. If resources are constrained:
   - Reduce batch operation size
   - Schedule operations for later
   - Close other applications
   - Contact your administrator

## Best Practices

### Planning Batch Operations

1. **Define Your Goal**: Know exactly what you want to accomplish
2. **Test First**: Try the operation on a small subset first
3. **Backup Data**: Ensure your data is backed up before large operations
4. **Schedule Wisely**: Perform large operations during off-peak hours
5. **Monitor Progress**: Watch the operation to catch any issues

### Selecting Items

- **Be Specific**: Select only the items you want to modify
- **Use Filters**: Apply filters to select items more precisely
- **Verify Selection**: Review the selection before starting
- **Start Small**: Begin with smaller batches to test
- **Expand Gradually**: Increase batch size as you gain confidence

### Executing Operations

- **One at a Time**: Don't start multiple large operations simultaneously
- **Monitor Progress**: Watch the progress panel for issues
- **Be Patient**: Allow operations to complete fully
- **Don't Close Browser**: Keep the browser window open during operation
- **Save Work**: Save any unsaved work before starting

### Error Management

- **Review Errors**: Always review error reports after operations
- **Understand Issues**: Understand why errors occurred
- **Correct Data**: Fix data issues before retrying
- **Document Problems**: Keep notes about recurring issues
- **Report Issues**: Report persistent problems to your administrator

### Performance Optimization

- **Batch Size**: Use recommended batch sizes for your operation type
- **Timing**: Schedule large operations during off-peak hours
- **Frequency**: Don't run multiple large operations simultaneously
- **Cleanup**: Regularly clean up old operations from history
- **Monitor Resources**: Keep an eye on system resource usage

## Common Batch Operations

### Scenario 1: Updating Movie Genres

1. Navigate to **Movies**
2. Search for movies: `Action`
3. Click **"Select All"** to select all action movies
4. Click **"Batch Edit"**
5. Select **"Genre"** field
6. Add genre: `Adventure`
7. Click **"Preview"** to verify
8. Click **"Apply"** to update all movies

### Scenario 2: Syncing Metadata for New Additions

1. Navigate to **Movies**
2. Filter by: Date Added = Last 7 days
3. Click **"Select All"** to select recent additions
4. Click **"Batch Sync Metadata"**
5. Choose source: **TMDB**
6. Click **"Start Sync"**
7. Monitor progress and review results

### Scenario 3: Exporting Your Library

1. Navigate to **Movies**
2. Click **"Select All"** to select all movies
3. Click **"Batch Export"**
4. Choose format: **CSV**
5. Select fields to include
6. Click **"Export"** to download

### Scenario 4: Marking TV Show Episodes as Watched

1. Navigate to **TV Shows**
2. Click on a show to open details
3. Click **"Seasons"** tab
4. Select a season
5. Click **"Select All Episodes"**
6. Click **"Batch Mark as Watched"**
7. Confirm the action

### Scenario 5: Organizing Movies into Collections

1. Navigate to **Movies**
2. Search for movies: `Drama`
3. Filter by: Rating >= 8.0
4. Click **"Select All"** to select all highly-rated dramas
5. Click **"Batch Move to Collection"**
6. Choose collection: **"Top Rated Dramas"**
7. Click **"Apply"** to move all movies

---

For more information, see:
- [Main User Guide](USER_GUIDE.md)
- [Movie Management Guide](USER_GUIDE_MOVIES.md)
- [TV Show Management Guide](USER_GUIDE_TV_SHOWS.md)
- [Search and Filtering Guide](USER_GUIDE_SEARCH_FILTER.md)
