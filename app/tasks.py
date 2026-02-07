"""Celery task configuration and definitions"""

import logging
import traceback
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from celery import Celery
from sqlalchemy.orm import Session
from app.config import settings
from app.database import SessionLocal
from app.models import Movie, TVShow, APICache, FileQueue, MovieFile, EpisodeFile, BatchOperation
from app.services_impl import OMDBService, TVDBService
from app.services.ffprobe_wrapper import FFProbeWrapper
from app.services.file_queue_manager import FileQueueManager
from app.services.task_error_handler import TaskErrorHandler
from app.services.batch_operations import BatchOperationService
import asyncio

logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    "media_tool",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
)


@celery_app.task(bind=True, max_retries=3)
def analyze_file(self, file_path: str):
    """Analyze media file with FFPROBE
    
    Args:
        file_path: Path to the media file to analyze
        
    Returns:
        Dictionary with analysis results including codec, resolution, bitrate, duration
    """
    try:
        logger.info(f"Starting file analysis for: {file_path}")
        
        # Initialize FFProbe wrapper
        ffprobe = FFProbeWrapper()
        
        # Extract metadata
        metadata = ffprobe.get_metadata(file_path)
        
        if "error" in metadata:
            logger.error(f"FFProbe analysis failed for {file_path}: {metadata['error']}")
            raise RuntimeError(f"FFProbe analysis failed: {metadata['error']}")
        
        # Extract key information
        resolution = metadata.get("resolution", {})
        bitrate = metadata.get("bitrate", {})
        codecs = metadata.get("codecs", {})
        duration = metadata.get("duration", -1)
        
        result = {
            "status": "success",
            "file_path": file_path,
            "codec_video": codecs.get("video", "Unknown"),
            "codec_audio": codecs.get("audio", "Unknown"),
            "resolution": f"{resolution.get('width', 0)}x{resolution.get('height', 0)}",
            "resolution_label": resolution.get("label", "Unknown"),
            "bitrate_total": bitrate.get("total", "Unknown"),
            "bitrate_video": bitrate.get("video", "Unknown"),
            "bitrate_audio": bitrate.get("audio", "Unknown"),
            "duration": duration,
            "frame_rate": metadata.get("frame_rate", -1),
        }
        
        logger.info(f"File analysis completed for: {file_path}")
        return result
        
    except FileNotFoundError as exc:
        logger.error(f"File not found during analysis: {file_path}")
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=2 ** self.request.retries)
        else:
            # Final failure - handle error
            TaskErrorHandler.handle_task_failure(
                task_id=self.request.id,
                task_name=self.name,
                exception=exc,
                tb=traceback.format_exc(),
                retry_count=self.request.retries,
            )
            raise
    except Exception as exc:
        logger.error(f"Error analyzing file {file_path}: {str(exc)}")
        if self.request.retries < self.max_retries:
            # Retry with exponential backoff
            raise self.retry(exc=exc, countdown=2 ** self.request.retries)
        else:
            # Final failure - handle error
            TaskErrorHandler.handle_task_failure(
                task_id=self.request.id,
                task_name=self.name,
                exception=exc,
                tb=traceback.format_exc(),
                retry_count=self.request.retries,
            )
            raise


