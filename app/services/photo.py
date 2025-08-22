"""
Photo service for Memorial Website.
Handles photo upload, processing, and management for memorial pages.
"""

import logging
import os
import uuid
from typing import Optional, List, Tuple
from uuid import UUID
from datetime import datetime
from pathlib import Path
import shutil

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from PIL import Image

from app.models.photo import Photo
from app.models.memorial import Memorial
from app.schemas.photo import PhotoResponse, PhotoType, PhotoUploadResponse, PhotoDeleteResponse
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class PhotoValidationError(Exception):
    """Exception for photo validation errors."""
    pass


class PhotoProcessingError(Exception):
    """Exception for photo processing errors."""
    pass


class PhotoService:
    """Service for photo operations."""
    
    def __init__(self):
        """Initialize photo service."""
        self.settings = get_settings()
        self.upload_dir = Path(self.settings.PHOTOS_FOLDER)
        self.allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        
        # Ensure upload directory exists
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    async def get_photos_by_memorial(
        self, 
        db: AsyncSession, 
        memorial_id: UUID
    ) -> List[PhotoResponse]:
        """Get all photos for a memorial."""
        try:
            result = await db.execute(
                select(Photo)
                .where(and_(Photo.memorial_id == memorial_id, ~Photo.is_deleted))
                .order_by(Photo.display_order)
            )
            photos = result.scalars().all()
            return [PhotoResponse.model_validate(photo) for photo in photos]
        
        except Exception as e:
            logger.error(f"Failed to get photos for memorial {memorial_id}: {e}")
            return []
    
    async def get_photo_by_id(
        self, 
        db: AsyncSession, 
        photo_id: UUID
    ) -> Optional[PhotoResponse]:
        """Get a specific photo by ID."""
        try:
            result = await db.execute(
                select(Photo).where(and_(Photo.id == photo_id, ~Photo.is_deleted))
            )
            photo = result.scalar_one_or_none()
            return PhotoResponse.model_validate(photo) if photo else None
        
        except Exception as e:
            logger.error(f"Failed to get photo {photo_id}: {e}")
            return None

    def validate_upload_file(self, file: UploadFile, photo_type: PhotoType) -> None:
        """
        Validate uploaded file.
        
        Args:
            file: The uploaded file
            photo_type: Type of photo being uploaded
            
        Raises:
            PhotoValidationError: If validation fails
        """
        # Check file size
        if hasattr(file, 'size') and file.size and file.size > self.max_file_size:
            raise PhotoValidationError(f"File size {file.size} bytes exceeds maximum {self.max_file_size} bytes")
        
        # Check file extension
        if file.filename:
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in self.allowed_extensions:
                raise PhotoValidationError(f"File extension {file_ext} not allowed. Allowed: {self.allowed_extensions}")
        
        # Check content type
        if file.content_type and not file.content_type.startswith('image/'):
            raise PhotoValidationError(f"Invalid content type: {file.content_type}")

    async def check_photo_type_limit(self, db: AsyncSession, memorial_id: UUID, photo_type: PhotoType) -> None:
        """
        Check if photo type limit is exceeded.
        
        Args:
            db: Database session
            memorial_id: ID of the memorial
            photo_type: Type of photo
            
        Raises:
            PhotoValidationError: If limit is exceeded
        """
        # Get current count for this photo type
        result = await db.execute(
            select(func.count(Photo.id))
            .where(and_(
                Photo.memorial_id == memorial_id,
                Photo.photo_type == photo_type,
                ~Photo.is_deleted
            ))
        )
        current_count = result.scalar()
        
        # Check limits based on photo type
        if photo_type in [PhotoType.DECEASED, PhotoType.GRAVE] and current_count >= 1:
            raise PhotoValidationError(f"Maximum 1 {photo_type} photo allowed per memorial")
        elif photo_type.value.startswith('memorial') and current_count >= 1:
            raise PhotoValidationError(f"Maximum 1 {photo_type} photo allowed per memorial")

    def generate_unique_filename(self, original_filename: str, memorial_id: UUID) -> str:
        """
        Generate unique filename for uploaded photo.
        
        Args:
            original_filename: Original filename from upload
            memorial_id: ID of the memorial
            
        Returns:
            str: Unique filename
        """
        file_ext = Path(original_filename).suffix.lower()
        unique_id = str(uuid.uuid4())
        return f"{memorial_id}_{unique_id}{file_ext}"

    def get_memorial_upload_path(self, memorial_id: UUID) -> Path:
        """Get upload path for a specific memorial."""
        path = self.upload_dir / str(memorial_id)
        path.mkdir(parents=True, exist_ok=True)
        return path

    async def process_uploaded_image(self, file_path: Path) -> Tuple[int, int]:
        """
        Process uploaded image (resize if needed, get dimensions).
        
        Args:
            file_path: Path to the uploaded image
            
        Returns:
            Tuple of (width, height)
            
        Raises:
            PhotoProcessingError: If processing fails
        """
        try:
            with Image.open(file_path) as img:
                width, height = img.size
                
                # Resize if image is too large (max 1920x1080)
                max_width, max_height = 1920, 1080
                if width > max_width or height > max_height:
                    # Calculate new dimensions maintaining aspect ratio
                    ratio = min(max_width / width, max_height / height)
                    new_width = int(width * ratio)
                    new_height = int(height * ratio)
                    
                    # Resize image
                    resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    
                    # Save resized image
                    if img.mode in ('RGBA', 'LA', 'P'):
                        # Convert to RGB for JPEG compatibility
                        rgb_img = Image.new('RGB', resized_img.size, (255, 255, 255))
                        rgb_img.paste(resized_img, mask=resized_img.split()[-1] if img.mode == 'RGBA' else None)
                        rgb_img.save(file_path, 'JPEG', quality=85, optimize=True)
                    else:
                        resized_img.save(file_path, 'JPEG', quality=85, optimize=True)
                    
                    return new_width, new_height
                
                return width, height
                
        except Exception as e:
            logger.error(f"Failed to process image {file_path}: {e}")
            raise PhotoProcessingError(f"Image processing failed: {str(e)}")

    async def create_thumbnails(self, file_path: Path) -> None:
        """
        Create thumbnail versions of the image.
        
        Args:
            file_path: Path to the original image
        """
        try:
            with Image.open(file_path) as img:
                # Create thumbnail (400x400)
                thumbnail_path = file_path.parent / f"{file_path.stem}_thumb_400x400{file_path.suffix}"
                thumb_img = img.copy()
                thumb_img.thumbnail((400, 400), Image.Resampling.LANCZOS)
                thumb_img.save(thumbnail_path, quality=85, optimize=True)
                
                # Create medium size (800x600)
                medium_path = file_path.parent / f"{file_path.stem}_medium_800x600{file_path.suffix}"
                medium_img = img.copy()
                medium_img.thumbnail((800, 600), Image.Resampling.LANCZOS)
                medium_img.save(medium_path, quality=85, optimize=True)
                
        except Exception as e:
            logger.warning(f"Failed to create thumbnails for {file_path}: {e}")

    async def upload_photo(
        self,
        db: AsyncSession,
        memorial_id: UUID,
        photo_type: PhotoType,
        file: UploadFile,
        caption: Optional[str] = None,
        user_id: Optional[UUID] = None
    ) -> PhotoUploadResponse:
        """
        Upload and process a photo for a memorial.
        
        Args:
            db: Database session
            memorial_id: ID of the memorial
            photo_type: Type of photo
            file: Uploaded file
            caption: Optional photo caption
            user_id: ID of the user uploading
            
        Returns:
            PhotoUploadResponse: Upload result
        """
        try:
            # Validate file
            self.validate_upload_file(file, photo_type)
            
            # Check photo type limits
            await self.check_photo_type_limit(db, memorial_id, photo_type)
            
            # Generate unique filename and path
            filename = self.generate_unique_filename(file.filename, memorial_id)
            upload_path = self.get_memorial_upload_path(memorial_id)
            file_path = upload_path / filename
            
            # Save file
            try:
                with open(file_path, "wb") as buffer:
                    content = await file.read()
                    buffer.write(content)
            except Exception as e:
                raise PhotoProcessingError(f"Failed to save file: {str(e)}")
            
            # Process image and get dimensions
            try:
                width, height = await self.process_uploaded_image(file_path)
                await self.create_thumbnails(file_path)
                is_processed = True
                processing_error = None
            except PhotoProcessingError as e:
                logger.error(f"Image processing failed: {e}")
                width = height = None
                is_processed = False
                processing_error = str(e)
            
            # Determine display order based on photo type
            display_order_map = {
                PhotoType.DECEASED: 1,
                PhotoType.GRAVE: 2,
                PhotoType.MEMORIAL1: 3,
                PhotoType.MEMORIAL2: 4,
                PhotoType.MEMORIAL3: 5,
                PhotoType.MEMORIAL4: 6
            }
            
            # Create photo record
            photo = Photo(
                memorial_id=memorial_id,
                photo_type=photo_type.value,
                file_path=str(file_path.relative_to(self.upload_dir.parent)),
                original_filename=file.filename or filename,
                file_size=len(content) if content else None,
                mime_type=file.content_type,
                width=width,
                height=height,
                caption=caption,
                display_order=display_order_map.get(photo_type, 1),
                is_primary=(photo_type == PhotoType.DECEASED),  # Deceased photo is primary
                is_processed=is_processed,
                processing_error=processing_error,
                uploaded_by_user_id=user_id,
                uploaded_at=datetime.utcnow()
            )
            
            db.add(photo)
            await db.commit()
            await db.refresh(photo)
            
            # Convert to response
            photo_dict = photo.to_dict()
            photo_response = PhotoResponse(**photo_dict)
            
            logger.info(f"Photo uploaded successfully: {photo.id} for memorial {memorial_id}")
            
            return PhotoUploadResponse(
                success=True,
                message="Photo uploaded successfully",
                photo=photo_response
            )
            
        except PhotoValidationError as e:
            logger.warning(f"Photo validation failed: {e}")
            return PhotoUploadResponse(
                success=False,
                message=str(e)
            )
        except PhotoProcessingError as e:
            logger.error(f"Photo processing failed: {e}")
            return PhotoUploadResponse(
                success=False,
                message=f"Photo processing failed: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error during photo upload: {e}")
            await db.rollback()
            return PhotoUploadResponse(
                success=False,
                message="Photo upload failed due to server error"
            )

    async def delete_photo(
        self,
        db: AsyncSession,
        photo_id: UUID,
        user_id: UUID
    ) -> PhotoDeleteResponse:
        """
        Delete a photo.
        
        Args:
            db: Database session
            photo_id: ID of photo to delete
            user_id: ID of user requesting deletion
            
        Returns:
            PhotoDeleteResponse: Deletion result
        """
        try:
            # Get photo
            result = await db.execute(
                select(Photo).where(and_(Photo.id == photo_id, ~Photo.is_deleted))
            )
            photo = result.scalar_one_or_none()
            
            if not photo:
                return PhotoDeleteResponse(
                    success=False,
                    message="Photo not found",
                    photo_id=photo_id,
                    deleted_at=datetime.utcnow()
                )
            
            # Check permissions
            if not photo.can_be_deleted_by(user_id):
                return PhotoDeleteResponse(
                    success=False,
                    message="Permission denied",
                    photo_id=photo_id,
                    deleted_at=datetime.utcnow()
                )
            
            # Soft delete
            photo.soft_delete()
            await db.commit()
            
            # Clean up files (optional - could be done by background job)
            try:
                file_path = Path(photo.get_absolute_file_path())
                if file_path.exists():
                    file_path.unlink()
                
                # Delete thumbnails
                thumbnail_path = Path(photo.generate_thumbnail_path("400x400"))
                if thumbnail_path.exists():
                    thumbnail_path.unlink()
                    
            except Exception as e:
                logger.warning(f"Failed to delete photo files: {e}")
            
            logger.info(f"Photo deleted successfully: {photo_id}")
            
            return PhotoDeleteResponse(
                success=True,
                message="Photo deleted successfully",
                photo_id=photo_id,
                deleted_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Failed to delete photo {photo_id}: {e}")
            await db.rollback()
            return PhotoDeleteResponse(
                success=False,
                message="Failed to delete photo",
                photo_id=photo_id,
                deleted_at=datetime.utcnow()
            )


def get_photo_service() -> PhotoService:
    """Get photo service instance."""
    return PhotoService()