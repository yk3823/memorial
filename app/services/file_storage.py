"""
File storage service for Memorial Website.
Handles photo and video uploads with cloud-ready architecture.
"""

import os
import uuid
import logging
import mimetypes
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime

from fastapi import UploadFile, HTTPException
from PIL import Image
import aiofiles

from app.core.config import get_settings

logger = logging.getLogger(__name__)

class FileStorageService:
    """
    File storage service that works locally and in cloud with PVC.
    
    Directory structure:
    - storage/photos/{memorial_id}/{photo_id}.{ext}
    - storage/videos/{memorial_id}/{video_id}.{ext}
    - storage/temp/{upload_id}.{ext}
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.base_path = Path(self.settings.UPLOAD_FOLDER)
        self.photos_path = Path(self.settings.PHOTOS_FOLDER)
        self.videos_path = Path(self.settings.VIDEOS_FOLDER)
        self.temp_path = Path(self.settings.TEMP_FOLDER)
        
        # Create directories if they don't exist
        for path in [self.photos_path, self.videos_path, self.temp_path]:
            path.mkdir(parents=True, exist_ok=True)
    
    def _get_file_extension(self, filename: str) -> str:
        """Extract file extension from filename."""
        return Path(filename).suffix.lower().lstrip('.')
    
    def _is_valid_image(self, filename: str) -> bool:
        """Check if file is a valid image."""
        ext = self._get_file_extension(filename)
        allowed = [ext.strip('"') for ext in self.settings.ALLOWED_IMAGE_EXTENSIONS]
        return ext in allowed
    
    def _is_valid_video(self, filename: str) -> bool:
        """Check if file is a valid video."""
        ext = self._get_file_extension(filename)
        allowed = [ext.strip('"') for ext in self.settings.ALLOWED_VIDEO_EXTENSIONS]
        return ext in allowed
    
    async def validate_upload_file(self, file: UploadFile) -> Dict[str, Any]:
        """
        Validate uploaded file.
        
        Returns:
            Dict with validation results and file info
        """
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        # Check file size
        content = await file.read()
        await file.seek(0)  # Reset file pointer
        
        size_mb = len(content) / (1024 * 1024)
        if size_mb > self.settings.MAX_UPLOAD_SIZE_MB:
            raise HTTPException(
                status_code=400, 
                detail=f"File size {size_mb:.1f}MB exceeds limit of {self.settings.MAX_UPLOAD_SIZE_MB}MB"
            )
        
        # Determine file type
        is_image = self._is_valid_image(file.filename)
        is_video = self._is_valid_video(file.filename)
        
        if not is_image and not is_video:
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Only images and videos are allowed."
            )
        
        return {
            'filename': file.filename,
            'size': len(content),
            'size_mb': size_mb,
            'is_image': is_image,
            'is_video': is_video,
            'content_type': file.content_type,
            'extension': self._get_file_extension(file.filename)
        }
    
    async def save_photo(self, file: UploadFile, memorial_id: str) -> Dict[str, Any]:
        """
        Save a photo file for a memorial.
        
        Args:
            file: Uploaded photo file
            memorial_id: Memorial UUID as string
            
        Returns:
            Dict with saved file information
        """
        # Validate file
        file_info = await self.validate_upload_file(file)
        
        if not file_info['is_image']:
            raise HTTPException(status_code=400, detail="File is not a valid image")
        
        # Generate unique filename
        photo_id = str(uuid.uuid4())
        filename = f"{photo_id}.{file_info['extension']}"
        
        # Create memorial directory
        memorial_dir = self.photos_path / memorial_id
        memorial_dir.mkdir(parents=True, exist_ok=True)
        
        # Save file
        file_path = memorial_dir / filename
        
        try:
            async with aiofiles.open(file_path, 'wb') as f:
                await file.seek(0)
                content = await file.read()
                await f.write(content)
            
            # Create thumbnail if it's an image
            thumbnail_path = await self._create_thumbnail(file_path, memorial_dir)
            
            # Get file URL path (relative to storage root)
            relative_path = f"photos/{memorial_id}/{filename}"
            thumbnail_relative_path = f"photos/{memorial_id}/thumb_{filename}" if thumbnail_path else None
            
            logger.info(f"Photo saved: {file_path}")
            
            return {
                'photo_id': photo_id,
                'filename': filename,
                'original_filename': file_info['filename'],
                'file_path': str(file_path),
                'relative_path': relative_path,
                'thumbnail_path': thumbnail_relative_path,
                'size': file_info['size'],
                'content_type': file_info['content_type'],
                'created_at': datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Failed to save photo: {e}")
            # Clean up partial file
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(status_code=500, detail="Failed to save photo")
    
    async def save_video(self, file: UploadFile, memorial_id: str) -> Dict[str, Any]:
        """
        Save a video file for a memorial.
        
        Args:
            file: Uploaded video file
            memorial_id: Memorial UUID as string
            
        Returns:
            Dict with saved file information
        """
        # Validate file
        file_info = await self.validate_upload_file(file)
        
        if not file_info['is_video']:
            raise HTTPException(status_code=400, detail="File is not a valid video")
        
        # Generate unique filename
        video_id = str(uuid.uuid4())
        filename = f"{video_id}.{file_info['extension']}"
        
        # Create memorial directory
        memorial_dir = self.videos_path / memorial_id
        memorial_dir.mkdir(parents=True, exist_ok=True)
        
        # Save file
        file_path = memorial_dir / filename
        
        try:
            async with aiofiles.open(file_path, 'wb') as f:
                await file.seek(0)
                content = await file.read()
                await f.write(content)
            
            # Get file URL path (relative to storage root)
            relative_path = f"videos/{memorial_id}/{filename}"
            
            logger.info(f"Video saved: {file_path}")
            
            return {
                'video_id': video_id,
                'filename': filename,
                'original_filename': file_info['filename'],
                'file_path': str(file_path),
                'relative_path': relative_path,
                'size': file_info['size'],
                'content_type': file_info['content_type'],
                'created_at': datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Failed to save video: {e}")
            # Clean up partial file
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(status_code=500, detail="Failed to save video")
    
    async def _create_thumbnail(self, image_path: Path, output_dir: Path) -> Optional[Path]:
        """
        Create thumbnail for image.
        
        Args:
            image_path: Path to original image
            output_dir: Directory to save thumbnail
            
        Returns:
            Path to thumbnail or None if failed
        """
        try:
            thumbnail_path = output_dir / f"thumb_{image_path.name}"
            
            # Create thumbnail using PIL
            with Image.open(image_path) as img:
                # Convert RGBA to RGB if necessary
                if img.mode == 'RGBA':
                    img = img.convert('RGB')
                
                # Create thumbnail (maintain aspect ratio)
                img.thumbnail((300, 300), Image.Resampling.LANCZOS)
                img.save(thumbnail_path, 'JPEG', quality=85)
            
            logger.info(f"Thumbnail created: {thumbnail_path}")
            return thumbnail_path
            
        except Exception as e:
            logger.warning(f"Failed to create thumbnail for {image_path}: {e}")
            return None
    
    async def delete_photo(self, memorial_id: str, filename: str) -> bool:
        """Delete a photo file."""
        try:
            file_path = self.photos_path / memorial_id / filename
            thumbnail_path = self.photos_path / memorial_id / f"thumb_{filename}"
            
            if file_path.exists():
                file_path.unlink()
            
            if thumbnail_path.exists():
                thumbnail_path.unlink()
            
            logger.info(f"Photo deleted: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete photo {filename}: {e}")
            return False
    
    async def delete_video(self, memorial_id: str, filename: str) -> bool:
        """Delete a video file."""
        try:
            file_path = self.videos_path / memorial_id / filename
            
            if file_path.exists():
                file_path.unlink()
            
            logger.info(f"Video deleted: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete video {filename}: {e}")
            return False
    
    def get_photo_url(self, memorial_id: str, filename: str, thumbnail: bool = False) -> str:
        """Get URL for photo."""
        prefix = "thumb_" if thumbnail else ""
        return f"/api/v1/files/photos/{memorial_id}/{prefix}{filename}"
    
    def get_video_url(self, memorial_id: str, filename: str) -> str:
        """Get URL for video."""
        return f"/api/v1/files/videos/{memorial_id}/{filename}"


# Singleton instance
_file_storage_service = None

def get_file_storage_service() -> FileStorageService:
    """Get file storage service singleton."""
    global _file_storage_service
    if _file_storage_service is None:
        _file_storage_service = FileStorageService()
    return _file_storage_service