@celery_app.task(bind=True, max_retries=3)
def enrich_metadata(self, media_id: int, media_type: str):
    """Enrich metadata from external APIs
    
    Args:
        media_id: ID of the media item in database
        media_type: Type of media ("movie" or "tv_show")
        
    Returns:
        Dictionary with enriched metadata
    """
    db: Optional[Session] = None
    try:
        logger.info(f"Starting metadata enrichment for {media_type} ID: {media_id}")
        
        db = SessionLocal()
        
        if media_type == "movie":
            media = db.query(Movie).filter(Movie.id == media_id).first()
            if not media:
                logger.error(f"Movie not found: {media_id}")
                raise RuntimeError(f"Movie not found: {media_id}")
            
            # Fetch from OMDB if we have an omdb_id
            if media.omdb_id:
                omdb_data = asyncio.run(OMDBService.get_movie_details(db, media.omdb_id))
                if omdb_data:
                    parsed = OMDBService.parse_omdb_response(omdb_data)
                    if parsed:
                        # Update movie with enriched data
                        media.plot = parsed.get("plot", media.plot)
                        media.rating = parsed.get("rating", media.rating)
                        media.runtime = parsed.get("runtime", media.runtime)
                        media.genres = parsed.get("genres", media.genres)
                        db.commit()
                        logger.info(f"Movie metadata enriched: {media_id}")
                        return {
                            "status": "success",
                            "media_id": media_id,
                            "media_type": media_type,
                            "enriched_fields": ["plot", "rating", "runtime", "genres"]
                        }
            
            return {
                "status": "success",
                "media_id": media_id,
                "media_type": media_type,
                "enriched_fields": []
            }
            
        elif media_type == "tv_show":
            media = db.query(TVShow).filter(TVShow.id == media_id).first()
            if not media:
                logger.error(f"TV Show not found: {media_id}")
                raise RuntimeError(f"TV Show not found: {media_id}")
            
            # Fetch from TVDB if we have a tvdb_id
            if media.tvdb_id:
                tvdb_data = asyncio.run(TVDBService.get_series_details(db, media.tvdb_id))
                if tvdb_data:
                    parsed = TVDBService.parse_tvdb_series_response(tvdb_data)
                    if parsed:
                        # Update TV show with enriched data
                        media.plot = parsed.get("plot", media.plot)
                        media.rating = parsed.get("rating", media.rating)
                        media.genres = parsed.get("genres", media.genres)
                        media.status = parsed.get("status", media.status)
                        db.commit()
                        logger.info(f"TV Show metadata enriched: {media_id}")
                        return {
                            "status": "success",
                            "media_id": media_id,
                            "media_type": media_type,
                            "enriched_fields": ["plot", "rating", "genres", "status"]
                        }
            
            return {
                "status": "success",
                "media_id": media_id,
                "media_type": media_type,
                "enriched_fields": []
            }
        else:
            raise ValueError(f"Invalid media_type: {media_type}")
            
    except Exception as exc:
        logger.error(f"Error enriching metadata for {media_type} ID {media_id}: {str(exc)}")
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=2 ** self.request.retries)
        else:
            # Final failure - handle error
            TaskErrorHandler.handle_task_failure(
                task_id=self.request.id,
                task_name=self.name,
                exception=exc,
                tb=traceback.format_exc(),
                retry_count=self.request.retries,
            )
            raise
    finally:
        if db:
            db.close()


@celery_app.task(bind=True)
def cleanup_cache(self):
    """Clean up expired cache entries
    
    Identifies and removes cache entries older than 24 hours.
    Logs cleanup statistics.
    
    Returns:
        Dictionary with cleanup statistics
    """
    db: Optional[Session] = None
    try:
        logger.info("Starting cache cleanup task")
        
        db = SessionLocal()
        
        # Calculate cutoff time (24 hours ago)
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        # Find expired cache entries
        expired_entries = db.query(APICache).filter(
            APICache.expires_at < datetime.utcnow()
        ).all()
        
        entries_removed = len(expired_entries)
        
        # Remove expired entries
        for entry in expired_entries:
            db.delete(entry)
        
        db.commit()
        
        # Calculate space freed (approximate)
        space_freed_bytes = sum(len(entry.response_data) for entry in expired_entries)
        space_freed_mb = space_freed_bytes / (1024 * 1024)
        
        logger.info(
            f"Cache cleanup completed: {entries_removed} entries removed, "
            f"~{space_freed_mb:.2f} MB freed"
        )
        
        return {
            "status": "success",
            "message": "Cache cleanup completed",
            "entries_removed": entries_removed,
            "space_freed_mb": round(space_freed_mb, 2),
            "cutoff_time": cutoff_time.isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Error during cache cleanup: {str(exc)}")
        # Handle error for non-critical task
        TaskErrorHandler.handle_task_failure(
            task_id=self.request.id,
            task_name=self.name,
            exception=exc,
            tb=traceback.format_exc(),
            retry_count=0,
        )
        return {
            "status": "error",
            "message": f"Cache cleanup failed: {str(exc)}"
        }
    finally:
        if db:
            db.close()


@celery_app.task(bind=True)
def cleanup_queue(self):
    """Clean up old queue entries
    
    Removes stale entries from file queue (older than 7 days).
    Updates queue status for abandoned items.
    Logs cleanup statistics.
    
    Returns:
        Dictionary with cleanup statistics
    """
    db: Optional[Session] = None
    try:
        logger.info("Starting queue cleanup task")
        
        db = SessionLocal()
        queue_manager = FileQueueManager(db)
        
        # Calculate cutoff time (7 days ago)
        cutoff_time = datetime.utcnow() - timedelta(days=7)
        
        # Find stale entries (older than 7 days, not completed)
        stale_entries = db.query(FileQueue).filter(
            FileQueue.created_at < cutoff_time,
            FileQueue.status.in_(["pending", "processing"])
        ).all()
        
        entries_updated = 0
        
        # Update stale entries to failed status
        for entry in stale_entries:
            entry.status = FileQueueManager.STATUS_FAILED
            entry.error_message = "Abandoned: Processing timeout after 7 days"
            entry.processed_at = datetime.utcnow()
            entries_updated += 1
        
        db.commit()
        
        # Get queue statistics
        stats = queue_manager.get_queue_stats()
        
        logger.info(
            f"Queue cleanup completed: {entries_updated} stale entries updated, "
            f"Queue stats - Total: {stats['total']}, Pending: {stats['pending']}, "
            f"Processing: {stats['processing']}, Completed: {stats['completed']}, "
            f"Failed: {stats['failed']}"
        )
        
        return {
            "status": "success",
            "message": "Queue cleanup completed",
            "entries_updated": entries_updated,
            "cutoff_time": cutoff_time.isoformat(),
            "queue_stats": stats
        }
        
    except Exception as exc:
        logger.error(f"Error during queue cleanup: {str(exc)}")
        # Handle error for non-critical task
        TaskErrorHandler.handle_task_failure(
            task_id=self.request.id,
            task_name=self.name,
            exception=exc,
            tb=traceback.format_exc(),
            retry_count=0,
        )
        return {
            "status": "error",
            "message": f"Queue cleanup failed: {str(exc)}"
        }
    finally:
        if db:
            db.close()


@celery_app.task(bind=True)
def sync_metadata(self):
    """Periodic metadata refresh
    
    Refreshes metadata for all media items in batches.
    Updates last_sync timestamp.
    Logs sync statistics.
    
    Returns:
        Dictionary with sync statistics
    """
    db: Optional[Session] = None
    try:
        logger.info("Starting periodic metadata sync task")
        
        db = SessionLocal()
        
        # Batch size to avoid overwhelming external APIs
        batch_size = 10
        
        # Sync movies
        movies = db.query(Movie).all()
        movies_synced = 0
        movies_failed = 0
        
        for i, movie in enumerate(movies):
            if i % batch_size == 0 and i > 0:
                # Small delay between batches to avoid rate limiting
                import time
                time.sleep(1)
            
            try:
                if movie.omdb_id:
                    omdb_data = asyncio.run(OMDBService.get_movie_details(db, movie.omdb_id))
                    if omdb_data:
                        parsed = OMDBService.parse_omdb_response(omdb_data)
                        if parsed:
                            movie.plot = parsed.get("plot", movie.plot)
                            movie.rating = parsed.get("rating", movie.rating)
                            movie.runtime = parsed.get("runtime", movie.runtime)
                            movie.genres = parsed.get("genres", movie.genres)
                            movie.updated_at = datetime.utcnow()
                            movies_synced += 1
            except Exception as e:
                logger.warning(f"Failed to sync movie {movie.id}: {str(e)}")
                movies_failed += 1
        
        # Sync TV shows
        tv_shows = db.query(TVShow).all()
        shows_synced = 0
        shows_failed = 0
        
        for i, show in enumerate(tv_shows):
            if i % batch_size == 0 and i > 0:
                # Small delay between batches
                import time
                time.sleep(1)
            
            try:
                if show.tvdb_id:
                    tvdb_data = asyncio.run(TVDBService.get_series_details(db, show.tvdb_id))
                    if tvdb_data:
                        parsed = TVDBService.parse_tvdb_series_response(tvdb_data)
                        if parsed:
                            show.plot = parsed.get("plot", show.plot)
                            show.rating = parsed.get("rating", show.rating)
                            show.genres = parsed.get("genres", show.genres)
                            show.status = parsed.get("status", show.status)
                            show.updated_at = datetime.utcnow()
                            shows_synced += 1
            except Exception as e:
                logger.warning(f"Failed to sync TV show {show.id}: {str(e)}")
                shows_failed += 1
        
        db.commit()
        
        total_synced = movies_synced + shows_synced
        total_failed = movies_failed + shows_failed
        
        logger.info(
            f"Metadata sync completed: {total_synced} items synced, {total_failed} failed. "
            f"Movies: {movies_synced} synced, {movies_failed} failed. "
            f"TV Shows: {shows_synced} synced, {shows_failed} failed."
        )
        
        return {
            "status": "success",
            "message": "Metadata sync completed",
            "movies_synced": movies_synced,
            "movies_failed": movies_failed,
            "shows_synced": shows_synced,
            "shows_failed": shows_failed,
            "total_synced": total_synced,
            "total_failed": total_failed,
            "sync_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Error during metadata sync: {str(exc)}")
        # Handle error for non-critical task
        TaskErrorHandler.handle_task_failure(
            task_id=self.request.id,
            task_name=self.name,
            exception=exc,
            tb=traceback.format_exc(),
            retry_count=0,
        )
        return {
            "status": "error",
            "message": f"Metadata sync failed: {str(exc)}"
        }
    finally:
        if db:
            db.close()


@celery_app.task(bind=True)
def bulk_metadata_sync_task(self, batch_id: int, media_ids: List[int], media_type: str):
    """Async task for bulk metadata refresh
    
    Args:
        batch_id: Batch operation ID
        media_ids: List of media IDs to sync
        media_type: Type of media ("movie" or "tv_show")
        
    Returns:
        Dictionary with sync results
    """
    db: Optional[Session] = None
    try:
        logger.info(f"Starting bulk metadata sync task for batch {batch_id}")
        
        db = SessionLocal()
        service = BatchOperationService(db)
        
        # Run async operation
        result = asyncio.run(service.bulk_metadata_sync(batch_id, media_ids, media_type))
        
        logger.info(f"Bulk metadata sync completed for batch {batch_id}: {result}")
        return result
        
    except Exception as exc:
        logger.error(f"Error in bulk metadata sync task for batch {batch_id}: {str(exc)}")
        if db:
            service = BatchOperationService(db)
            service.fail_batch_operation(batch_id, str(exc))
        
        TaskErrorHandler.handle_task_failure(
            task_id=self.request.id,
            task_name=self.name,
            exception=exc,
            tb=traceback.format_exc(),
            retry_count=0,
        )
        return {
            "status": "error",
            "batch_id": batch_id,
            "message": f"Bulk metadata sync failed: {str(exc)}"
        }
    finally:
        if db:
            db.close()


@celery_app.task(bind=True)
def bulk_file_import_task(self, batch_id: int, file_paths: List[str], media_type: str):
     """Async task for bulk file import
     
     Args:
         batch_id: Batch operation ID
         file_paths: List of file paths to import
         media_type: Type of media ("movie" or "tv_show")
         
     Returns:
         Dictionary with import results
     """
     db: Optional[Session] = None
     try:
         logger.info(f"Starting bulk file import task for batch {batch_id}")
         
         db = SessionLocal()
         service = BatchOperationService(db)
         
         # Run async operation
         result = asyncio.run(service.bulk_file_import(batch_id, file_paths, media_type))
         
         logger.info(f"Bulk file import completed for batch {batch_id}: {result}")
         return result
         
     except Exception as exc:
         logger.error(f"Error in bulk file import task for batch {batch_id}: {str(exc)}")
         if db:
             service = BatchOperationService(db)
             service.fail_batch_operation(batch_id, str(exc))
         
         TaskErrorHandler.handle_task_failure(
             task_id=self.request.id,
             task_name=self.name,
             exception=exc,
             tb=traceback.format_exc(),
             retry_count=0,
         )
         return {
             "status": "error",
             "batch_id": batch_id,
             "message": f"Bulk file import failed: {str(exc)}"
         }
     finally:
         if db:
             db.close()


@celery_app.task(bind=True)
def process_batch_item(self, batch_id: int, item_id: int, item_type: str, operation_type: str):
     """Worker task for processing individual batch items
     
     Args:
         batch_id: Batch operation ID
         item_id: ID of the item to process
         item_type: Type of item ("movie", "tv_show", "file")
         operation_type: Type of operation ("metadata_sync", "file_import")
         
     Returns:
         Dictionary with processing result
     """
     db: Optional[Session] = None
     try:
         logger.info(f"Processing batch item {item_id} for batch {batch_id}")
         
         db = SessionLocal()
         
         if operation_type == "metadata_sync":
             if item_type == "movie":
                 movie = db.query(Movie).filter(Movie.id == item_id).first()
                 if not movie:
                     return {"success": False, "error": "Movie not found"}
                 
                 if movie.omdb_id:
                     omdb_data = asyncio.run(OMDBService.get_movie_details(db, movie.omdb_id))
                     if omdb_data:
                         parsed = OMDBService.parse_omdb_response(omdb_data)
                         if parsed:
                             movie.plot = parsed.get("plot", movie.plot)
                             movie.rating = parsed.get("rating", movie.rating)
                             movie.runtime = parsed.get("runtime", movie.runtime)
                             movie.genres = parsed.get("genres", movie.genres)
                             movie.updated_at = datetime.utcnow()
                             db.commit()
                             return {"success": True}
             
             elif item_type == "tv_show":
                 show = db.query(TVShow).filter(TVShow.id == item_id).first()
                 if not show:
                     return {"success": False, "error": "TV show not found"}
                 
                 if show.tvdb_id:
                     tvdb_data = asyncio.run(TVDBService.get_series_details(db, show.tvdb_id))
                     if tvdb_data:
                         parsed = TVDBService.parse_tvdb_series_response(tvdb_data)
                         if parsed:
                             show.plot = parsed.get("plot", show.plot)
                             show.rating = parsed.get("rating", show.rating)
                             show.genres = parsed.get("genres", show.genres)
                             show.status = parsed.get("status", show.status)
                             show.updated_at = datetime.utcnow()
                             db.commit()
                             return {"success": True}
         
         return {"success": True}
         
     except Exception as exc:
         logger.error(f"Error processing batch item {item_id}: {str(exc)}")
         return {"success": False, "error": str(exc)}
     finally:
         if db:
             db.close()


@celery_app.task(bind=True)
def update_batch_progress(self, batch_id: int, completed_items: int, failed_items: int, error_message: Optional[str] = None):
     """Task for updating batch progress
     
     Args:
         batch_id: Batch operation ID
         completed_items: Number of completed items
         failed_items: Number of failed items
         error_message: Optional error message
         
     Returns:
         Dictionary with update result
     """
     db: Optional[Session] = None
     try:
         logger.info(f"Updating progress for batch {batch_id}: completed={completed_items}, failed={failed_items}")
         
         db = SessionLocal()
         service = BatchOperationService(db)
         
         batch_op = service.update_batch_progress(batch_id, completed_items, failed_items, error_message)
         
         if not batch_op:
             return {"success": False, "error": "Batch operation not found"}
         
         return {
             "success": True,
             "batch_id": batch_id,
             "progress_percentage": batch_op.progress_percentage,
             "eta": batch_op.eta.isoformat() if batch_op.eta else None
         }
         
     except Exception as exc:
         logger.error(f"Error updating batch progress for {batch_id}: {str(exc)}")
         return {"success": False, "error": str(exc)}
     finally:
         if db:
             db.close()
